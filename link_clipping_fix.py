# link_clipping_fix.py - 클리핑 파일 YAML 형식 소급 수정
#
# 추가 필드: 출처(없을 경우 빈 문자열), 링크처리: false, 상태: 대기
# 수정 완료 후 온유 실행 시 mtime 기반으로 자동 재임베딩됨 (별도 트리거 불필요)

import re
import json
from pathlib import Path
from datetime import datetime

VAULT_DIR      = Path(r"C:\Users\User\Documents\Obsidian Vault")
CLIPPING_DIR   = VAULT_DIR / "클리핑"
LOG_DIR        = VAULT_DIR / "자동화_로그"
REPORT_PATH    = LOG_DIR / f"clipping_fix_{datetime.now().strftime('%Y-%m-%d')}.json"


def parse_yaml(content: str) -> tuple[dict, str, str] | None:
    """
    YAML frontmatter 파싱. 리스트형(  - 항목) 값도 올바르게 처리.
    반환: (yaml_dict, yaml_raw, rest_body) 또는 None (YAML 없는 경우)
    """
    m = re.match(r'^---\s*\n([\s\S]*?)\n---\s*\n', content)
    if not m:
        return None

    yaml_raw  = m.group(1)
    rest_body = content[m.end():]
    yaml_dict = {}
    current_key = None

    for line in yaml_raw.splitlines():
        # 리스트 항목 (  - 값)
        list_item = re.match(r'^[ \t]+-[ \t]+(.*)', line)
        if list_item and current_key:
            if not isinstance(yaml_dict.get(current_key), list):
                yaml_dict[current_key] = []
            yaml_dict[current_key].append(list_item.group(1).strip())
            continue

        # key: value 행
        kv = re.match(r'^(\S[^:]*?)\s*:\s*(.*)', line)
        if kv:
            current_key = kv.group(1).strip()
            val = kv.group(2).strip().strip('"\'')
            # 값이 없으면 None (리스트 항목이 이어올 수 있음)
            yaml_dict[current_key] = val if val else None

    return yaml_dict, yaml_raw, rest_body


def rebuild_yaml(yaml_dict: dict, key_order: list[str]) -> str:
    """순서 보존하여 YAML 재조립."""
    lines = []
    written = set()

    # 지정 순서대로 먼저
    for key in key_order:
        if key in yaml_dict:
            val = yaml_dict[key]
            # 리스트 값 처리 (tags 등)
            if isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {val}")
            written.add(key)

    # 나머지 필드 (순서 미지정)
    for key, val in yaml_dict.items():
        if key not in written:
            if isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {val}")

    return "\n".join(lines)


def fix_clipping_file(md_file: Path) -> dict:
    """
    단일 클리핑 파일 수정.
    반환: {"file": str, "status": "fixed"/"skipped"/"error", "detail": str}
    """
    rel_str = str(md_file.relative_to(VAULT_DIR)).replace("\\", "/")

    try:
        content = md_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"file": rel_str, "status": "error", "detail": str(e)}

    parsed = parse_yaml(content)

    if parsed is None:
        # YAML 없는 파일 → 최소 YAML 추가
        today = datetime.now().strftime("%Y-%m-%d")
        new_yaml = (
            f"---\ntags:\n  - 클리핑\n날짜: {today}\n"
            f"주제: \n출처: \n링크처리: false\n상태: 대기\n---\n\n"
        )
        modified = new_yaml + content
        md_file.write_text(modified, encoding="utf-8")
        return {"file": rel_str, "status": "fixed", "detail": "YAML 신규 추가"}

    yaml_dict, yaml_raw, rest_body = parsed

    changed = False

    # 출처 필드 추가 (없을 경우)
    if "출처" not in yaml_dict:
        # source 필드가 있으면 출처로 복사
        yaml_dict["출처"] = yaml_dict.get("source", "")
        changed = True

    # 링크처리 필드 추가
    if "링크처리" not in yaml_dict:
        yaml_dict["링크처리"] = "false"
        changed = True

    # 상태 필드 추가
    if "상태" not in yaml_dict:
        yaml_dict["상태"] = "대기"
        changed = True

    # tags가 문자열이면 리스트로 변환 (간단 처리)
    if "tags" in yaml_dict and isinstance(yaml_dict["tags"], str):
        raw_tags = yaml_dict["tags"].strip("[]").split(",")
        yaml_dict["tags"] = [t.strip() for t in raw_tags if t.strip()]
        changed = True

    if not changed:
        return {"file": rel_str, "status": "skipped", "detail": "이미 최신 형식"}

    # YAML 재조립 (필드 순서 통일)
    key_order = ["tags", "날짜", "주제", "출처", "링크처리", "상태"]
    new_yaml_body = rebuild_yaml(yaml_dict, key_order)
    modified = f"---\n{new_yaml_body}\n---\n\n{rest_body.lstrip()}"

    try:
        md_file.write_text(modified, encoding="utf-8")
        return {"file": rel_str, "status": "fixed", "detail": "출처/링크처리/상태 필드 추가"}
    except PermissionError:
        return {"file": rel_str, "status": "error", "detail": "쓰기 접근 거부"}


def main():
    print("=" * 55)
    print("  클리핑 파일 YAML 형식 소급 수정")
    print(f"  시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  대상: {CLIPPING_DIR}")
    print("=" * 55)

    if not CLIPPING_DIR.exists():
        print(f"[오류] 클리핑 폴더 없음: {CLIPPING_DIR}")
        return

    files = sorted(CLIPPING_DIR.glob("*.md"))
    print(f"\n대상 파일 {len(files)}개\n")

    results = []
    fixed   = 0
    skipped = 0
    errors  = 0

    for md_file in files:
        result = fix_clipping_file(md_file)
        results.append(result)

        status = result["status"]
        if status == "fixed":
            fixed += 1
            print(f"  [수정] {md_file.name}")
        elif status == "skipped":
            skipped += 1
        else:
            errors += 1
            print(f"  [오류] {md_file.name} → {result['detail']}")

    # 결과 리포트 저장
    LOG_DIR.mkdir(exist_ok=True)
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total":   len(files),
        "fixed":   fixed,
        "skipped": skipped,
        "errors":  errors,
        "note":    "수정된 파일은 온유 다음 실행 시 mtime 기반으로 자동 재임베딩됩니다.",
        "details": results,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 55}")
    print(f"  완료: 수정 {fixed}개 / 건너뜀 {skipped}개 / 오류 {errors}개")
    print(f"  리포트: {REPORT_PATH}")
    print(f"  재임베딩: 온유 다음 실행 시 자동 처리됩니다.")
    print("=" * 55)


if __name__ == "__main__":
    main()
