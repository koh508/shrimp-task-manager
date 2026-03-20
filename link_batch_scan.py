# link_batch_scan.py - 기존 파일 1회성 배치 링크 삽입 스캔
#
# 특징:
#   - 중단 후 재시작 가능 (link_batch_progress.json으로 진행 상황 저장)
#   - 5개 배치 단위 처리, 일일 한도 50개
#   - 루프 카운터 / 실패 카운터 2종 분리
#   - 50KB 이상 파일은 헤딩 기준 분할 + 무결성 검사
#   - API 1차(제안) → 2차(검증) 2회 호출
#   - 오류 로그: 자동화_로그/link_error_YYYY-MM-DD.json

import io
import json
import hashlib
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Windows 콘솔 UTF-8 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ── 스피너 ─────────────────────────────────────────────────────────────────

class Spinner:
    FRAMES = ["|", "/", "-", "\\"]

    def __init__(self):
        self._running = False
        self._thread  = None
        self._msg     = ""

    def start(self, msg: str = ""):
        self._msg     = msg
        self._running = True
        self._thread  = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self):
        i = 0
        while self._running:
            elapsed = int(time.time() - self._start)
            frame   = self.FRAMES[i % len(self.FRAMES)]
            print(f"\r  {frame} {self._msg} ({elapsed}s)", end="", flush=True)
            i += 1
            time.sleep(0.15)

    def stop(self, result: str = ""):
        self._running = False
        if self._thread:
            self._thread.join()
        print(f"\r  {result}" + " " * 40, flush=True)

    def __enter__(self):
        self._start = time.time()
        self.start(self._msg)
        return self

    def __exit__(self, *_):
        self.stop()


_spinner = Spinner()

from google import genai
from google.genai import types

# 내부 모듈
sys.path.insert(0, str(Path(__file__).parent))
from link_index import build_index, load_index, index_as_list, resolve_link
from link_safe_writer import (
    insert_links, update_yaml_flag,
    split_by_headings, verify_split_integrity, verify_write_integrity
)

# ── 설정 ───────────────────────────────────────────────────────────────────
VAULT_DIR     = Path(r"C:\Users\User\Documents\Obsidian Vault")
SYSTEM_DIR    = VAULT_DIR / "SYSTEM"
LOG_DIR       = VAULT_DIR / "자동화_로그"
PROGRESS_PATH = SYSTEM_DIR / "link_batch_progress.json"

BATCH_SIZE     = 5
DAILY_LIMIT    = 9999
CHUNK_MAX_CHAR = 8000
SPLIT_THRESHOLD_KB = 50

EXCLUDE_DIRS = {
    "SYSTEM", "Processed", ".obsidian", "__pycache__", ".trash", ".git",
    "Onew_Core_Backup_절대건드리지말것", "db_backup", "code_backup",
    "대화기록", "01_Daily",
}

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL  = "gemini-2.5-flash"

# ── 진행 상황 관리 ──────────────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        with PROGRESS_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {"done": [], "failed": {}, "loop_count": {}, "daily": {}}


def save_progress(prog: dict):
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)


# ── 해시 ───────────────────────────────────────────────────────────────────

def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ── 오류 로그 ──────────────────────────────────────────────────────────────

def write_error_log(file_path: str, error_type: str, detail: str, extra: dict = None):
    LOG_DIR.mkdir(exist_ok=True)
    today    = datetime.now().strftime("%Y-%m-%d")
    log_path = LOG_DIR / f"link_error_{today}.json"

    entry = {
        "timestamp":  datetime.now().isoformat(timespec="seconds"),
        "file":       file_path,
        "error_type": error_type,  # loop_error / api_error / parse_error / split_error / permission_error
        "detail":     detail,
        "action":     "stopped",
    }
    if extra:
        entry.update(extra)

    logs = []
    if log_path.exists():
        try:
            with log_path.open(encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass

    logs.append(entry)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"  [오류로그] {error_type}: {Path(file_path).name} → {detail}")


# ── 파일 수집 ──────────────────────────────────────────────────────────────

