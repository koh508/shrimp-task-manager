import os
import glob
import json
import re
import math
import time
import sys
import shutil
import threading
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from google import genai
from google.genai import types

# ==============================================================================
# [설정 영역]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
DB_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_pure_db.json")
SYSTEM_PROMPT_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_시스템_초기화_프로토콜.md")
USAGE_LOG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "api_usage_log.json")

# ==============================================================================
# [테두리 설정 - 여기만 수정하면 됩니다]
# ==============================================================================

# ── 학습 테두리 ──────────────────────────────────────────────────────────────
# 이 이름이 경로에 포함된 폴더는 임베딩 학습에서 제외
SYNC_EXCLUDE_DIRS  = ["대화기록", "venv", ".obsidian", ".git",
                       "code_backup", "db_backup", "__pycache__", "Onew_Core_Backup"]

# 이 이름이 포함된 파일은 학습 제외
SYNC_EXCLUDE_FILES = ["onew_pure_db", "api_usage_log"]

MAX_FILE_SIZE_KB   = 200        # 이 크기(KB) 초과 파일은 학습 스킵
MAX_CHUNKS_PER_FILE = 150       # 파일 당 청크 최대 수 (초과 시 스킵)
MAX_DAILY_EMBED_CALLS = 150000  # 하루 임베딩 API 호출 한도
AUTO_SYNC_HOURS    = 12         # 자동 학습 주기 (시간 단위)
CHUNK_VERSION      = "v2"       # 청크 전략 버전 (바뀌면 전체 재학습)

# ── 웹 검색 테두리 ───────────────────────────────────────────────────────────
MAX_DAILY_SEARCHES = 30         # 하루 웹 검색 최대 횟수
EXAM_DATE          = datetime(2026, 4, 26)  # 공조냉동 실기 시험일
# 허용 주제 키워드 (비어있으면 무제한)
SEARCH_ALLOW_TOPICS = []  # 비어있으면 무제한 (일일 30회 한도만 적용)

# ── 자동 클리핑 설정 ──────────────────────────────────────────────────────────
CLIP_CONFIG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "clip_config.json")
CLIP_INDEX_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "클리핑_인덱스.json")
CLIP_FOLDER      = os.path.join(OBSIDIAN_VAULT_PATH, "클리핑")
MAX_CLIP_FILE_KB = 200   # 클리핑 파일 최대 크기
CLIP_DEDUP_DAYS  = 7     # 동일 주제 재클리핑 방지 기간 (일)
CLIP_DEFAULTS = {
    "topics": [
        "AI 최신 뉴스", "LLM 기술 동향", "Python 팁",
        "오픈소스 AI 도구", "머신러닝 트렌드", "개발자 생산성 도구",
        "ChatGPT 활용법", "딥러닝 연구 동향", "코딩 기법", "AI 윤리 이슈"
    ],
    "delay_seconds": 30,
    "max_clips": 10,
    "enabled": True
}

# Gemini API 키 (환경변수에서 로드)
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ 오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("💡 PowerShell에서 다음 명령어를 실행하세요:")
    print('   [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key", "User")')
    sys.exit(1)
client = genai.Client(api_key=API_KEY)

# ==============================================================================
# [위치 감지 모듈 - 집/회사 모드]
# ==============================================================================
LOCATION_CONFIG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_location.json")

# 회사 모드에서 차단할 민감 주제 키워드
SENSITIVE_KEYWORDS = [
    "양악", "수술", "산재", "요양", "우울", "힘들어", "외로워", "불안",
    "상처", "아파", "속상", "고민", "스트레스", "감정", "마음이", "외롭",
    "죽고", "포기", "무기력", "치료", "병원", "정신", "심리",
]

def _get_public_ip() -> str:
    """현재 공인 IP를 반환. 실패 시 빈 문자열."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except:
        return ""

_wifi_security_cache: dict = {}  # {"result": str, "time": float}

def _get_wifi_security() -> str:
    """현재 연결된 WiFi 보안 방식을 반환. 'open'(비밀번호없음), 'secured'(비밀번호있음), 'unknown' 중 하나.
    PowerShell + UTF-8 강제 출력으로 한글 Windows 인코딩 문제 우회.
    결과를 60초간 캐시하여 중복 호출 방지.
    """
    if _wifi_security_cache and time.time() - _wifi_security_cache.get("time", 0) < 60:
        return _wifi_security_cache["result"]
    try:
        _PS = ["powershell", "-NoProfile", "-Command"]

        # 1. 현재 연결된 SSID 가져오기
        r1 = subprocess.run(
            _PS + ["[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; netsh wlan show interfaces"],
            capture_output=True, timeout=7
        )
        output1 = r1.stdout.decode("utf-8", errors="ignore")
        ssid = ""
        for line in output1.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[-1].strip()
                break
        if not ssid:
            _wifi_security_cache.update({"result": "unknown", "time": time.time()})
            return "unknown"

        # 2. 해당 프로필의 인증 방식 확인 (영문 출력 강제)
        r2 = subprocess.run(
            _PS + [f"[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; netsh wlan show profiles name='{ssid}' key=clear"],
            capture_output=True, timeout=7
        )
        output2 = r2.stdout.decode("utf-8", errors="ignore")
        result = "unknown"
        for line in output2.splitlines():
            if "Authentication" in line:
                auth = line.split(":", 1)[-1].strip().lower()
                result = "open" if auth in ("open", "none") else "secured"
                break
        _wifi_security_cache.update({"result": result, "time": time.time()})
        return result
    except:
        _wifi_security_cache.update({"result": "unknown", "time": time.time()})
        return "unknown"

def detect_location_mode() -> str:
    """WiFi 보안 방식 기반으로 시크릿 모드 결정.
    - 개방형 WiFi(비밀번호 없음) → 'work' (시크릿 ON)
    - 보안 WiFi(비밀번호 있음)  → 'home' (시크릿 OFF)
    - 수동 오버라이드 설정 있으면 그걸 우선 적용.
    """
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass

    # 수동 오버라이드 우선 적용
    if config.get("manual_override") is not None:
        return "work" if config["manual_override"] else "home"

    # WiFi 보안 방식 자동 감지
    wifi_sec = _get_wifi_security()
    if wifi_sec == "open":
        return "work"   # 개방형 → 시크릿 ON
    elif wifi_sec == "secured":
        return "home"   # 보안됨 → 시크릿 OFF

    # 폴백: 공인 IP 기반 (onew_location.json의 work_ips 목록)
    work_ips = config.get("work_ips", [])
    if work_ips:
        current_ip = _get_public_ip()
        if current_ip and current_ip in work_ips:
            return "work"
    return "home"

# ==============================================================================
# [1. 스마트 기억 모듈 (마크다운 전용 순정 코어)]
# ==============================================================================
def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    return dot_product / (mag1 * mag2) if mag1 * mag2 != 0 else 0.0

def _semantic_chunks(content: str, max_chunk: int = 800) -> list[str]:
    """마크다운 헤더(#) 단위로 의미 있게 분할. 섹션이 너무 길면 재분할."""
    # YAML 프론트매터 제거
    body = re.sub(r'^---[\s\S]*?---\n?', '', content.strip())

    # 헤더 기준 분할 (# ## ### 모두)
    sections = re.split(r'(?=\n#{1,3} )', body)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_chunk:
            chunks.append(sec)
        else:
            # 긴 섹션은 문단(빈 줄) 단위로 재분할
            paras = [p.strip() for p in re.split(r'\n{2,}', sec) if p.strip()]
            buf = ""
            for p in paras:
                if len(buf) + len(p) + 1 <= max_chunk:
                    buf = (buf + "\n\n" + p).strip()
                else:
                    if buf:
                        chunks.append(buf)
                    # 문단 자체가 max_chunk 초과면 고정 크기로 자름
                    if len(p) > max_chunk:
                        for i in range(0, len(p), max_chunk):
                            chunks.append(p[i:i+max_chunk])
                    else:
                        buf = p
            if buf:
                chunks.append(buf)

    # 빈 청크 제거
    return [c for c in chunks if len(c.strip()) > 20]


def _compress_content(content: str, filename: str) -> str:
    """대용량 파일을 섹션별로 나눠 Gemini로 압축 요약한다."""
    try:
        # 3000자 단위로 섹션 분할 후 각각 요약
        sections = [content[i:i+3000] for i in range(0, len(content), 3000)]
        summaries = []
        for i, sec in enumerate(sections[:10]):  # 최대 10섹션
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    f"다음 마크다운 내용을 핵심만 남겨 500자 이내로 압축하라. "
                    f"파일명: {filename}\n\n{sec}"
                ),
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            summaries.append(res.text.strip())
            time.sleep(0.3)
        return f"[압축 요약 - {filename}]\n\n" + "\n\n".join(summaries)
    except Exception as e:
        return ""

