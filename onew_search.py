import os
import sys
import json
import subprocess
import time
from pathlib import Path
from google import genai
from google.genai import types

# Windows 환경에서 한글 깨짐 방지
sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# [설정]
# ==============================================================================
current_script_path = Path(__file__).resolve()
if "Obsidian Vault" in str(current_script_path):
    ROOT_PATH = str(current_script_path.parents[2])
else:
    ROOT_PATH = r"C:\Users\User\Documents\DdidA"

OBSIDIAN_VAULT_PATH = os.path.join(ROOT_PATH, "Obsidian Vault")
SYSTEM_PATH         = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")
LANCE_DB_DIR        = os.path.join(SYSTEM_PATH, ".onew_lance_db")
TOP_K = 5

# ==============================================================================
# [초기화 및 유틸리티]
# ==============================================================================
def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"],
                capture_output=True, text=True, timeout=5)
            key = result.stdout.strip()
        except: pass
    return key

# ==============================================================================
# [핵심 검색 로직 — LanceDB 사용]
# ==============================================================================
def search(query, k=TOP_K):
    api_key = get_api_key()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY를 찾을 수 없습니다.")
        sys.exit(1)

    if not os.path.exists(LANCE_DB_DIR):
        print(f"❌ ERROR: LanceDB가 없습니다 -> {LANCE_DB_DIR}\n먼저 온유를 실행해 sync_vault()를 완료해 주세요.")
        sys.exit(1)

    try:
        import lancedb
    except ImportError:
        print("❌ ERROR: lancedb 패키지가 없습니다. pip install lancedb")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 쿼리 임베딩 생성
    try:
        res = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
        q_emb = list(res.embeddings[0].values)
    except Exception as e:
        print(f"❌ ERROR: 임베딩 생성 중 오류: {e}")
        sys.exit(1)

    # LanceDB 벡터 검색
    try:
        db    = lancedb.connect(LANCE_DB_DIR)
        table = db.open_table("chunks")
        rows  = (table.search(q_emb)
                      .metric("cosine")
                      .limit(k * 3)  # 중복 제거 여유분
                      .select(["path", "text", "links", "tags", "_distance"])
                      .to_list())
    except Exception as e:
        print(f"❌ ERROR: LanceDB 검색 실패: {e}")
        sys.exit(1)

    # cosine distance → similarity 변환 (distance = 1 - similarity)
    # 임계값 0.15 (obsidian_agent.py와 동일)
    THRESHOLD = 1 - 0.15  # distance <= 0.85
    seen_paths = {}
    results = []
    for row in rows:
        dist  = row.get("_distance", 1.0)
        score = 1.0 - dist  # similarity
        if score < 0.15:
            continue
        path = row.get("path", "")
        # 같은 파일에서 가장 높은 점수 청크만 유지
        if path not in seen_paths or score > seen_paths[path]["score"]:
            try:
                links = json.loads(row.get("links", "[]"))
            except: links = []
            try:
                tags  = json.loads(row.get("tags", "[]"))
            except: tags = []
            seen_paths[path] = {
                "score":     score,
                "source":    os.path.basename(path),
                "full_path": path,
                "text":      row.get("text", ""),
                "links":     links,
                "tags":      tags,
            }

    results = sorted(seen_paths.values(), key=lambda x: x["score"], reverse=True)
    return results[:k]

# ==============================================================================
# [메인 실행부]
# ==============================================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python onew_search.py \"검색어\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"🔍 온유가 기억을 더듬는 중: '{query}'...")

    start_time = time.time()
    results    = search(query)
    elapsed    = time.time() - start_time

    if not results:
        print("\n💡 관련 내용을 찾지 못했습니다.")
    else:
        print(f"\n✅ {len(results)}개의 기억을 찾았습니다. ({elapsed:.2f}초)")
        print("=" * 70)
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] 출처: {r['source']} (유사도: {r['score']:.3f})")
            if r['tags']:
                print(f"    태그: {' '.join(['#'+t for t in r['tags']])}")
            if r['links']:
                print(f"    연결: {', '.join(r['links'][:3])}")
            clean_text = r['text'].replace('\n', ' ').strip()
            print(f"    내용: {clean_text[:350]}...")
        print("\n" + "=" * 70)