def collect_files(prog: dict) -> list[Path]:
    """처리 대상 파일 수집 (완료/오류/제외 파일 제외)."""
    done_set   = set(prog["done"])
    failed_set = set(prog["failed"].keys())
    targets    = []

    for md_file in sorted(VAULT_DIR.rglob("*.md")):
        rel = md_file.relative_to(VAULT_DIR)

        # 제외 폴더
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue

        rel_str = str(rel).replace("\\", "/")

        # 이미 완료
        if rel_str in done_set:
            continue

        # 실패 횟수 3회 이상
        fail_count = prog["failed"].get(rel_str, 0)
        if fail_count >= 3:
            continue

        # 루프 횟수 3회 이상
        loop_count = prog["loop_count"].get(rel_str, 0)
        if loop_count >= 3:
            continue

        # 최소 길이 필터 (파일 크기로 대체 — 디스크 전체 읽기 없음)
        try:
            if md_file.stat().st_size < 100:
                continue
        except Exception:
            continue

        # Excalidraw / 링크처리 확인 (앞 500바이트만 읽기)
        try:
            header = md_file.read_bytes()[:500].decode("utf-8", errors="replace")
        except Exception:
            continue

        if "excalidraw-plugin" in header:
            continue

        if re.search(r'^링크처리:\s*true', header, re.MULTILINE):
            continue

        targets.append(md_file)

    return targets


# ── API 1차 호출 ────────────────────────────────────────────────────────────

def api_first_pass(batch_contents: list[dict], note_index_list: list[str]) -> list | None:
    """
    batch_contents: [{"file_id": 0, "path": "...", "content": "..."}, ...]
    note_index_list: Vault 전체 파일 경로 목록
    """
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "results": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_id": types.Schema(type=types.Type.INTEGER),
                        "link_candidates": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "keyword":     types.Schema(type=types.Type.STRING),
                                    "target_note": types.Schema(type=types.Type.STRING),
                                    "context":     types.Schema(type=types.Type.STRING),
                                    "confidence":  types.Schema(type=types.Type.NUMBER),
                                    "line_hint":   types.Schema(type=types.Type.STRING),
                                },
                                required=["keyword", "target_note", "context", "confidence"]
                            )
                        ),
                        "suggested_tags":  types.Schema(type=types.Type.ARRAY,
                                                        items=types.Schema(type=types.Type.STRING)),
                        "summary_1line":   types.Schema(type=types.Type.STRING),
                    },
                    required=["file_id", "link_candidates"]
                )
            )
        },
        required=["results"]
    )

    note_list_str = "\n".join(note_index_list[:300])  # 너무 길면 토큰 낭비
    batch_str = json.dumps(
        [{"file_id": b["file_id"], "path": b["path"],
          "content": b["content"][:CHUNK_MAX_CHAR]} for b in batch_contents],
        ensure_ascii=False
    )

    prompt = f"""다음은 Obsidian 노트 배열이다. 각 노트에 대해 링크 후보를 분석하라.

[실존 노트 인덱스 - 이 목록에 있는 것만 링크 대상으로 제안]
{note_list_str}

[분석 규칙]
1. 링크 후보는 반드시 위 인덱스에 있는 노트 경로로만 제안
2. 파일당 최대 5개 링크 후보
3. 이미 [[링크]] 형태로 있는 것은 제안 금지
4. 코드블록, YAML, 수식($...$) 안의 텍스트는 제안 금지
5. 확신도(confidence) 0.8 미만이면 제안 금지
6. 한 단어가 아닌 구체적 맥락에서만 제안

[노트 배열]
{batch_str}"""

    try:
        _spinner._msg = "API 1차 호출 중"
        with _spinner:
            res = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
        return json.loads(res.text).get("results", [])
    except Exception as e:
        return None


# ── API 2차 호출 ────────────────────────────────────────────────────────────

def api_second_pass(first_results: list) -> list | None:
    """
    1차 결과를 받아 엄격하게 검증. 원문 재전달 없음 → 토큰 절약.
    """
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "results": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_id": types.Schema(type=types.Type.INTEGER),
                        "approved_links": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "keyword":     types.Schema(type=types.Type.STRING),
                                    "target_note": types.Schema(type=types.Type.STRING),
                                    "line_hint":   types.Schema(type=types.Type.STRING),
                                    "insert_as":   types.Schema(type=types.Type.STRING),
                                },
                                required=["keyword", "target_note", "insert_as"]
                            )
                        ),
                        "final_tags":      types.Schema(type=types.Type.ARRAY,
                                                        items=types.Schema(type=types.Type.STRING)),
                        "rejected_count":  types.Schema(type=types.Type.INTEGER),
                    },
                    required=["file_id", "approved_links"]
                )
            )
        },
        required=["results"]
    )

    # 원문 제외하고 후보 + 컨텍스트만 전달
    candidates_only = [
        {"file_id": r["file_id"], "link_candidates": r.get("link_candidates", [])}
        for r in first_results
    ]

    prompt = f"""너는 엄격한 지식 편집장이다.
아래 링크 후보들을 검토하여 진짜 가치 있는 것만 승인하라.

[기각 기준]
1. 키워드가 일치해도 맥락이 다른 경우 (예: 냉매 → 일상 메모에서 언급)
2. 있어도 그만, 없어도 그만인 경우
3. 같은 파일 내 자기 참조에 가까운 경우
4. 동사/형용사처럼 링크로 만들면 어색한 단어

[승인된 링크의 insert_as 형식]
- 기본: [[파일명 확장자 없음]]
- 표시명이 키워드와 다를 때: [[파일명|키워드]]

[후보 목록]
{json.dumps(candidates_only, ensure_ascii=False)}"""

    try:
        _spinner._msg = "API 2차 검증 중"
        with _spinner:
            res = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
        return json.loads(res.text).get("results", [])
    except Exception as e:
        return None


