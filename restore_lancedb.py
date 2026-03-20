"""
LanceDB 복구 스크립트
백업 JSON(onew_pure_db_MANUAL_20260318_113155.json) -> LanceDB 재마이그레이션
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json, os, numpy as np
import lancedb, pyarrow as pa

VAULT = r"C:\Users\User\Documents\Obsidian Vault"
BACKUP_JSON = r"C:\Users\User\AppData\Local\onew\db_backup\onew_pure_db_MANUAL_20260318_113155.json"
LANCE_DB_DIR = os.path.join(VAULT, "SYSTEM", ".onew_lance_db")
EMBED_DIM = 3072  # gemini-embedding-001 실제 출력 차원
CHUNK_VERSION = "v3"

def main():
    # 1. 백업 JSON 로드
    print(f"[1/4] 백업 JSON 로딩 중... ({os.path.getsize(BACKUP_JSON) // 1024 // 1024}MB)")
    with open(BACKUP_JSON, 'r', encoding='utf-8') as f:
        old_db = json.load(f)
    print(f"[1/4] JSON 로드 완료 - {len(old_db)}개 키")

    # 2. 청크 변환
    print("[2/4] 청크 변환 중...")
    rows = []
    meta = {}
    for path, data in old_db.items():
        if path == "__meta__":
            meta.update(data)
            continue
        hit_json = json.dumps(data.get("hit_log", []), ensure_ascii=False)
        for i, chunk in enumerate(data.get("chunks", [])):
            if "embedding" not in chunk:
                continue
            emb = chunk["embedding"]
            vec = emb.astype(np.float32).tolist() if isinstance(emb, np.ndarray) else [float(x) for x in emb]
            if len(vec) != EMBED_DIM:
                continue
            rows.append({
                "path": path, "chunk_idx": i,
                "text": chunk.get("text", ""),
                "vector": vec, "mtime": float(data.get("mtime", 0.0)),
                "links": json.dumps(chunk.get("links", []), ensure_ascii=False),
                "tags":  json.dumps(chunk.get("tags",  []), ensure_ascii=False),
                "importance": data.get("importance", "LOW"),
                "user_written": bool(data.get("user_written", True)),
                "hit_log": hit_json,
            })
    file_count = len(set(r["path"] for r in rows))
    print(f"[2/4] 변환 완료 - {len(rows)}개 청크, {file_count}개 파일")

    # 3. LanceDB 초기화 및 쓰기
    print("[3/4] LanceDB 쓰기 중...")
    db = lancedb.connect(LANCE_DB_DIR)

    schema = pa.schema([
        pa.field("path",         pa.string()),
        pa.field("chunk_idx",    pa.int32()),
        pa.field("text",         pa.string()),
        pa.field("vector",       pa.list_(pa.float32(), EMBED_DIM)),
        pa.field("mtime",        pa.float64()),
        pa.field("links",        pa.string()),
        pa.field("tags",         pa.string()),
        pa.field("importance",   pa.string()),
        pa.field("user_written", pa.bool_()),
        pa.field("hit_log",      pa.string()),
    ])
    tbl = db.create_table("chunks", schema=schema, mode="overwrite")

    # 배치로 나눠서 쓰기 (메모리 절약)
    BATCH = 5000
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        tbl.add(batch)
        print(f"  [{i+len(batch)}/{len(rows)}]", end="\r")
    print()

    # 4. 메타 저장 (chunk_version = v3 강제 설정)
    print("[4/4] 메타 저장 중...")
    meta["chunk_version"] = CHUNK_VERSION
    meta_rows = [{"key": k, "value": str(v)} for k, v in meta.items()]
    meta_schema = pa.schema([pa.field("key", pa.string()), pa.field("value", pa.string())])
    db.create_table("meta", schema=meta_schema, mode="overwrite").add(meta_rows)

    print(f"\n복구 완료!")
    print(f"  청크: {tbl.count_rows()}개")
    print(f"  chunk_version: {CHUNK_VERSION}")
    print(f"  last_sync: {meta.get('last_sync', '없음')}")

if __name__ == "__main__":
    main()
