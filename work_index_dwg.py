"""
work_index_dwg.py
DWG 도면 메타데이터 인덱싱 → drawing_index.json 생성

전략: DWG → 이미지 변환 ❌ (비용 폭발)
     파일명 파싱만으로 설비/라인번호 인덱싱 ✅ (API 0원)

출력:
  SYSTEM/work_index/drawing_index.json  (list of records)

실행: python work_index_dwg.py [--company 36] [--force]
"""

import os
import re
import json
import argparse
import logging
import tempfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── 경로 ─────────────────────────────────────────────────────────────
VAULT_DIR     = r"C:\Users\User\Documents\Obsidian Vault"
WORK_INDEX    = os.path.join(VAULT_DIR, "SYSTEM", "work_index")
MANIFEST_FILE = os.path.join(WORK_INDEX, "file_manifest.json")
OUTPUT_FILE   = os.path.join(WORK_INDEX, "drawing_index.json")

# ── 설비 패턴 (work_build_equipment_md.py EQUIP_IN_PARAM와 동기화) ──
EQUIP_PATTERNS = [
    ("절탄기",    re.compile(r"절탄기|economizer|economi[sz]er", re.IGNORECASE)),
    ("과열기",    re.compile(r"과열기|superheater|sh[-_\s]?\d", re.IGNORECASE)),
    ("재열기",    re.compile(r"재열기|reheater|rh[-_\s]?\d", re.IGNORECASE)),
    ("폐열보일러", re.compile(r"폐열보일러|hrsg|waste.?heat", re.IGNORECASE)),
    ("버너",      re.compile(r"버너|burner", re.IGNORECASE)),
    ("증기드럼",  re.compile(r"증기드럼|steam.?drum", re.IGNORECASE)),
    ("펌프",      re.compile(r"펌프|\bpump\b", re.IGNORECASE)),
    ("팬",        re.compile(r"\bfan\b|\bblower\b", re.IGNORECASE)),
    ("밸브",      re.compile(r"밸브|\bvalve\b", re.IGNORECASE)),
    ("압축기",    re.compile(r"압축기|compressor", re.IGNORECASE)),
    ("탱크",      re.compile(r"탱크|\btank\b", re.IGNORECASE)),
    ("필터",      re.compile(r"필터|\bfilter\b", re.IGNORECASE)),
    ("화격자",    re.compile(r"화격자|grate|furnace", re.IGNORECASE)),
]

# 라인번호 패턴: "GAS-101", "STM-2301", "CW-012" 등
LINE_PAT = re.compile(r"[A-Z]{2,5}-\d{2,4}")


def detect_equipment(name: str) -> str | None:
    for eq_name, pat in EQUIP_PATTERNS:
        if pat.search(name):
            return eq_name
    return None


def detect_line(name: str) -> str | None:
    m = LINE_PAT.search(name)
    return m.group(0) if m else None


def load_manifest() -> list[dict]:
    with open(MANIFEST_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_index(manifest: list[dict], company_filter: str | None, force: bool) -> list[dict]:
    # 기존 인덱스 로드 (증분 업데이트용)
    existing: dict[str, dict] = {}
    if os.path.exists(OUTPUT_FILE) and not force:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for rec in json.load(f):
                existing[rec["path"]] = rec

    targets = [
        e for e in manifest
        if e.get("file_ext", "").upper() == "DWG"
        and not Path(e["abs_path"]).name.startswith("~$")
        and (company_filter is None or e.get("company_id") == company_filter)
    ]

    log.info(f"DWG 대상: {len(targets)}개")

    index = []
    new_cnt = skip_cnt = 0

    for e in targets:
        path = e["abs_path"]

        if path in existing and not force:
            index.append(existing[path])
            skip_cnt += 1
            continue

        fname = Path(path).name
        record = {
            "file":         fname,
            "path":         path,
            "company_id":   e.get("company_id"),
            "company_name": e.get("company_name"),
            "doc_type":     e.get("doc_type"),
            "rev":          e.get("rev"),
            "equipment":    detect_equipment(fname),
            "line":         detect_line(fname),
            "indexed_at":   datetime.now().strftime("%Y-%m-%d"),
        }
        index.append(record)
        new_cnt += 1

    log.info(f"신규: {new_cnt}개 / 스킵(기존): {skip_cnt}개")
    return index


def save_index(index: list[dict]) -> None:
    """Atomic write: tmp → os.replace"""
    os.makedirs(WORK_INDEX, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=WORK_INDEX, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, OUTPUT_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="DWG 도면 인덱서")
    parser.add_argument("--company", help="업체 ID 필터 (예: 36)")
    parser.add_argument("--force", action="store_true", help="기존 인덱스 무시 후 전체 재생성")
    args = parser.parse_args()

    manifest = load_manifest()
    index = build_index(manifest, args.company, args.force)
    save_index(index)

    equip_cnt = sum(1 for r in index if r["equipment"])
    line_cnt  = sum(1 for r in index if r["line"])
    log.info(f"총 {len(index)}개 → 설비 태그: {equip_cnt}개 / 라인번호: {line_cnt}개")
    log.info(f"저장: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