# ── 파일 1개 처리 ──────────────────────────────────────────────────────────

def process_single_file(
    md_file: Path,
    second_result: dict,
    prog: dict
) -> bool:
    """API 2차 결과를 받아 실제 파일에 링크 삽입. 성공 시 True 반환."""
    rel_str = str(md_file.relative_to(VAULT_DIR)).replace("\\", "/")

    approved = second_result.get("approved_links", [])
    if not approved:
        # 승인된 링크 없어도 처리완료 표시
        prog["done"].append(rel_str)
        return True

    try:
        original = md_file.read_text(encoding="utf-8", errors="replace")
        original_hash = md5(original)
    except PermissionError:
        write_error_log(rel_str, "permission_error", "읽기 접근 거부")
        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
        return False

    # 50KB 이상 분할 처리
    file_size = md_file.stat().st_size
    try:
        if file_size > SPLIT_THRESHOLD_KB * 1024:
            chunks = split_by_headings(original, CHUNK_MAX_CHAR)
            ok, msg = verify_split_integrity(original, chunks)
            if not ok:
                write_error_log(rel_str, "split_error", msg)
                prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
                return False

            # 청크 간 중복 링크 방지
            used_keywords: set[str] = set()
            modified_chunks = []
            total_inserted  = 0

            for chunk in chunks:
                filtered = [lk for lk in approved if lk["keyword"] not in used_keywords]
                modified_chunk, n = insert_links(chunk, filtered)
                for lk in approved:
                    if lk["keyword"] not in used_keywords:
                        if "[[" in modified_chunk and lk["keyword"] in modified_chunk:
                            used_keywords.add(lk["keyword"])
                modified_chunks.append(modified_chunk)
                total_inserted += n

            modified = "".join(modified_chunks)
            inserted = total_inserted
        else:
            modified, inserted = insert_links(original, approved)
    except ValueError as e:
        write_error_log(rel_str, "parse_error", str(e))
        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
        return False

    if inserted == 0:
        prog["done"].append(rel_str)
        return True

    # 링크처리: true 플래그 추가
    modified = update_yaml_flag(modified, "링크처리", "true")

    # 루프 감지: 수정 전후 해시가 같으면 실제 삽입 안 된 것
    if md5(modified) == original_hash:
        prog["done"].append(rel_str)
        return True

    # 루프 카운터 증가 (watchdog 없이 배치 처리이므로 일반적으로 0)
    prog["loop_count"][rel_str] = prog["loop_count"].get(rel_str, 0) + 1
    if prog["loop_count"][rel_str] >= 3:
        write_error_log(rel_str, "loop_error", "3회 이상 동일 파일 처리 시도")
        return False

    try:
        md_file.write_text(modified, encoding="utf-8")
    except PermissionError:
        write_error_log(rel_str, "permission_error", "쓰기 접근 거부")
        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
        return False
    except Exception as e:
        write_error_log(rel_str, "parse_error", str(e))
        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
        return False

    # 무결성 검사 3: 저장 후 읽기 확인
    ok, msg = verify_write_integrity(md_file, modified)
    if not ok:
        write_error_log(rel_str, "write_integrity_error", msg)
        # 원본 복구 시도
        try:
            md_file.write_text(original, encoding="utf-8")
            print(f"  [복구] 원본 복구 완료: {rel_str}")
        except Exception:
            pass
        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
        return False

    print(f"  [{inserted}개 링크] {rel_str}")

    prog["done"].append(rel_str)
    return True


