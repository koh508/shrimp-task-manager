"""
온유 동기화 테스트 모델 (500개 파일 샘플)
실제 DB 건드리지 않고 변경사항 검증용으로 사용.

사용법:
    python test_sync.py          # 500개 샘플로 전체 sync 테스트
    python test_sync.py --search "오석송"   # 검색 테스트
    python test_sync.py --clean  # 테스트 DB 초기화
"""
import sys, io, os, glob, json, random, hashlib, time, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import lancedb, pyarrow as pa, numpy as np

VAULT          = r"C:\Users\User\Documents\Obsidian Vault"
TEST_DB_DIR    = os.path.join(VAULT, "SYSTEM", "onew_test_db")
TEST_HASH_FILE = os.path.join(VAULT, "SYSTEM", "onew_test_hashes.json")
TEST_SAMPLE    = 300
EMBED_DIM      = 3072  # gemini-embedding-001 실제 출력 차원
CHUNK_VERSION  = "v3"

EXCLUDE_DIRS  = ["대화기록", "venv", ".obsidian", ".git",
                 "code_backup", "db_backup", "__pycache__", "Onew_Core_Backup"]
EXCLUDE_FILES = ["onew_pure_db", "api_usage_log", "onew_content_hashes",
                 "onew_test_hashes"]

# ── Gemini 클라이언트 ──────────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
except Exception as e:
    print(f"❌ Gemini 초기화 실패: {e}"); sys.exit(1)

# ── 청킹 (obsidian_agent.py와 동일) ───────────────────────────────────────────
import re
def _semantic_chunks(content, max_chunk=2000):
    body = re.sub(r'^---[\s\S]*?---\n?', '', content.strip())
    sections = re.split(r'(?=\n#{1,3} )', body)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec: continue
        if len(sec) <= max_chunk:
            chunks.append(sec)
        else:
            paras = [p.strip() for p in re.split(r'\n{2,}', sec) if p.strip()]
            buf = ""
            for p in paras:
                if len(buf) + len(p) + 1 <= max_chunk:
                    buf = (buf + "\n\n" + p).strip()
                else:
                    if buf: chunks.append(buf)
                    if len(p) > max_chunk:
                        for i in range(0, len(p), max_chunk):
                            chunks.append(p[i:i+max_chunk])
                    else:
                        buf = p
            if buf: chunks.append(buf)
    return [c for c in chunks if len(c.strip()) > 20]

# ── DB 초기화 ─────────────────────────────────────────────────────────────────
def _init_db():
    import shutil
    if os.path.exists(TEST_DB_DIR):
        shutil.rmtree(TEST_DB_DIR)
    if os.path.exists(TEST_HASH_FILE):
        os.remove(TEST_HASH_FILE)
    print("🗑️  테스트 DB 초기화 완료")

def _get_table():
    db = lancedb.connect(TEST_DB_DIR)
    schema = pa.schema([
        pa.field("path",         pa.string()),
        pa.field("chunk_idx",    pa.int32()),
        pa.field("text",         pa.string()),
        pa.field("vector",       pa.list_(pa.float32(), EMBED_DIM)),
        pa.field("mtime",        pa.float64()),
    ])
    existing = db.table_names() if hasattr(db, "table_names") else [str(t) for t in db.list_tables()]
    if "chunks" in existing:
        return db, db.open_table("chunks")
    return db, db.create_table("chunks", schema=schema, mode="overwrite")

# ── 파일 샘플링 ───────────────────────────────────────────────────────────────
def _sample_files():
    all_files = glob.glob(os.path.join(VAULT, "**/*.md"), recursive=True)
    def excluded(p):
        p2 = p.replace("\\", "/")
        if any(f"/{d}/" in p2 or p2.endswith(f"/{d}") for d in EXCLUDE_DIRS): return True
        if any(x in os.path.basename(p) for x in EXCLUDE_FILES): return True
        return False
    all_files = [f for f in all_files if not excluded(f)]

    # 폴더별 비율 유지한 stratified sampling
    by_folder = {}
    for f in all_files:
        folder = os.path.dirname(f).replace(VAULT, "").split(os.sep)[1] if os.sep in os.path.dirname(f).replace(VAULT, "") else "root"
        by_folder.setdefault(folder, []).append(f)

    sampled = []
    total = len(all_files)
    for folder, files in by_folder.items():
        n = max(1, round(len(files) / total * TEST_SAMPLE))
        sampled.extend(random.sample(files, min(n, len(files))))

    random.shuffle(sampled)
    return sampled[:TEST_SAMPLE]