def _score_importance(content: str, filename: str) -> str:
    """노트 중요도를 HIGH / MEDIUM / LOW 로 자동 판별."""
    score = 0
    # 시험/공부 관련 키워드
    study_kw = ["공조냉동", "냉매", "압축기", "응축기", "증발기", "성적계수", "COP",
                "소방", "방재", "OCU", "시험", "오답", "공식", "계산"]
    # 일정/중요 이벤트 키워드
    event_kw = ["산재", "양악", "병원", "면담", "복직", "마감", "제출", "D-"]
    # 일기 (날짜 파일명)
    import re as _re
    if _re.match(r'\d{4}-\d{2}-\d{2}', filename):
        score += 1
    for kw in study_kw:
        if kw in content:
            score += 1
    for kw in event_kw:
        if kw in content:
            score += 2
    # 링크/태그 많을수록 중요
    link_count = len(_re.findall(r'\[\[.*?\]\]', content))
    score += min(link_count // 3, 3)

    if score >= 5:   return "HIGH"
    elif score >= 2: return "MEDIUM"
    else:            return "LOW"


class OnewPureMemory:
    def __init__(self):
        self.db = {}
        self._db_mtime = 0
        self._load_db()

    def _load_db(self):
        if os.path.exists(DB_FILE):
            try:
                mtime = os.path.getmtime(DB_FILE)
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
                self._db_mtime = mtime
            except: pass

    def _reload_if_updated(self):
        """watcher 등 외부에서 DB가 변경됐으면 자동으로 다시 로드."""
        try:
            mtime = os.path.getmtime(DB_FILE)
            if mtime > self._db_mtime:
                self._load_db()
        except: pass

    def _save_db(self):
        try:
            if os.path.exists(DB_FILE):
                backup_dir = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "db_backup")
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                import shutil
                shutil.copy2(DB_FILE, os.path.join(backup_dir, f"onew_pure_db_{timestamp}.json"))
                backups = sorted(glob.glob(os.path.join(backup_dir, "*.json")))
                for old in backups[:-3]:
                    os.remove(old)

            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ DB 저장 오류: {e}")

    def sync(self, silent=False):
        if not silent:
            print("🧠 온유(MD 전용 안전 모드)가 지식 네트워크를 스캔 중입니다...")

        # 청크 버전 체크 — 버전 다르면 전체 재학습
        stored_version = self.db.get("__meta__", {}).get("chunk_version")
        if stored_version != CHUNK_VERSION:
            if not silent:
                print(f"🔄 청크 전략 변경 감지 ({stored_version} → {CHUNK_VERSION}). 전체 재학습합니다...")
            self.db = {}  # DB 초기화

        # 마지막 sync 시간 표시
        last_sync = self.db.get("__meta__", {}).get("last_sync")
        if not silent and last_sync:
            print(f"⏱️  마지막 동기화: {last_sync}")

        # 일일 사용량 로드
        today = datetime.now().strftime("%Y-%m-%d")
        usage_data = {}
        if os.path.exists(USAGE_LOG_FILE):
            try:
                with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: usage_data = json.load(f)
            except: pass
        daily_calls = usage_data.get(today, 0)

        md_files = glob.glob(os.path.join(OBSIDIAN_VAULT_PATH, "**/*.md"), recursive=True)

        # 제외 폴더/파일 필터 (SYNC_EXCLUDE_DIRS / SYNC_EXCLUDE_FILES 기반)
        def _is_excluded(path):
            p = path.replace("\\", "/")
            if any(f"/{d}/" in p or p.endswith(f"/{d}") for d in SYNC_EXCLUDE_DIRS): return True
            if any(excl in os.path.basename(path) for excl in SYNC_EXCLUDE_FILES): return True
            return False

        md_files = [f for f in md_files if not _is_excluded(f)]
        md_files_set = set(md_files)
        updated = 0

        if not silent:
            print(f"📂 학습 대상: {len(md_files)}개 파일 "
                  f"(제외 폴더: {', '.join(SYNC_EXCLUDE_DIRS)})")

        # 삭제된 파일 + 0청크 좀비 항목 DB에서 제거
        orphans = [p for p in list(self.db.keys())
                   if p != "__meta__" and (p not in md_files_set or not self.db[p].get("chunks"))]
        if orphans:
            for p in orphans:
                del self.db[p]
            if not silent:
                print(f"🗑️  DB 정리: {len(orphans)}개 제거 (삭제된 파일 또는 빈 항목)")

        # 신규/변경 파일만 필터링 (크기 제한 없이 모두 포함)
        to_update = [
            f for f in md_files
            if (f not in self.db or self.db[f].get("mtime", 0) < os.path.getmtime(f))
        ]
        total = len(to_update)

        for idx, f_path in enumerate(to_update, 1):
            mtime = os.path.getmtime(f_path)
            try:
                with open(f_path, 'r', encoding='utf-8') as f: content = f.read()
                if not content.strip(): continue

                links = list(set([l.split('|')[0] for l in re.findall(r'\[\[(.*?)\]\]', content)]))
                tags = list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content)))
                importance = _score_importance(content, os.path.basename(f_path))

                # 대용량 파일은 압축 후 임베딩 (200KB 초과인 경우만)
                is_large = (os.path.getsize(f_path) > MAX_FILE_SIZE_KB * 1024)
                chunks = _semantic_chunks(content)
                if not chunks:
                    continue  # YAML만 있고 본문 없는 파일 건너뜀
                if is_large:
                    if not silent: print(f"\n📦 압축 중: {os.path.basename(f_path)}")
                    compressed = _compress_content(content, os.path.basename(f_path))
                    if not compressed:
                        if not silent: print(f"\n⚠️  압축 실패, 건너뜀: {os.path.basename(f_path)}")
                        continue
                    chunks = _semantic_chunks(compressed)

                if not silent:
                    print(f"🔄 [{idx}/{total}] {os.path.basename(f_path)}", end="\r")

                file_data = {"mtime": mtime, "importance": importance, "chunks": []}
                skip_file = False
                hit_limit = False
                for c in chunks:
                    if daily_calls >= MAX_DAILY_EMBED_CALLS:
                        if not silent: print(f"\n🚨 [서킷 브레이커] 금일 리미트({MAX_DAILY_EMBED_CALLS:,}회) 도달. 중단.")
                        hit_limit = True
                        break
                    res = None
                    for attempt in range(2):
                        try:
                            res = client.models.embed_content(
                                model="gemini-embedding-001",
                                contents=c,
                                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                            break
                        except: time.sleep(0.5)

                    if not res or not res.embeddings:
                        skip_file = True
                        break

                    daily_calls += 1
                    file_data["chunks"].append({"text": c, "embedding": res.embeddings[0].values, "links": links, "tags": tags})
                    time.sleep(0.1)

                if skip_file:
                    if not silent: print(f"\n❌ API 응답 지연 건너뜀: {os.path.basename(f_path)}")
                    continue
                if hit_limit:
                    continue  # 빈 chunks로 DB 저장 방지

                self.db[f_path] = file_data
                updated += 1
            except: continue

        # 마지막 sync 시간 저장
        if "__meta__" not in self.db:
            self.db["__meta__"] = {}
        self.db["__meta__"]["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.db["__meta__"]["chunk_version"] = CHUNK_VERSION

        # 사용량 로그 저장
        usage_data[today] = daily_calls
        try:
            with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(usage_data, f)
        except: pass

        if updated > 0 or orphans:
            self._save_db()
            if not silent: print(f"\n💾 완료: {updated}개 업데이트, {len(orphans)}개 정리")
        else:
            if not silent: print("\n✨ 모든 자료가 최신 상태입니다.")

    def search(self, query, k=5):
        self._reload_if_updated()  # watcher 업데이트 자동 반영

        # 전체 청크 수집
        all_chunks = []
        for path, data in self.db.items():
            for c in data.get("chunks", []):
                if "embedding" not in c:
                    continue
                all_chunks.append({
                    "text": c["text"],
                    "embedding": c["embedding"],
                    "links": c.get("links", []),
                    "source": os.path.basename(path),
                    "importance": data.get("importance", "LOW"),
                })
        if not all_chunks:
            return []

        # --- 벡터 점수 ---
        try:
            res = client.models.embed_content(
                model="gemini-embedding-001",
                contents=query,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
            q_emb = res.embeddings[0].values
            vec_scores = [cosine_similarity(q_emb, c["embedding"]) for c in all_chunks]
            _increment_usage("rag")
        except:
            vec_scores = [0.0] * len(all_chunks)

        # --- BM25 점수 (한국어 형태소 없이 공백 분리) ---
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [c["text"].split() for c in all_chunks]
            bm25 = BM25Okapi(tokenized)
            bm25_raw = bm25.get_scores(query.split())
            bm25_max = max(bm25_raw) or 1
            bm25_scores = [s / bm25_max for s in bm25_raw]  # 0~1 정규화
        except:
            bm25_scores = [0.0] * len(all_chunks)

        # --- 하이브리드 점수 (벡터 70% + BM25 30%) + 중요도 보정 + 부분문자열 보정 ---
        importance_bonus = {"HIGH": 0.05, "MEDIUM": 0.02, "LOW": 0.0}
        # 쿼리 토큰 중 하나라도 텍스트에 부분 포함되면 보너스 (한국어 조사/어미 대응)
        query_tokens = query.split()
        for i, c in enumerate(all_chunks):
            bonus = importance_bonus.get(c.get("importance", "LOW"), 0.0)
            substr_bonus = 0.3 if any(tok in c["text"] for tok in query_tokens) else 0.0
            c["score"] = vec_scores[i] * 0.7 + bm25_scores[i] * 0.3 + bonus + substr_bonus

        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        return [r for r in all_chunks[:k] if r["score"] >= 0.15]

# ==============================================================================
# [2. Vibe Coding Tools (파일 제어 권한 도구)]
# ==============================================================================
def read_file(filepath: str) -> str:
    """지정된 경로의 파일 내용을 읽어옵니다. 코드를 수정하기 전에 먼저 읽어보세요.
    파일명만 입력 시(예: '2025-10-17.md') Vault 전체에서 자동으로 파일을 찾습니다."""
    try:
        p = Path(filepath)
        # 절대경로이거나 파일이 바로 존재하면 그대로 읽기
        if p.is_absolute() and p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                return f.read()
        # 상대경로 또는 파일명만 입력된 경우 → Vault 전체에서 탐색
        if not p.is_absolute():
            candidates = list(Path(OBSIDIAN_VAULT_PATH).rglob(p.name))
            if candidates:
                with open(candidates[0], 'r', encoding='utf-8') as f:
                    return f.read()
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """지정된 경로에 파일을 생성하거나 내용을 덮어씁니다. 코드를 작성하거나 수정할 때 사용하세요."""
    try:
        p = Path(filepath)
        if p.suffix == '.py':
            import ast
            try: ast.parse(content)
            except SyntaxError as se: return f"문법 오류로 저장 실패: {se}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return f"Success: {filepath} 파일에 성공적으로 저장되었습니다."
    except Exception as e:
        return f"Error writing file: {e}"

def list_files(directory: str) -> str:
    """지정된 디렉토리 내의 파일 및 폴더 목록을 반환합니다. 구조를 파악할 때 사용하세요."""
    try:
        return "\n".join(os.listdir(directory))
    except Exception as e:
        return f"Error listing directory: {e}"

def move_file(src: str, dst: str) -> str:
    """파일을 src에서 dst로 이동합니다. 바탕화면 → Vault 정리 등에 사용하세요."""
    try:
        s = Path(src).resolve()
        d = Path(dst).resolve()
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(s).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] 출발 경로가 허용 범위 밖입니다 → {src}"
        if not any(str(d).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] 목적지 경로가 허용 범위 밖입니다 → {dst}"
        if not s.exists():
            return f"Error: 파일이 존재하지 않습니다 → {src}"
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return f"Success: 이동 완료 → {src}  →  {dst}"
    except Exception as e:
        return f"Error moving file: {e}"

def delete_file(filepath: str) -> str:
    """지정된 파일을 삭제합니다. 파일 이동 후 원본 제거, 불필요한 파일 정리에 사용하세요."""
    try:
        p = Path(filepath).resolve()
        # Vault 내부 또는 바탕화면만 허용
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] Vault/바탕화면 외부 경로는 삭제할 수 없습니다 → {filepath}"
        if not p.exists():
            return f"Error: 파일이 존재하지 않습니다 → {filepath}"
        if p.is_dir():
            return f"Error: 디렉토리는 삭제할 수 없습니다 (파일만 가능) → {filepath}"
        p.unlink()
        return f"Success: 삭제 완료 → {filepath}"
    except Exception as e:
        return f"Error deleting file: {e}"

def execute_script(filepath: str) -> str:
    """작성된 파이썬 스크립트를 즉시 실행하고 결과를 반환한다. 코드를 작성한 뒤 검증할 때 사용하세요."""
    try:
        p = Path(filepath).resolve()
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] Vault/바탕화면 외부 경로의 스크립트는 실행할 수 없습니다 → {filepath}"
        if p.suffix != '.py':
            return f"🚫 [보안] .py 파일만 실행 가능합니다 → {filepath}"
        res = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, timeout=30)
        return f"--- Output ---\n{res.stdout}\n--- Error ---\n{res.stderr}"
    except Exception as e:
        return f"Execution Failed: {e}"

