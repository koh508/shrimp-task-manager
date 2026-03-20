import os
import sys
import json
import math
import subprocess
import time
from pathlib import Path
from google import genai
from google.genai import types

# Windows 환경에서 한글 깨짐 방지
sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# [설정 - 엔진 v4.8과 경로 및 환경 동기화]
# ==============================================================================
current_script_path = Path(__file__).resolve()
if "Obsidian Vault" in str(current_script_path):
    ROOT_PATH = str(current_script_path.parents[2])
else:
    ROOT_PATH = r"C:\Users\User\Documents\DdidA"

OBSIDIAN_VAULT_PATH = os.path.join(ROOT_PATH, "Obsidian Vault")
SYSTEM_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")
DB_FILE = os.path.join(SYSTEM_PATH, "onew_pure_db.json")
TOP_K = 5

# ==============================================================================
# [초기화 및 유틸리티]
# ==============================================================================
def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"],
                capture_output=True, text=True, timeout=5)
            key = result.stdout.strip()
        except: pass
    return key

def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a * a for a in v1))
    m2 = math.sqrt(sum(b * b for b in v2))
    return dot / (m1 * m2) if m1 * m2 != 0 else 0.0

# ==============================================================================
# [핵심 검색 로직]
# ==============================================================================
def search(query, k=TOP_K):
    api_key = get_api_key()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY를 찾을 수 없습니다.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if not os.path.exists(DB_FILE):
        print(f"❌ ERROR: DB 파일이 없습니다 -> {DB_FILE}\n먼저 'obsidian_agent.py sync'를 실행해 주세요.")
        sys.exit(1)

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # 쿼리 임베딩 생성
    try:
        res = client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
        q_emb = res.embeddings[0].values
    except Exception as e:
        print(f"❌ ERROR: 임베딩 생성 중 오류 발생: {e}")
        sys.exit(1)

    results = []
    for path, data in db.items():
        # 메타데이터 키는 건너뜀
        if path == "__meta__":
            continue
            
        for chunk in data.get("chunks", []):
            if "embedding" not in chunk:
                continue
                
            score = cosine_similarity(q_emb, chunk["embedding"])
            # 검색 품질 유지를 위한 임계값 (엔진 v4.8과 동일하게 0.3 설정)
            if score >= 0.3:
                results.append({
                    "score": score,
                    "source": os.path.basename(path),
                    "full_path": path,
                    "text": chunk["text"],
                    "links": chunk.get("links", []),
                    "tags": chunk.get("tags", [])
                })

    # 유사도 순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
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
    results = search(query)
    elapsed_time = time.time() - start_time

    if not results:
        print("\n💡 관련 내용을 찾지 못했습니다.")
    else:
        print(f"\n✅ {len(results)}개의 기억을 찾았습니다. ({elapsed_time:.2f}초)")
        print("=" * 70)
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] 출처: {r['source']} (유사도: {r['score']:.3f})")
            if r['tags']:
                print(f"    태그: {' '.join(['#'+t for t in r['tags']])}")
            if r['links']:
                print(f"    연결: {', '.join(r['links'][:3])}")
            
            # 내용을 깔끔하게 출력
            clean_text = r['text'].replace('\n', ' ').strip()
            print(f"    내용: {clean_text[:350]}...")
        print("\n" + "=" * 70)