# ── 메인 ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  온유 링크 배치 스캔 시작")
    print(f"  시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 인덱스 갱신
    print("\n[1] 노트 인덱스 빌드 중...")
    index = build_index()
    note_list = index_as_list(index)
    print(f"  → {len(note_list)}개 노트 인덱싱 완료")

    # 진행 상황 로드
    prog = load_progress()
    today = datetime.now().strftime("%Y-%m-%d")
    daily_done = prog["daily"].get(today, 0)

    # 처리 대상 수집
    print("\n[2] 처리 대상 파일 수집 중...")
    targets = collect_files(prog)
    print(f"  → {len(targets)}개 파일 (완료: {len(prog['done'])}개, 실패제외: {len(prog['failed'])}개)")

    if not targets:
        print("\n처리할 파일 없음. 완료.")
        return

    # 일일 한도 잔여량
    remaining = DAILY_LIMIT - daily_done
    if remaining <= 0:
        print(f"\n일일 한도({DAILY_LIMIT}개) 도달. 내일 다시 실행하세요.")
        return

    targets = targets[:remaining]
    print(f"  → 오늘 처리 가능: {remaining}개 (이미 {daily_done}개 처리됨)")

    # 배치 처리
    print(f"\n[3] 배치 처리 시작 (배치 크기: {BATCH_SIZE}개)")
    total_inserted_files = 0
    total_links = 0

    for batch_start in range(0, len(targets), BATCH_SIZE):
        batch = targets[batch_start: batch_start + BATCH_SIZE]
        print(f"\n  배치 {batch_start // BATCH_SIZE + 1} | 파일 {batch_start + 1}~{batch_start + len(batch)}")

        # 배치 내용 준비
        batch_contents = []
        batch_originals = {}

        for i, md_file in enumerate(batch):
            rel_str = str(md_file.relative_to(VAULT_DIR)).replace("\\", "/")
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                # 50KB 이상은 첫 청크만 API에 전달 (분할 처리는 수정 단계에서)
                if md_file.stat().st_size > SPLIT_THRESHOLD_KB * 1024:
                    chunks = split_by_headings(content, CHUNK_MAX_CHAR)
                    ok, msg = verify_split_integrity(content, chunks)
                    if not ok:
                        write_error_log(rel_str, "split_error", msg)
                        prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
                        continue
                    api_content = chunks[0]
                else:
                    api_content = content

                batch_contents.append({"file_id": i, "path": rel_str, "content": api_content})
                batch_originals[i] = md_file
            except Exception as e:
                write_error_log(rel_str, "parse_error", str(e))

        if not batch_contents:
            continue

        # API 1차 호출
        first_results = api_first_pass(batch_contents, note_list)
        if first_results is None:
            print("  [오류] 1차 API 호출 실패 → 이 배치 건너뜀")
            for bc in batch_contents:
                rel_str = bc["path"]
                prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
            save_progress(prog)
            time.sleep(2)
            continue

        has_candidates = [r for r in first_results if r.get("link_candidates")]
        if not has_candidates:
            print("  1차 결과: 링크 후보 없음 → 2차 호출 생략")
            for bc in batch_contents:
                prog["done"].append(bc["path"])
            save_progress(prog)
            continue

        # API 2차 호출
        second_results = api_second_pass(first_results)
        if second_results is None:
            print("  [오류] 2차 API 호출 실패 → 이 배치 건너뜀")
            for bc in batch_contents:
                rel_str = bc["path"]
                prog["failed"][rel_str] = prog["failed"].get(rel_str, 0) + 1
            save_progress(prog)
            time.sleep(2)
            continue

        # 파일별 링크 삽입
        result_map = {r["file_id"]: r for r in second_results}

        for bc in batch_contents:
            fid     = bc["file_id"]
            md_file = batch_originals.get(fid)
            if md_file is None:
                continue
            result = result_map.get(fid, {"file_id": fid, "approved_links": []})
            success = process_single_file(md_file, result, prog)
            if success:
                total_inserted_files += 1
                total_links += len(result.get("approved_links", []))
                daily_done += 1
                prog["daily"][today] = daily_done

        save_progress(prog)
        time.sleep(1)  # API rate limit 여유

        if daily_done >= DAILY_LIMIT:
            print(f"\n일일 한도 {DAILY_LIMIT}개 도달. 중단합니다.")
            break

    print(f"\n{'=' * 60}")
    print(f"  배치 스캔 완료")
    print(f"  처리 파일: {total_inserted_files}개")
    print(f"  삽입 링크: {total_links}개 (추정)")
    print(f"  오류 로그: {LOG_DIR}/link_error_{today}.json")
    print(f"  진행 상황: {PROGRESS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