def backup_system() -> str:
    """SYSTEM 폴더 전체를 ZIP으로 압축 백업한다."""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "db_backup")
        os.makedirs(backup_dir, exist_ok=True)
        target = os.path.join(backup_dir, f"Onew_Backup_{ts}")
        shutil.make_archive(target, 'zip', os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM"))
        return f"Success: 백업 완료 → {target}.zip"
    except Exception as e:
        return f"Backup Failed: {e}"

def _get_search_count() -> tuple[dict, str, int]:
    """오늘의 웹 검색 횟수를 반환한다."""
    today = datetime.now().strftime("%Y-%m-%d")
    usage_data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: usage_data = json.load(f)
        except: pass
    return usage_data, today, usage_data.get(f"search_{today}", 0)

def _increment_usage(category: str):
    """카테고리별 API 호출 횟수를 기록한다. category: 'chat', 'rag', 'summary', 'flowchart'"""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{category}_{today}"
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except: pass
    data[key] = data.get(key, 0) + 1
    try:
        with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)
    except: pass

# ==============================================================================
# [자동 클리핑 시스템]
# ==============================================================================
def _load_clip_config() -> dict:
    cfg = dict(CLIP_DEFAULTS)
    if os.path.exists(CLIP_CONFIG_FILE):
        try:
            with open(CLIP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg.update(json.load(f))
        except: pass
    return cfg

def _save_clip_config(cfg: dict):
    try:
        with open(CLIP_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except: pass

def _load_clip_index() -> dict:
    if os.path.exists(CLIP_INDEX_FILE):
        try:
            with open(CLIP_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def _save_clip_index(index: dict):
    try:
        with open(CLIP_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except: pass

def _is_recently_clipped(topic: str) -> bool:
    index = _load_clip_index()
    if topic not in index: return False
    try:
        last = datetime.strptime(index[topic]["date"], "%Y-%m-%d")
        return (datetime.now() - last).days < CLIP_DEDUP_DAYS
    except: return False

def _today_clip_count() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(USAGE_LOG_FILE): return 0
    try:
        with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(f"clip_{today}", 0)
    except: return 0

class AutoClipper:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        self.today_clips = []  # {"topic", "file", "status"}

    def start(self):
        if self._running: return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        self._stop_event.set()
        self._running = False

    def _run(self):
        cfg = _load_clip_config()
        if not cfg.get("enabled", True):
            self._running = False
            return

        today = datetime.now().strftime("%Y-%m-%d")
        done = _today_clip_count()
        max_clips = cfg.get("max_clips", 10)
        delay = cfg.get("delay_seconds", 30)

        if done >= max_clips:
            self._running = False
            return

        os.makedirs(CLIP_FOLDER, exist_ok=True)
        topics = cfg.get("topics", [])

        # 이전 세션에서 오늘 완료된 항목 복원 (목록 MD 연속성 유지)
        index = _load_clip_index()
        for topic in topics:
            entry = index.get(topic, {})
            if entry.get("date") == today:
                self.today_clips.append({
                    "topic": topic,
                    "file": entry.get("file", ""),
                    "status": "✅ (이전 세션)"
                })
        if self.today_clips:
            self._update_list_md(today)

        for topic in topics:
            if self._stop_event.is_set(): break

            done = _today_clip_count()
            cfg = _load_clip_config()  # 실행 중 설정 변경 반영
            max_clips = cfg.get("max_clips", 10)
            delay = cfg.get("delay_seconds", 30)

            if done >= max_clips: break
            if _is_recently_clipped(topic): continue
            if self._stop_event.is_set(): break

            try:
                search_tool = types.Tool(google_search=types.GoogleSearch())
                ans = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{topic} 최신 동향 상세 정리해줘",
                    config=types.GenerateContentConfig(tools=[search_tool])
                )
                result_text = ans.text or ""

                # 200KB 제한
                max_bytes = MAX_CLIP_FILE_KB * 1024
                encoded = result_text.encode('utf-8')
                if len(encoded) > max_bytes:
                    result_text = encoded[:max_bytes].decode('utf-8', errors='ignore')
                    result_text += "\n\n*(200KB 제한으로 잘림)*"

                safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)
                filename = f"{today}_{safe_topic}.md"
                filepath = os.path.join(CLIP_FOLDER, filename)

                content = (
                    f"---\ntags:\n  - 클리핑\n  - AI\n  - 자동수집\n"
                    f"날짜: {today}\n주제: {topic}\n---\n\n"
                    f"# {topic}\n\n> 자동 클리핑 ({today})\n\n{result_text}"
                )
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                # 인덱스 + 카운터 업데이트
                index = _load_clip_index()
                index[topic] = {"date": today, "file": filename}
                _save_clip_index(index)
                _increment_usage("clip")

                self.today_clips.append({"topic": topic, "file": filename, "status": "✅"})
                self._update_list_md(today)
                print(f"\n📎 [클리핑] {topic} → {filename}")

            except Exception as e:
                self.today_clips.append({"topic": topic, "file": "", "status": f"❌ {e}"})
                self._update_list_md(today)
                print(f"\n⚠️  [클리핑 오류] {topic}: {e}")
                log_error_to_vault(f"클리핑: {topic}", str(e))

            self._stop_event.wait(delay)

        self._running = False

    def _update_list_md(self, today: str):
        cfg = _load_clip_config()
        list_path = os.path.join(CLIP_FOLDER, f"{today}_클리핑목록.md")
        lines = [
            "---", "tags:", "  - 클리핑목록", f"날짜: {today}", "---", "",
            f"# {today} 자동 클리핑 목록", "",
            "| # | 주제 | 파일 | 상태 |",
            "|---|------|------|------|",
        ]
        for i, item in enumerate(self.today_clips, 1):
            flink = f"[[{item['file']}]]" if item['file'] else "-"
            lines.append(f"| {i} | {item['topic']} | {flink} | {item['status']} |")
        lines += [
            "", "---",
            f"설정 | 딜레이: {cfg.get('delay_seconds',30)}초 "
            f"| 최대: {cfg.get('max_clips',10)}개 "
            f"| 중복방지: {CLIP_DEDUP_DAYS}일",
        ]
        try:
            with open(list_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except: pass

    def status(self) -> str:
        cfg = _load_clip_config()
        today = datetime.now().strftime("%Y-%m-%d")
        done = _today_clip_count()
        state = "🔄 실행 중" if self._running else "⏸ 대기/완료"
        index = _load_clip_index()
        lines = [
            f"📎 [자동 클리핑 현황] {state}",
            f"- 오늘: {done}/{cfg.get('max_clips',10)}개 완료",
            f"- 딜레이: {cfg.get('delay_seconds',30)}초",
            f"- 자동클리핑: {'ON' if cfg.get('enabled',True) else 'OFF'}",
            f"- 중복방지: {CLIP_DEDUP_DAYS}일",
            "", "[주제 목록]",
        ]
        for i, t in enumerate(cfg.get("topics", []), 1):
            last = index.get(t, {}).get("date", "미수집")
            lines.append(f"  {i}. {t}  (최근: {last})")
        return "\n".join(lines)


def _clip_command(q: str, clipper: "AutoClipper") -> bool:
    """자연어 클리핑 명령 처리. 처리됐으면 True 반환."""
    t = q.strip()

    # ── 시작 ─────────────────────────────────────────
    if re.search(r'클리핑.*(시작|켜|on|열어|돌려|실행)', t, re.I):
        clipper.start(); print("📎 클리핑 시작됨."); return True

    # ── 정지 ─────────────────────────────────────────
    if re.search(r'클리핑.*(정지|꺼|off|멈춰|중지|그만|끄)', t, re.I):
        clipper.stop(); print("📎 클리핑 정지됨."); return True

    # ── 상태 ─────────────────────────────────────────
    if re.search(r'클리핑.*(상태|현황|어때|확인|보여|알려|몇)', t, re.I):
        print(clipper.status()); return True

    # ── 딜레이 변경: "딜레이 60", "간격 30초", "30초마다" ───
    m = re.search(r'(딜레이|간격|주기).*?(\d+)\s*초?', t)
    if not m: m = re.search(r'(\d+)\s*초\s*(마다|간격|딜레이)', t)
    if m and re.search(r'클리핑', t, re.I):
        sec = int(m.group(2) if m.lastindex >= 2 else m.group(1))
        print(set_clip_config(delay_seconds=sec)); return True

    # ── 횟수 변경: "횟수 5", "5개로", "10개로 늘려" ──────
    m = re.search(r'(\d+)\s*개', t)
    if m and re.search(r'클리핑.*(횟수|개수|수|늘|줄|변경|바꿔|설정)', t, re.I):
        print(set_clip_config(max_clips=int(m.group(1)))); return True

    # ── 주제 변경 ────────────────────────────────────────────
    is_topic_cmd = bool(re.search(r'클리핑.*(주제|topic)', t, re.I) or
                        re.search(r'주제.*(바꿔|변경|교체|설정)', t, re.I))
    if is_topic_cmd:
        new_topics = []

        # 명령어 노이즈 제거 헬퍼
        def _clean(s):
            # 앞쪽: "변경해줘", "바꿔줘", "클리핑", "주제" 등 제거
            s = re.sub(r'^(클리핑|주제|topic)\s*', '', s, flags=re.I).strip()
            s = re.sub(r'^(변경해줘?|바꿔줘?|교체해줘?|해줘?|변경|바꿔|교체)\s*', '', s, flags=re.I).strip()
            # 뒤쪽: "으로 바꿔줘", "주제" 잔여 제거
            s = re.sub(r'\s*(으?로\s*)?(바꿔|변경|교체|해)줘?\.?$', '', s).strip()
            s = re.sub(r'\s*(주제|topic)\s*$', '', s, flags=re.I).strip(' .,')
            return s

        # 패턴1: "주제: A, B" / "주제 A, B" 쉼표 목록
        m = re.search(r'주제\s*[:\s]\s*(.+)', t)
        if m:
            candidates = [_clean(s) for s in re.split(r'[,，/]', m.group(1)) if s.strip()]
            new_topics = [c for c in candidates if c]

        # 패턴2: "X로 바꿔줘" → X 추출
        if not new_topics:
            m = re.search(r'([가-힣a-zA-Z0-9\s]+?)(?:으?로)\s*(?:바꿔|변경|교체)', t)
            if m:
                c = _clean(m.group(1))
                if c: new_topics = [c]

        # 패턴3: "주제바꿔줘. X로" — 문장 끝 "X로" 형태
        if not new_topics:
            m = re.search(r'([가-힣a-zA-Z0-9]+)(?:으?로)[.\s]*$', t)
            if m:
                c = m.group(1).strip()
                if c: new_topics = [c]

        # 패턴4: "주제 X" 직접 지정 (fallback)
        if not new_topics:
            m = re.search(r'(?:주제|topic)\s+([가-힣a-zA-Z0-9\s,]+)', t, re.I)
            if m:
                parts = [_clean(s) for s in re.split(r'[,，]', m.group(1)) if s.strip()]
                new_topics = [p for p in parts if p]

        if new_topics:
            print(set_clip_config(topics=new_topics)); return True

    return False


def clip_status() -> str:
    """자동 클리핑 현황, 주제 목록, 설정을 보여준다."""
    if 'clipper' in globals(): return globals()['clipper'].status()
    return "클리핑 시스템이 초기화되지 않았습니다."

def set_clip_config(topics: list[str] = None, delay_seconds: int = None,
                    max_clips: int = None, enabled: bool = None) -> str:
    """자동 클리핑 설정을 변경한다.
    topics: 새 주제 리스트 (예: ["AI 뉴스", "Python 팁"])
    delay_seconds: 클리핑 간격 (초)
    max_clips: 하루 최대 클리핑 수
    enabled: True=ON / False=OFF
    """
    cfg = _load_clip_config()
    if topics        is not None: cfg["topics"]         = topics
    if delay_seconds is not None: cfg["delay_seconds"] = delay_seconds
    if max_clips     is not None: cfg["max_clips"]     = max_clips
    if enabled       is not None: cfg["enabled"]       = enabled
    _save_clip_config(cfg)
    msgs = []
    if topics        is not None: msgs.append(f"주제 {len(topics)}개 업데이트")
    if delay_seconds is not None: msgs.append(f"딜레이 {delay_seconds}초")
    if max_clips     is not None: msgs.append(f"최대 {max_clips}개")
    if enabled       is not None: msgs.append(f"자동클리핑 {'ON' if enabled else 'OFF'}")
    return "✅ 클리핑 설정 변경: " + ", ".join(msgs)


def analyze_trend(query: str) -> str:
    """Google 검색으로 최신 금융/기술/학습 트렌드를 분석한다."""
    # 웹 검색 일일 횟수 체크
    usage_data, today, search_count = _get_search_count()
    if search_count >= MAX_DAILY_SEARCHES:
        return f"🚫 [검색 테두리] 오늘 검색 한도({MAX_DAILY_SEARCHES}회)를 초과했습니다. (현재: {search_count}회)"

    # 허용 주제 필터 (SEARCH_ALLOW_TOPICS 비어있으면 무제한)
    if SEARCH_ALLOW_TOPICS:
        allowed = any(keyword in query for keyword in SEARCH_ALLOW_TOPICS)
        if not allowed:
            return (f"🚫 [검색 테두리] 허용되지 않은 주제입니다.\n"
                    f"허용 주제: {', '.join(SEARCH_ALLOW_TOPICS[:8])} 등")

    try:
        search_tool = types.Tool(google_search=types.GoogleSearchRetrieval())
        ans = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
        # 검색 횟수 기록
        usage_data[f"search_{today}"] = search_count + 1
        with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(usage_data, f)
        return f"🌐 [웹 검색 리포트] ({search_count+1}/{MAX_DAILY_SEARCHES}회)\n\n{ans.text}"
    except Exception as e:
        return f"Search Error: {e}"

# ==============================================================================
# [Google Calendar 연동]
# ==============================================================================
CALENDAR_CREDS_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "calendar_credentials.json")
CALENDAR_TOKEN_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "calendar_token.json")
CALENDAR_SCOPES      = ["https://www.googleapis.com/auth/calendar"]

def _get_calendar_service():
    """Google Calendar 서비스 객체를 반환한다. 최초 1회 브라우저 인증 필요."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(CALENDAR_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(CALENDAR_TOKEN_FILE, CALENDAR_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CALENDAR_CREDS_FILE):
                raise FileNotFoundError(
                    f"calendar_credentials.json 없음 → {CALENDAR_CREDS_FILE}\n"
                    "Google Cloud Console에서 OAuth2 자격증명을 다운로드 후 저장하세요.")
            flow = InstalledAppFlow.from_client_secrets_file(CALENDAR_CREDS_FILE, CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CALENDAR_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def calendar_list(days: int = 7) -> str:
    """오늘부터 N일간의 구글 캘린더 일정을 조회한다. (기본 7일)"""
    try:
        service = _get_calendar_service()
        from datetime import timezone
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        if not events:
            return f"📅 향후 {days}일간 일정 없음."
        lines = [f"📅 향후 {days}일 일정:"]
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))[:16]
            lines.append(f"- [{start}] {e.get('summary', '(제목없음)')}  (id: {e['id']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Calendar Error: {e}"

def _normalize_dt(dt: str) -> str:
    """날짜시간 문자열을 'YYYY-MM-DDTHH:MM:SS' 형식으로 정규화."""
    dt = dt.strip().replace(" ", "T")
    # 초 없으면 추가
    if len(dt) == 16:  # YYYY-MM-DDTHH:MM
        dt += ":00"
    # 날짜만 있으면 자정으로
    if len(dt) == 10:  # YYYY-MM-DD
        dt += "T00:00:00"
    return dt

def calendar_add(title: str, start: str, end: str, description: str = "") -> str:
    """구글 캘린더에 일정을 추가한다.
    start/end 형식: 'YYYY-MM-DDTHH:MM' (예: '2026-03-20T09:00')"""
    try:
        service = _get_calendar_service()
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": _normalize_dt(start), "timeZone": "Asia/Seoul"},
            "end":   {"dateTime": _normalize_dt(end),   "timeZone": "Asia/Seoul"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ 일정 추가 완료: [{start}] {title}  (id: {created['id']})"
    except Exception as e:
        return f"Calendar Error: {e}"

def calendar_update(event_id: str, title: str = "", start: str = "", end: str = "", description: str = "") -> str:
    """기존 일정을 수정한다. event_id는 calendar_list로 확인. 변경할 항목만 입력."""
    try:
        service = _get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        if title:       event["summary"] = title
        if description: event["description"] = description
        if start:       event["start"] = {"dateTime": _normalize_dt(start), "timeZone": "Asia/Seoul"}
        if end:         event["end"]   = {"dateTime": _normalize_dt(end),   "timeZone": "Asia/Seoul"}
        updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return f"✅ 일정 수정 완료: {updated.get('summary')} (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"

def calendar_delete(event_id: str) -> str:
    """구글 캘린더 일정을 삭제한다. event_id는 calendar_list로 확인."""
    try:
        service = _get_calendar_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"✅ 일정 삭제 완료 (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"

def check_errors() -> str:
    """온유_오류.md에서 최근 오류를 읽어 분석하고 원인과 조치를 제안한다."""
    log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
    if not os.path.exists(log_path):
        return "✅ 기록된 오류 없음."
    try:
        content = Path(log_path).read_text(encoding="utf-8").strip()
        if not content:
            return "✅ 기록된 오류 없음."

        # 최근 10개 항목만 추출
        entries = content.split("\n## ")
        recent = "\n## ".join(entries[-10:])

        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                f"다음은 온유 시스템 오류 로그다. 각 오류의 원인을 짧게 분석하고 "
                f"조치 방법을 제안하라. 한국어로, 항목별로 간결하게.\n\n{recent}"
            ),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        return f"🔍 [오류 분석 리포트]\n\n{res.text}"
    except Exception as e:
        return f"Error: {e}"

def log_error_to_vault(context: str, error: str):
    """오류를 Obsidian SYSTEM/온유_오류.md에 날짜별로 누적 기록. 최대 50개 유지."""
    try:
        log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n## {timestamp}\n- 상황: {context}\n- 오류: {error}\n"
        existing = ""
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                existing = f.read()
        # 최대 50개 항목 유지 (오래된 것부터 제거)
        entries = existing.split("\n## ")
        if len(entries) > 50:
            entries = entries[-50:]
            existing = "\n## ".join(entries)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(existing + entry)
    except: pass

def report_status() -> str:
    """오늘의 API 사용량, 비용, 저장된 지식 수를 보고한다."""
    _, today, search_count = _get_search_count()
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except: pass
    embed_count  = data.get(today, 0)
    chat_count   = data.get(f"chat_{today}", 0)
    rag_count    = data.get(f"rag_{today}", 0)
    sum_count    = data.get(f"summary_{today}", 0)
    flow_count   = data.get(f"flowchart_{today}", 0)
    doc_count    = len(onew.mem.db) if 'onew' in globals() else '?'
    return (f"📊 [온유 오늘 API 사용 내역]\n"
            f"  대화(chat):    {chat_count}회\n"
            f"  RAG 검색:      {rag_count}회\n"
            f"  임베딩(sync):  {embed_count:,} / {MAX_DAILY_EMBED_CALLS:,}회\n"
            f"  자동 요약:     {sum_count}회\n"
            f"  순서도 생성:   {flow_count}회\n"
            f"  웹 검색:       {search_count} / {MAX_DAILY_SEARCHES}회\n"
            f"─────────────────────────────\n"
            f"  보존 지식:     {doc_count}개 문서\n"
            f"  학습 제외:     {', '.join(SYNC_EXCLUDE_DIRS)}")

def search_vault(query: str) -> str:
    """옵시디언 Vault(개인 노트/일기/공부자료)에서 키워드를 검색한다.
    인물, 날짜, 대화 내용, 공부 기록 등 개인 기록을 찾을 때 사용하라.
    웹 검색(analyze_trend)과 다르며, 인터넷 연결 없이 로컬 DB에서 검색한다.
    """
    if 'onew' not in globals():
        return "Error: 온유 에이전트가 초기화되지 않았습니다."
    agent = globals()['onew']

    # 시크릿(회사) 모드: 민감 키워드 포함 결과 필터링
    if agent.location_mode == "work":
        if any(kw in query for kw in SENSITIVE_KEYWORDS):
            return "🔒 [시크릿 모드] 이 주제는 집에서 검색하세요."

    results = agent.mem.search(query, k=10)
    if not results:
        return f"Vault에서 '{query}'와 관련된 기록을 찾지 못했습니다."

    lines = [f"🔍 Vault 검색 결과: '{query}'"]
    for i, r in enumerate(results, 1):
        text = r['text']
        # 시크릿 모드: 결과 텍스트 내 민감 키워드 포함 시 해당 항목 제외
        if agent.location_mode == "work" and any(kw in text for kw in SENSITIVE_KEYWORDS):
            continue
        lines.append(f"\n[{i}] 출처: {r['source']}")
        lines.append(text[:400])

    if len(lines) == 1:  # 헤더만 남은 경우
        return "🔒 [시크릿 모드] 해당 검색 결과에 민감한 내용이 포함되어 있어 표시할 수 없습니다."
    return "\n".join(lines)

def set_secret_mode(on: bool) -> str:
    """시크릿 모드를 켜거나 끈다. on=True면 민감 주제 차단, on=False면 해제."""
    if 'onew' in globals():
        globals()['onew'].set_secret_mode(on)
    mode = "ON" if on else "OFF"
    return f"✅ 시크릿 모드 {mode} 완료."

def get_secret_mode() -> str:
    """현재 시크릿 모드 상태와 설정 방식을 확인한다. (WiFi 자동감지 or 수동 오버라이드)"""
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
    manual = config.get("manual_override")
    wifi_sec = _get_wifi_security()
    if manual is not None:
        mode = "ON (시크릿)" if manual else "OFF (일반)"
        return (f"🔒 시크릿 모드: {mode}\n"
                f"- 설정 방식: 수동 오버라이드\n"
                f"- WiFi 보안: {wifi_sec}\n"
                f"- 해제: '시크릿 자동' 입력 시 WiFi 자동감지로 복귀")
    else:
        if wifi_sec == "open":
            mode = "ON (시크릿) - 개방형 WiFi 감지"
        elif wifi_sec == "secured":
            mode = "OFF (일반) - 보안 WiFi 감지"
        else:
            mode = "OFF (일반) - WiFi 미감지, 기본값"
        return (f"🔍 시크릿 모드: {mode}\n"
                f"- 설정 방식: WiFi 자동감지\n"
                f"- 현재 WiFi 보안: {wifi_sec}\n"
                f"- 수동 변경: '시크릿 on' / '시크릿 off'")

# 온유가 사용할 수 있는 권한 목록
tool_map = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "move_file": move_file,
    "delete_file": delete_file,
    "execute_script": execute_script,
    "backup_system": backup_system,
    "analyze_trend": analyze_trend,
    "calendar_list": calendar_list,
    "calendar_add": calendar_add,
    "calendar_update": calendar_update,
    "calendar_delete": calendar_delete,
    "check_errors": check_errors,
    "report_status": report_status,
    "get_secret_mode": get_secret_mode,
    "set_secret_mode": set_secret_mode,
    "search_vault": search_vault,
    "clip_status": clip_status,
    "set_clip_config": set_clip_config,
}
onew_tools = [
    read_file, write_file, list_files, move_file, delete_file,
    execute_script, backup_system, analyze_trend,
    calendar_list, calendar_add, calendar_update, calendar_delete,
    check_errors, report_status, get_secret_mode, set_secret_mode,
    search_vault, clip_status, set_clip_config,
]

# ==============================================================================
# [3. 온유 본체]
# ==============================================================================
class OnewAgent:
    def __init__(self):
        self.mem = OnewPureMemory()
        self.history_records = []

        # 위치 모드 감지
        self.location_mode = detect_location_mode()

        # 시스템 프롬프트 주입 (Vibe Coding 권한 인지)
        prompt = self._build_system_prompt()
        if os.path.exists(SYSTEM_PROMPT_PATH):
            try:
                with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                    prompt += "\n\n" + f.read()
            except: pass
            
        self.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                tools=onew_tools,  # analyze_trend 함수가 내부적으로 웹 검색 수행
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

    def _save_history_to_vault(self):
        try:
            # 월별 폴더로 정리 (삭제 없이 보존)
            month_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화기록",
                                     datetime.now().strftime("%Y-%m"))
            os.makedirs(month_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            save_path = os.path.join(month_dir, f"{timestamp}_온유_대화.md")

            lines = [
                f"---",
                f"tags: [대화기록, 온유]",
                f"날짜: {datetime.now().strftime('%Y-%m-%d')}",
                f"---",
                f"",
                f"# {timestamp} 온유 대화 기록\n"
            ]

            for msg in self.history_records:
                role = "💬 용준" if msg["role"] == "user" else "💡 온유"
                lines.append(f"## {role}")
                lines.append(msg["text"].strip())
                lines.append("")

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print(f"💾 대화 기록 자동 저장 → {save_path}")
        except Exception as e:
            print(f"❌ 대화 기록 저장 실패: {e}")

    def _build_system_prompt(self) -> str:
        """위치 모드에 따라 시스템 프롬프트를 다르게 구성."""
        base = (
            "당신은 고용준님의 완벽한 외부 뇌이자 바이브 코딩(Vibe Coding) 에이전트 '온유(Onew)'입니다. "
            "이제 당신은 컴퓨터의 파일을 직접 읽고 쓸 수 있는 권한(Tools)을 가집니다. "
            "사용자가 파일 수정이나 생성을 요청하면 즉시 도구를 사용하여 파일을 제어하세요. "
            "철저히 팩트 기반으로 답변하며, 감정적 위로보다 확실한 행동(결과물)으로 증명하세요."
        )
        if self.location_mode == "work":
            base += (
                "\n\n[회사 모드 활성화] "
                "현재 회사 네트워크에서 접속 중입니다. "
                "공부(공조냉동, OCU), 업무, 코딩, 일정 관련 대화만 응답하세요. "
                "건강 문제, 수술 계획, 개인 감정, 심리적 고민 등 사적인 내면 주제는 "
                "'집에서 이야기해요'라고 짧게 안내하고 응답을 거절하세요."
            )
        return base

    def _new_chat_session(self, prev_summary: str = ""):
        """채팅 세션만 초기화 (메모리 DB는 유지). 이전 맥락 요약 주입 가능."""
        prompt = self._build_system_prompt()
        if prev_summary:
            prompt += f"\n\n[이전 대화 맥락]: {prev_summary}"
        if os.path.exists(SYSTEM_PROMPT_PATH):
            try:
                with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                    prompt += "\n\n" + f.read()
            except: pass
        self.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                tools=onew_tools,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

    def set_secret_mode(self, on: bool):
        """시크릿 모드를 수동으로 설정하고 onew_location.json에 저장."""
        config = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        config["manual_override"] = on
        with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.location_mode = "work" if on else "home"
        self._new_chat_session()
        if on:
            print("🔒 [시크릿 모드 ON] 개인·민감 주제가 차단됩니다. '시크릿 off'로 해제 가능.")
        else:
            print("🔓 [시크릿 모드 OFF] 모든 대화 가능합니다. '시크릿 on'으로 재설정 가능.")

    def clear_secret_override(self):
        """수동 오버라이드를 제거 → 이후 WiFi 자동 감지로 복귀."""
        config = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        config.pop("manual_override", None)
        with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.location_mode = detect_location_mode()
        self._new_chat_session()
        mode_str = "시크릿 ON (개방형 WiFi)" if self.location_mode == "work" else "시크릿 OFF (보안 WiFi)"
        print(f"🔄 [자동 감지 복귀] 현재 모드: {mode_str}")

    def _summarize_last_session(self) -> str:
        """저장된 마지막 대화 파일을 읽어 한 줄 요약 반환."""
        try:
            month_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화기록",
                                     datetime.now().strftime("%Y-%m"))
            files = sorted(Path(month_dir).glob("*_온유_대화.md"))
            if not files:
                return ""
            content = files[-1].read_text(encoding="utf-8")[:3000]
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"다음 대화를 2문장 이내로 핵심만 요약하라. 한국어로.\n\n{content}",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            return res.text.strip()
        except:
            return ""

    def _reset_chat_if_needed(self):
        turn = len(self.history_records)

        # 5턴마다 자동 저장 (세션 유지)
        if turn > 0 and turn % 5 == 0:
            self._save_history_to_vault()
            print("💾 [자동저장] 대화 기록 저장됨")

        # 20턴 초과 시 이전 맥락 요약 → 새 세션에 주입 후 리셋
        if turn > 20:
            self._save_history_to_vault()
            summary = self._summarize_last_session()
            self.history_records = []
            self._new_chat_session(prev_summary=summary)
            if summary:
                print(f"✅ 새 세션 시작\n📝 [이전 맥락]: {summary}")
            else:
                print("✅ 새 세션 시작 (이전 대화는 저장되었습니다)")

    def ask(self, query, silent_search=False):
        self._reset_chat_if_needed()

        # 회사 모드: 민감 주제 클라이언트 측 차단 (API 호출 전에 막음)
        if self.location_mode == "work":
            if any(kw in query for kw in SENSITIVE_KEYWORDS):
                print("==================================================")
                print("💡 온유: 이 주제는 집에서 이야기해요.")
                print("   지금은 공부·업무·코딩 관련 대화만 할게요.")
                print("==================================================")
                return

        if not silent_search:
            print(f"\n온유(Onew) 🔍 지식 네트워크 탐색 중...")
        
        # 1. RAG 기반 지식 검색
        res = self.mem.search(query)
        ctx = ""
        source_list = "없음"
        if not res:
            if not silent_search: print("💡 관련된 기억을 찾지 못했습니다. 일반 지식과 Vibe 권한으로 응답합니다.")
        else:
            ctx = "\n".join([f"[출처: {r['source']}] (연결: {r['links']})\n{r['text']}" for r in res])
            source_list = ", ".join(list(set([r['source'] for r in res])))

        # 2. 질문 전송
        try:
            ans = self.chat.send_message(f"Context:\n{ctx}\n\n명령: {query}")
            _increment_usage("chat")
        except Exception as e:
            print(f"❌ API 호출 오류: {e}")
            log_error_to_vault("API 호출", str(e))
            return

        # 3. 🌟 Vibe Coding: 도구(Tool) 자동 실행 루프 (최대 10회)
        tool_loop_count = 0
        while getattr(ans, 'function_calls', None) and tool_loop_count < 10:
            tool_loop_count += 1
            tool_responses = []
            for call in ans.function_calls:
                func_name = call.name
                
                # 인자(args) 파싱 방어 로직
                if isinstance(call.args, dict): args_dict = call.args
                elif hasattr(call.args, "model_dump"): args_dict = call.args.model_dump()
                else: args_dict = {k: getattr(call.args, k) for k in dir(call.args) if not k.startswith('_')}
                
                target = args_dict.get('filepath') or args_dict.get('directory') or str(args_dict)
                if not silent_search:
                    print(f"🛠️ [Vibe Coding] 온유가 시스템을 제어합니다: [{func_name}] -> {target}")
                
                # 실제 함수 실행
                try:
                    if func_name in tool_map:
                        result = tool_map[func_name](**args_dict)
                    else:
                        result = f"Error: 존재하지 않는 기능입니다 ({func_name})"
                except Exception as e:
                    result = f"Error 실행 실패: {e}"
                    log_error_to_vault(f"Tool 실행: {func_name}", str(e))
                
                # 결과를 모델이 이해할 수 있게 패키징
                tool_responses.append(types.Part.from_function_response(
                    name=func_name,
                    response={"result": result}
                ))
            
            # 도구 실행 결과를 다시 모델에게 던져서 최종 텍스트 답변을 받아냄
            ans = self.chat.send_message(tool_responses)
            _increment_usage("chat")
        
        # 4. 최종 결과 출력 및 히스토리 저장
        final_text = ans.text if ans.text else "(파일 제어 작업이 완료되었습니다.)"
        self.history_records.append({"role": "user", "text": query})
        self.history_records.append({"role": "model", "text": final_text})
        
        print(f"==================================================")
        print(f"💡 온유:\n{final_text}\n")
        if source_list != "없음":
            print(f"📚 참고자료: {source_list}")
        print(f"==================================================")

def _auto_backup():
    """시작 시 SYSTEM 코드 파일(.py, .md)을 code_backup/YYYY-MM-DD/ 에 자동 백업."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = os.path.join(SYSTEM_PATH, "code_backup", today)
        # 오늘 이미 백업했으면 건너뜀
        if os.path.exists(backup_dir):
            return
        os.makedirs(backup_dir, exist_ok=True)
        import shutil
        backed = 0
        for f in os.listdir(SYSTEM_PATH):
            if f.endswith((".py", ".md")) and "복사본" not in f:
                shutil.copy2(os.path.join(SYSTEM_PATH, f), os.path.join(backup_dir, f))
                backed += 1
        print(f"💾 [자동 백업] {backed}개 파일 → code_backup/{today}/")
    except Exception as e:
        print(f"⚠️ [자동 백업] 실패: {e}")

if __name__ == "__main__":
    _auto_backup()
    onew = OnewAgent()
    clipper = AutoClipper()
    
    # 🌟 [과금 방어 1단계] 수동 동기화 전용 명령어: gemini --sync
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        print("⚠️ [수동 학습 모드] 새로 작성된 노트를 온유의 뇌(DB)에 각인시킵니다...")
        onew.mem.sync(silent=False)
        print("✅ 학습이 완료되었습니다. 이제 평소처럼 gemini 명령어를 사용하십시오.")
        sys.exit(0)

    # 🌟 [과금 방어 2단계] 단발성 CLI 모드 (스캔 절대 안 함)
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        # onew.mem.sync() 로직을 완전히 삭제. 오직 기존에 저장된 로컬 DB만 읽습니다.
        onew.ask(query, silent_search=True)
    
    # 🌟 [과금 방어 3단계] 대화형 챗봇 모드
    else:
        print("🌟 온유(Onew) Vibe Coding 에이전트 가동 중...")
        wifi_sec = _wifi_security_cache.get("result", _get_wifi_security())  # 캐시 우선 사용
        config_data = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except: pass
        is_manual = config_data.get("manual_override") is not None
        if onew.location_mode == "work":
            reason = "수동 설정" if is_manual else f"개방형 WiFi ({wifi_sec})"
            print(f"🔒 [시크릿 모드 ON] 개인 민감 주제 차단 중. ({reason})")
            print("   해제하려면: '시크릿 off' 또는 '시크릿 자동'(WiFi 재감지)")
        else:
            reason = "수동 설정" if is_manual else f"보안 WiFi ({wifi_sec})"
            print(f"🔓 [시크릿 모드 OFF] 모든 대화 가능. ({reason})")
            print("   활성화하려면: '시크릿 on'")

        # 🧠 [자율 학습] 마지막 sync로부터 6시간 이상 지났으면 자동 학습
        last_sync_str = onew.mem.db.get("__meta__", {}).get("last_sync")
        auto_sync_needed = True
        if last_sync_str:
            try:
                last_sync_dt = datetime.strptime(last_sync_str, "%Y-%m-%d %H:%M")
                if (datetime.now() - last_sync_dt).total_seconds() < AUTO_SYNC_HOURS * 3600:
                    auto_sync_needed = False
            except: pass

        if auto_sync_needed:
            print(f"🧠 [자율 학습] 마지막 동기화: {last_sync_str or '없음'} → 자동 업데이트 시작...")
            onew.mem.sync(silent=False)
        else:
            print(f"✅ [자율 학습] 최신 상태 확인 완료 (마지막: {last_sync_str})")

        print("🌐 [웹 검색] Google Search 직접 연결 완료.")

        # 📎 자동 클리핑 시작
        clip_cfg = _load_clip_config()
        if clip_cfg.get("enabled", True):
            done = _today_clip_count()
            max_c = clip_cfg.get("max_clips", 10)
            if done < max_c:
                clipper.start()
                print(f"📎 [자동 클리핑] 백그라운드 시작 ({done}/{max_c}개 완료, {clip_cfg.get('delay_seconds',30)}초 간격)")
            else:
                print(f"📎 [자동 클리핑] 오늘 {done}개 완료 (한도 도달)")
        else:
            print("📎 [자동 클리핑] OFF (켜려면: '클리핑 시작')")

        # 📅 오늘 일정 + D-day 자동 표시
        try:
            today_schedule = calendar_list(1)
            if "없음" not in today_schedule:
                print(f"\n{today_schedule}")
            exam_dday = (EXAM_DATE - datetime.now()).days
            print(f"⏳ 공조냉동 실기 D-{exam_dday}")
        except: pass

        # 🔍 오류 로그 자동 점검
        try:
            log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                # 마지막 수정 시간이 24시간 이내인 경우만 알림
                mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
                if (datetime.now() - mtime).total_seconds() < 86400:
                    print(f"\n⚠️  최근 오류 기록 감지됨. '오류 확인해줘'라고 말하면 분석합니다.")
        except: pass

        print("\n💬 파일 수정, 코드 작성, 웹 검색 등 무엇이든 명령하십시오.")
        while True:
            try:
                q = input("\n💬 용준 님: ")
                if q.strip().lower() in ['끝', 'exit', 'quit']: break
                elif q.strip().lower() in ['동기화', 'sync', '싱크']:
                    onew.mem.sync(silent=False)
                elif q.strip().lower() in ['시크릿 on', '시크릿on', '시크릿모드 on', '시크릿모드on', 'secret on', '보안모드 on']:
                    onew.set_secret_mode(True)
                elif q.strip().lower() in ['시크릿 off', '시크릿off', '시크릿모드 off', '시크릿모드off', 'secret off', '보안모드 off']:
                    onew.set_secret_mode(False)
                elif q.strip().lower() in ['시크릿 자동', '자동감지', '시크릿모드 자동', 'secret auto']:
                    onew.clear_secret_override()
                elif _clip_command(q, clipper):
                    pass
                elif q.strip(): onew.ask(q)
            except KeyboardInterrupt: break
        print("온유 시스템 종료.")