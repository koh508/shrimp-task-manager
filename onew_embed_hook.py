"""
onew_embed_hook.py — Claude Code PostToolUse 훅: .md 파일 즉시 LanceDB 임베딩

- Edit/Write 도구로 Vault 내 .md 파일 수정 시 자동 실행
- DB 초기화 중이거나 이상 상태면 조용히 건너뜀
- 실패는 항상 sys.exit(0) — Claude Code/온유 작업 방해 금지
"""
import hashlib, json, os, re, sys, time
from pathlib import Path

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH   = str(Path(SCRIPT_DIR).parent)
LANCE_DIR    = os.path.join(SCRIPT_DIR, ".onew_lance_db")
HASH_FILE    = os.path.join(SCRIPT_DIR, "onew_content_hashes.json")
USAGE_FILE   = os.path.join(SCRIPT_DIR, "api_usage_log.json")
EMBED_DIM    = 3072
MAX_FILE_KB  = 200
MAX_CHUNKS   = 150
EXCLUDE_DIRS  = {
    "대화기록","venv",".obsidian",".git","code_backup",
    ".db","__pycache__","Onew_Core_Backup_절대건드리지말것"
}
EXCLUDE_FILES = {"onew_pure_db","api_usage_log","onew_content_hashes"}


def _is_db_ready() -> bool:
    """LanceDB가 초기화 완료 상태인지 확인."""
    versions_dir = os.path.join(LANCE_DIR, "chunks.lance", "_versions")
    if not os.path.isdir(versions_dir):
        return False
    manifests = [f for f in os.listdir(versions_dir) if f.endswith(".manifest")]
    return len(manifests) > 0


def _is_excluded(path: str) -> bool:
    p = path.replace("\\", "/")
    if any(f"/{d}/" in p or p.endswith(f"/{d}") for d in EXCLUDE_DIRS):
        return True
    return any(excl in os.path.basename(path) for excl in EXCLUDE_FILES)


def _semantic_chunks(content: str, max_chunk: int = 2000) -> list:
    body = re.sub(r'^---[\s\S]*?---\n?', '', content.strip())
    sections = re.split(r'(?=\n#{1,3} )', body)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_chunk:
            chunks.append(sec)
        else:
            paras = [p.strip() for p in re.split(r'\n{2,}', sec) if p.strip()]
            buf = ""
            for p in paras:
                if len(buf) + len(p) + 1 <= max_chunk:
                    buf = (buf + "\n\n" + p).strip()
                else:
                    if buf:
                        chunks.append(buf)
                    if len(p) > max_chunk:
                        for i in range(0, len(p), max_chunk):
                            chunks.append(p[i:i+max_chunk])
                    else:
                        buf = p
            if buf:
                chunks.append(buf)
    return [c for c in chunks if len(c.strip()) > 20]