# ── sync 테스트 ───────────────────────────────────────────────────────────────
def run_sync():
    files = _sample_files()
    print(f"📂 샘플: {len(files)}개 파일")

    _, tbl = _get_table()

    # DB가 비어있으면 해시 캐시 무시 (DB 소실 후 재실행 대비)
    try:
        db_empty = tbl.to_arrow().num_rows == 0
    except:
        db_empty = True

    hash_cache = {}
    if not db_empty and os.path.exists(TEST_HASH_FILE):
        try:
            with open(TEST_HASH_FILE, 'r', encoding='utf-8') as f:
                hash_cache = json.load(f)
        except: pass

    # 기존 mtime 로드
    db_mtimes = {}
    try:
        for row in tbl.search().select(["path", "mtime"]).limit(1_000_000).to_list():
            p = row["path"]
            if p not in db_mtimes or row["mtime"] > db_mtimes[p]:
                db_mtimes[p] = row["mtime"]
    except: pass

    BATCH_SIZE = 50
    batch_rows = []
    updated = skipped_hash = skipped_mtime = embed_calls = 0
    total = len(files)

    def _flush():
        if batch_rows:
            try:
                tbl.add(batch_rows)
                batch_rows.clear()
            except Exception as e:
                print(f"\n🚨 [DB Add 에러] {e}")
                if batch_rows:
                    print(f"   타입 확인: { {k: type(v).__name__ for k, v in batch_rows[0].items()} }")
                raise

    for idx, f_path in enumerate(files, 1):
        if not os.path.exists(f_path): continue
        mtime = os.path.getmtime(f_path)

        # mtime 체크
        if f_path in db_mtimes and db_mtimes[f_path] >= mtime:
            skipped_mtime += 1
            continue

        try:
            with open(f_path, 'r', encoding='utf-8') as f: content = f.read()
            if not content.strip(): continue

            # 해시 체크
            content_hash = hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()
            if hash_cache.get(f_path) == content_hash:
                skipped_hash += 1
                continue

            chunks = _semantic_chunks(content)
            if not chunks: continue
            chunks = chunks[:150]

            print(f"🔄 [{idx}/{total}] {os.path.basename(f_path)} ({len(chunks)}청크)", end="\r")

            new_rows = []
            for i, c in enumerate(chunks):
                res = None
                for attempt in range(2):
                    try:
                        res = client.models.embed_content(
                            model="gemini-embedding-001", contents=c,
                            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                        break
                    except: time.sleep(0.5)
                if not res or not res.embeddings: break
                embed_calls += 1
                vec = list(res.embeddings[0].values)
                if len(vec) != EMBED_DIM: continue
                new_rows.append({
                    "path": f_path, "chunk_idx": i,
                    "text": f"[문서명: {os.path.basename(f_path)}]\n{c}",
                    "vector": vec, "mtime": mtime,
                })
                time.sleep(0.05)

            if new_rows:
                escaped = f_path.replace("'", "''")
                try: tbl.delete(f"path = '{escaped}'")
                except: pass
                batch_rows.extend(new_rows)
                hash_cache[f_path] = content_hash
                updated += 1

            if updated % BATCH_SIZE == 0 and updated > 0:
                _flush()
                with open(TEST_HASH_FILE, 'w', encoding='utf-8') as f:
                    json.dump(hash_cache, f, ensure_ascii=False)

        except: continue

    _flush()
    with open(TEST_HASH_FILE, 'w', encoding='utf-8') as f:
        json.dump(hash_cache, f, ensure_ascii=False)

    try: row_count = tbl.to_arrow().num_rows
    except: row_count = updated  # fallback

    print(f"\n\n✅ 완료")
    print(f"   임베딩: {updated}개 파일, {embed_calls}회 API 호출")
    print(f"   스킵(mtime): {skipped_mtime}개 | 스킵(해시): {skipped_hash}개")
    print(f"   총 청크: {row_count}개")

# ── 검색 테스트 ───────────────────────────────────────────────────────────────
def run_search(query):
    _, tbl = _get_table()
    try:
        n = tbl.to_arrow().num_rows
    except:
        n = 0
    if n == 0:
        print("❌ 테스트 DB가 비어 있습니다. 먼저 sync를 실행하세요.")
        return

    res = client.models.embed_content(
        model="gemini-embedding-001", contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
    q_emb = list(res.embeddings[0].values)

    results = tbl.search(q_emb).metric("cosine").limit(5).to_list()

    # BM25
    try:
        from rank_bm25 import BM25Okapi
        texts = [r["text"] for r in results]
        bm25 = BM25Okapi([t.split() for t in texts])
        bm25_scores = bm25.get_scores(query.split())
        bm25_max = max(bm25_scores) or 1
        bm25_norm = [s / bm25_max for s in bm25_scores]
    except:
        bm25_norm = [0.0] * len(results)

    for i, (r, b) in enumerate(zip(results, bm25_norm)):
        vec_score = max(0.0, 1.0 - r.get("_distance", 1.0))
        score = vec_score * 0.7 + b * 0.3
        print(f"\n[{i+1}] {os.path.basename(r['path'])}  score={score:.3f}")
        print(r["text"][:200])

# ── 진입점 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean",  action="store_true", help="테스트 DB 초기화")
    parser.add_argument("--search", type=str, help="검색어")
    args = parser.parse_args()

    if args.clean:
        _init_db()
    elif args.search:
        run_search(args.search)
    else:
        run_sync()
