import os
import glob
import json
import re
import math
import time
from datetime import datetime
import google.generativeai as genai

# ==============================================================================
# [설정 영역]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
DB_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_pure_db.json")
SYSTEM_PROMPT_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_시스템_초기화_프로토콜.md")
MAX_FILE_SIZE_KB = 50 
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    exit(1)
genai.configure(api_key=API_KEY)

# ==============================================================================
# [1. 스마트 기억 모듈]
# ==============================================================================
def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    return dot_product / (mag1 * mag2) if mag1 * mag2 != 0 else 0.0

class OnewPureMemory:
    def __init__(self):
        self.db = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f: self.db = json.load(f)

    def sync(self):
        print("🧠 온유(안전 모드)가 지식 네트워크를 스캔 중입니다...")
        md_files = glob.glob(os.path.join(OBSIDIAN_VAULT_PATH, "**/*.md"), recursive=True)
        updated = 0
        for f_path in md_files:
            if "onew_pure_db" in f_path or os.path.getsize(f_path) > MAX_FILE_SIZE_KB * 1024: continue
            mtime = os.path.getmtime(f_path)
            if f_path not in self.db or self.db[f_path].get("mtime", 0) < mtime:
                try:
                    with open(f_path, 'r', encoding='utf-8') as f: content = f.read()
                    links = list(set([l.split('|')[0] for l in re.findall(r'\[\[(.*?)\]\]', content)]))
                    tags = list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content)))
                    chunks = [content[i:i+800] for i in range(0, len(content), 700)]
                    file_data = {"mtime": mtime, "chunks": []}
                    print(f"🔄 분석 중: {os.path.basename(f_path)}", end="\r")
                    for c in chunks:
                        res = genai.embed_content(model="models/gemini-embedding-001", content=c, task_type="retrieval_document")
                        file_data["chunks"].append({"text": c, "embedding": res['embedding'], "links": links, "tags": tags})
                    self.db[f_path] = file_data
                    updated += 1
                except: continue
        if updated > 0:
            with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(self.db, f, ensure_ascii=False)
            print(f"\n💾 {updated}개의 파일 동기화 완료!")
        else: print("\n✨ 최신 상태입니다.")

    def search(self, query, k=4):
        q_emb = genai.embed_content(model="models/gemini-embedding-001", content=query, task_type="retrieval_query")['embedding']
        results = []
        for path, data in self.db.items():
            for c in data["chunks"]:
                results.append({"score": cosine_similarity(q_emb, c["embedding"]), "text": c["text"], "links": c["links"], "source": os.path.basename(path)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

# ==============================================================================
# [2. 온유 본체]
# ==============================================================================
class OnewAgent:
    def __init__(self):
        self.mem = OnewPureMemory()
        prompt = "당신은 고용준님의 외부 뇌 온유입니다."
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f: prompt = f.read()
        self.model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=prompt)
        self.chat = self.model.start_chat(history=[])

    def ask(self, query):
        print(f"\n온유(Onew) 🔗 탐색 중...")
        res = self.mem.search(query)
        ctx = "\n".join([f"[출처: {r['source']}] {r['text']}" for r in res])
        ans = self.chat.send_message(f"Context:\n{ctx}\n\n질문: {query}")
        print(f"==================================================\n💡 온유:\n{ans.text}\n==================================================")

if __name__ == "__main__":
    print("🌟 온유 가동 중...")
    onew = OnewAgent()
    onew.mem.sync()
    while True:
        q = input("\n💬 용준 님: ")
        if q.strip().lower() in ['끝', 'exit']: break
        if q.strip(): onew.ask(q)