def _score_importance(content: str, filename: str) -> str:
    score = 0
    study_kw = ["공조냉동","냉매","압축기","응축기","증발기","COP","소방","방재","OCU","시험","오답","공식","계산"]
    event_kw = ["산재","양악","병원","면담","복직","마감","제출","D-"]
    if re.match(r'\d{4}-\d{2}-\d{2}', filename):
        score += 1
    for kw in study_kw:
        if kw in content: score += 1
    for kw in event_kw:
        if kw in content: score += 2
    score += min(len(re.findall(r'\[\[.*?\]\]', content)) // 3, 3)
    if score >= 5:   return "HIGH"
    elif score >= 2: return "MEDIUM"
    else:            return "LOW"


def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            import subprocess
            r = subprocess.run(
                ["powershell","-NoProfile","-Command",
                 "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY','User')"],
                capture_output=True, text=True, timeout=5)
            key = r.stdout.strip()
        except: pass
    return key


def embed_file(file_path: str) -> str:
    """단일 .md 파일을 LanceDB에 임베딩. 반환: 결과 메시지."""
    if not _is_db_ready():
        return "skip: DB 미초기화"

    if not os.path.isfile(file_path):
        return "skip: 파일 없음"
    if not file_path.lower().endswith(".md"):
        return "skip: .md 아님"
    if not file_path.replace("\\","/").startswith(VAULT_PATH.replace("\\","/")):
        return "skip: Vault 외부"
    if _is_excluded(file_path):
        return "skip: 제외 대상"
    if os.path.getsize(file_path) > MAX_FILE_KB * 1024:
        return f"skip: {MAX_FILE_KB}KB 초과"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"skip: 파일 읽기 오류 ({e})"

    if not content.strip():
        return "skip: 빈 파일"

    # 해시 체크 — 내용 변경 없으면 스킵 (API 0원)
    content_hash = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
    hash_cache = {}
    try:
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            hash_cache = json.load(f)
    except: pass

    if hash_cache.get(file_path) == content_hash:
        return "skip: 내용 변경 없음 (0 API)"

    # 일일 임베딩 한도 체크
    today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    usage = {}
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            usage = json.load(f)
    except: pass
    daily_calls = usage.get(today, 0)
    if daily_calls >= 10000:
        return "skip: 일일 임베딩 한도 도달"

    # 청킹
    chunks = _semantic_chunks(content)
    if not chunks:
        return "skip: 청크 없음"
    chunks = chunks[:MAX_CHUNKS]

    # Gemini 임베딩
    try:
        from google import genai
        from google.genai import types as gtypes
    except ImportError:
        return "skip: google-genai 미설치"

    api_key = _get_api_key()
    if not api_key:
        return "skip: API 키 없음"

    gclient = genai.Client(api_key=api_key)
    fname   = os.path.basename(file_path)
    mtime   = os.path.getmtime(file_path)
    links   = json.dumps(list(set(re.findall(r'\[\[(.*?)\]\]', content))), ensure_ascii=False)
    tags    = json.dumps(list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content))), ensure_ascii=False)
    importance   = _score_importance(content, fname)
    user_written = "author: Onew" not in content[:500]

    new_rows = []
    for i, chunk in enumerate(chunks):
        if daily_calls >= 10000:
            break
        for attempt in range(2):
            try:
                res = gclient.models.embed_content(
                    model="gemini-embedding-001",
                    contents=f"[문서명: {fname}]\n{chunk}",
                    config=gtypes.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                break
            except:
                time.sleep(0.5)
                res = None
        if not res or not res.embeddings:
            return f"오류: 청크 {i} 임베딩 실패"
        vec = list(res.embeddings[0].values)
        if len(vec) != EMBED_DIM:
            continue
        new_rows.append({
            "path":         file_path,
            "chunk_idx":    i,
            "text":         f"[문서명: {fname}]\n{chunk}",
            "vector":       vec,
            "mtime":        mtime,
            "links":        links,
            "tags":         tags,
            "importance":   importance,
            "user_written": user_written,
            "hit_log":      "[]",
        })
        daily_calls += 1
        time.sleep(0.1)

    if not new_rows:
        return "오류: 임베딩 행 없음"

    # LanceDB 업데이트
    try:
        import lancedb
        db    = lancedb.connect(LANCE_DIR)
        table = db.open_table("chunks")
        escaped = file_path.replace("'", "''")
        try:
            table.delete(f"path = '{escaped}'")
        except: pass
        table.add(new_rows)
        # FTS 인덱스 갱신
        try:
            table.create_fts_index("text", replace=True)
        except: pass
    except Exception as e:
        return f"오류: LanceDB 쓰기 실패 ({e})"

    # 해시 캐시 저장
    try:
        hash_cache[file_path] = content_hash
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            json.dump(hash_cache, f, ensure_ascii=False)
    except: pass

    # API 사용량 업데이트
    try:
        usage[today] = daily_calls
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(usage, f)
    except: pass

    return f"완료: {len(new_rows)}청크 임베딩 ({fname})"


def _hook_mode():
    """Claude Code PostToolUse 훅 모드."""
    try:
        raw       = sys.stdin.read()
        data      = json.loads(raw)
        file_path = data.get("tool_input", {}).get("file_path", "")
        if not file_path.lower().endswith(".md"):
            sys.exit(0)
        result = embed_file(file_path)
        if not result.startswith("skip"):
            print(f"[임베딩 훅] {result}", flush=True)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    if "--hook" in sys.argv:
        _hook_mode()
    elif len(sys.argv) > 1:
        sys.stdout.reconfigure(encoding="utf-8")
        print(embed_file(sys.argv[1]))
    else:
        print("사용법: python onew_embed_hook.py <file.md>")
        print("       python onew_embed_hook.py --hook  (훅 모드)")
