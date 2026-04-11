"""
work_make_manifest.py
D:\기계도면\기계도면\ 전체 스캔 → file_manifest.json + equipment_resolver.json + _전체인덱스.md

출력 파일:
  SYSTEM/work_index/file_manifest.json       — 전체 파일 목록 (라우팅 엔진)
  SYSTEM/work_index/equipment_resolver.json  — 설비명 → 파일 경로 역인덱스
  SYSTEM/work_index/rev_conflicts.json       — Rev 충돌 감지 목록
  업무자료/준공도서/_전체인덱스.md            — 사람이 읽는 Obsidian 인덱스

API 비용: 0원 (파일시스템 스캔만)
"""

import os
import re
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────
SOURCE_DIR   = r"D:\기계도면\기계도면"
VAULT_DIR    = r"C:\Users\User\Documents\Obsidian Vault"
WORK_INDEX   = os.path.join(VAULT_DIR, "SYSTEM", "work_index")
OUTPUT_MD    = os.path.join(VAULT_DIR, "업무자료", "준공도서", "_전체인덱스.md")

MANIFEST_FILE  = os.path.join(WORK_INDEX, "file_manifest.json")
RESOLVER_FILE  = os.path.join(WORK_INDEX, "equipment_resolver.json")
CONFLICTS_FILE = os.path.join(WORK_INDEX, "rev_conflicts.json")

os.makedirs(WORK_INDEX, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)

# ──────────────────────────────────────────────
# 처리 대상 확장자
# ──────────────────────────────────────────────
TARGET_EXTS = {".pdf", ".xlsx", ".xls", ".hwp", ".dwg", ".DWG",
               ".doc", ".docx", ".pptx", ".csv"}

# ──────────────────────────────────────────────
# 폴더명 → 문서 유형 매핑
# ──────────────────────────────────────────────
FOLDER_CATEGORY_MAP = [
    (r"(?i)data.?sheet|데이터.?시트|6\.\s*data",          "DATA_SHEET"),
    (r"(?i)line.?list|라인리스트|piping.?info|18\.",       "LINELIST"),
    (r"(?i)설계.?계산|design.?calc|calculation|5\.",       "CALCULATION"),
    (r"(?i)운전.*지침|operation.*manual|O&M|16\.",         "MANUAL"),
    (r"(?i)p&id|p\.and\.i|p-&-i",                         "PID"),
    (r"(?i)instrument.?list|계장.*목록|12\.",              "INSTRUMENT_LIST"),
    (r"(?i)7\.\s*도면|drawing.*list|도면.*목차|1\.\s*도면", "DRAWING_INDEX"),
    (r"(?i)시방서|specification|4\.",                      "SPEC"),
    (r"(?i)용접.*절차|welding.*proc|9\.",                  "WELDING"),
    (r"(?i)시험.*검사|inspection|test.*proc|10\.",         "INSPECTION"),
    (r"(?i)예비품|spare.*part|14\.",                       "SPARE_PARTS"),
    (r"(?i)성능.*곡선|performance.*curve",                 "PERFORMANCE_CURVE"),
    (r"(?i)sub.?vendor|서브벤더|17\.",                     "VENDOR_LIST"),
    (r"(?i)보온.*도장|insulation|8\.",                     "INSULATION"),
    (r"(?i)구성.*기기|component.*list|11\.",               "COMPONENT_LIST"),
    (r"(?i)\.dwg$|dwg|도면",                               "DRAWING_DWG"),
]

def classify_folder(path_parts: list[str]) -> str:
    """폴더 경로 구성 요소에서 문서 유형 판별"""
    search_text = " / ".join(path_parts)
    for pattern, category in FOLDER_CATEGORY_MAP:
        if re.search(pattern, search_text):
            return category
    return "OTHER"

# ──────────────────────────────────────────────
# 설비명 정규화 테이블
# ──────────────────────────────────────────────
EQUIPMENT_PATTERNS = [
    # (정규식 패턴, 표준 설비명)
    (r"(?i)economizer|economiser|이코노마이저|절탄기|econ\b|e\.c\b",       "절탄기"),
    (r"(?i)superheater|과열기|sh\b|s\.h\b|super.heat",                    "과열기"),
    (r"(?i)hrsg|waste.heat.boiler|배열보일러|폐열보일러|폐열회수",          "폐열보일러"),
    (r"(?i)steam.drum|증기드럼|s\.d\b|sd\b",                              "증기드럼"),
    (r"(?i)burner|버너|점화",                                              "버너"),
    (r"(?i)incinerator|소각로|소각설비|연소로",                            "소각로"),
    (r"(?i)fan|송풍기|blower|ID.fan|FD.fan|PA.fan|SA.fan",                "송풍기"),
    (r"(?i)pump|펌프|pump",                                                "펌프"),
    (r"(?i)heat.exchanger|열교환기|cooler|쿨러|hx\b",                     "열교환기"),
    (r"(?i)compressor|압축기|comp\b",                                      "압축기"),
    (r"(?i)scrubber|스크러버|세정기",                                      "스크러버"),
    (r"(?i)cyclone|사이클론",                                              "사이클론"),
    (r"(?i)bag.filter|백필터|여과집진|집진기",                             "집진기"),
    (r"(?i)cooling.tower|냉각탑|c\.t\b|ct\b",                             "냉각탑"),
    (r"(?i)chiller|냉동기|칠러",                                           "냉동기"),
    (r"(?i)air.handling|공기조화기|ahu\b|a\.h\.u",                        "공기조화기"),
    (r"(?i)boiler(?!.*waste|.*heat|.*hrsg)|보일러(?!.*폐열|.*배열)",       "보일러"),
    (r"(?i)계량대|weigher|weigh",                                          "계량대"),
    (r"(?i)소석회|lime|slaker|슬러리",                                    "소석회설비"),
    (r"(?i)순수.*제조|pure.water|탈염|dem\b",                             "순수제조설비"),
    (r"(?i)악취.*제거|odor|탈취",                                          "악취제거설비"),
    (r"(?i)hydraul|유압",                                                  "유압설비"),
    (r"(?i)control|자동.*제어|plc|dcs|instrumentation",                   "자동제어"),
    (r"(?i)화격자|grate|stoker",                                           "화격자"),
    (r"(?i)댐퍼|damper",                                                   "댐퍼"),
    (r"(?i)세차|car.wash",                                                 "세차설비"),
    (r"(?i)소방.*펌프|fire.pump",                                          "소방펌프"),
    (r"(?i)빗물.*저류|rainwater|우수",                                    "빗물저류조"),
    (r"(?i)비산재|fly.ash|비산",                                           "비산재처리"),
    (r"(?i)바닥재|bottom.ash",                                             "바닥재처리"),
    (r"(?i)반입.*공급|feeding|투입",                                       "반입공급설비"),
    (r"(?i)심정|deep.well|지하수",                                         "심정펌프"),
    (r"(?i)보조.*보일러|aux.*boiler",                                      "보조보일러"),
    (r"(?i)내화물|refractory|내화",                                        "내화물"),
    (r"(?i)실험실|lab|laboratory",                                         "실험실설비"),
    (r"(?i)배관.*덕트|pipe.*duct|duct.*pipe",                              "배관덕트"),
    (r"(?i)연소.*가스.*처리|flue.gas|배가스",                              "연소가스처리"),
]

def detect_equipment(text: str) -> str:
    """파일명 + 폴더명 조합 텍스트에서 설비명 탐지"""
    for pattern, name in EQUIPMENT_PATTERNS:
        if re.search(pattern, text):
            return name
    return "기타"

# ──────────────────────────────────────────────
# Rev 번호 추출
# ──────────────────────────────────────────────
REV_PATTERNS = [
    r"[Rr]ev\.?\s*(\d+)",
    r"[-_][Rr](\d+)(?:\b|_)",
    r"[-_][Rr][eE][vV]\.?(\d+)",
    r"[Rr](\d+)(?:[-_\.\s]|$)",
    r"\brev\.?\s*(\d+)\b",
]

def extract_rev(text: str) -> str | None:
    for pat in REV_PATTERNS:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    if re.search(r"(?i)as.?built|준공", text):
        return "AS_BUILT"
    return None

def rev_sort_key(rev: str | None) -> int:
    """Rev 번호 비교용 정수 변환 (AS_BUILT = 9999)"""
    if rev is None:
        return -1
    if rev == "AS_BUILT":
        return 9999
    try:
        return int(rev)
    except ValueError:
        return 0

# ──────────────────────────────────────────────
# SHA256 해시 (앞 64KB만 — 속도 균형)
# ──────────────────────────────────────────────
def file_hash(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            h.update(f.read(65536))
        return h.hexdigest()[:16]
    except Exception:
        return "error"

# ──────────────────────────────────────────────
# 업체 파싱 (폴더명: "36. 폐열보일러 (조선내화E)")
# ──────────────────────────────────────────────
def parse_company(folder_name: str) -> tuple[str, str]:
    """(company_id, company_name)"""
    m = re.match(r"^(\d+)\.\s*(.+?)(?:\s*\(.+\))?$", folder_name)
    if m:
        return m.group(1).zfill(2), m.group(2).strip()
    return "00", folder_name

# ──────────────────────────────────────────────
# 메인 스캔
# ──────────────────────────────────────────────
def scan(source_dir: str) -> list[dict]:
    records = []
    total = 0
    skipped = 0

    print(f"\n📂 스캔 시작: {source_dir}")

    for root, dirs, files in os.walk(source_dir):
        # 불필요 폴더 제외
        dirs[:] = [d for d in sorted(dirs) if not d.startswith(".")]

        rel_root = os.path.relpath(root, source_dir)
        parts    = rel_root.replace("\\", "/").split("/")

        # 업체 정보 (최상위 폴더)
        top_folder = parts[0] if parts and parts[0] != "." else ""
        company_id, company_name = parse_company(top_folder)

        # 폴더 카테고리
        doc_type = classify_folder(parts)

        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext not in TARGET_EXTS and Path(fname).suffix not in TARGET_EXTS:
                skipped += 1
                continue

            fpath = os.path.join(root, fname)
            total += 1

            # 설비명 탐지 (파일명 + 폴더명 전체 사용)
            detect_text = fname + " " + " ".join(parts)
            equipment = detect_equipment(detect_text)

            # Rev 추출 (파일명 우선, 폴더명 폴백)
            rev = extract_rev(fname) or extract_rev(rel_root)

            # AS_BUILT 판단
            is_as_built = bool(re.search(r"(?i)as.?built|준공", fname + rel_root))

            try:
                stat = os.stat(fpath)
                fsize  = stat.st_size
                fmtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            except Exception:
                fsize, fmtime = 0, "unknown"

            record = {
                "company_id":   company_id,
                "company_name": company_name,
                "equipment":    equipment,
                "doc_type":     doc_type,
                "file_name":    fname,
                "file_ext":     ext.lstrip(".").upper(),
                "rev":          rev,
                "is_as_built":  is_as_built,
                "is_latest":    None,           # 후처리에서 결정
                "size_kb":      round(fsize / 1024, 1),
                "mtime":        fmtime,
                "hash":         file_hash(fpath),
                "abs_path":     fpath,
                "rel_path":     os.path.join(rel_root, fname),
            }
            records.append(record)

        if total % 500 == 0 and total > 0:
            print(f"  ... {total}개 처리 중")

    print(f"  ✅ 완료: {total}개 처리 / {skipped}개 건너뜀")
    return records

# ──────────────────────────────────────────────
# Rev 최신 판별 (같은 company + equipment + doc_type 그룹 내)
# ──────────────────────────────────────────────
def resolve_latest(records: list[dict]) -> list[dict]:
    """동일 그룹(업체+설비+문서유형+파일명_베이스) 내 최신 Rev 판별"""

    def base_name(fname):
        # Rev 번호 제거한 베이스 파일명
        cleaned = re.sub(r"[-_\s]*[Rr]ev\.?\s*\d+", "", fname, flags=re.IGNORECASE)
        cleaned = re.sub(r"[-_\s]*[Rr]\d+(?=[-_\.\s]|$)", "", cleaned)
        return re.sub(r"[-_\s]+$", "", Path(cleaned).stem).lower()

    # 그룹별 묶기
    groups: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(records):
        key = (r["company_id"], r["equipment"], r["doc_type"],
               base_name(r["file_name"]), r["file_ext"])
        groups[key].append(i)

    conflicts = []
    for key, idxs in groups.items():
        if len(idxs) == 1:
            records[idxs[0]]["is_latest"] = True
            continue

        # Rev 정렬
        idxs_sorted = sorted(idxs, key=lambda i: rev_sort_key(records[i]["rev"]))
        latest_idx  = idxs_sorted[-1]

        for i in idxs_sorted[:-1]:
            records[i]["is_latest"] = False
        records[latest_idx]["is_latest"] = True

        # AS_BUILT가 있으면 AS_BUILT 우선
        as_built = [i for i in idxs if records[i]["is_as_built"]]
        if as_built:
            for i in idxs:
                records[i]["is_latest"] = False
            records[as_built[-1]]["is_latest"] = True

        # 충돌 기록 (Rev이 다른 경우만)
        revs = set(records[i]["rev"] for i in idxs)
        if len(revs) > 1:
            conflicts.append({
                "key":   str(key),
                "files": [records[i]["file_name"] for i in idxs],
                "revs":  [records[i]["rev"] for i in idxs],
                "latest": records[latest_idx]["file_name"],
            })

    return records, conflicts

# ──────────────────────────────────────────────
# Equipment Resolver 인덱스 생성
# (설비명 → 최신 파일 경로 목록)
# ──────────────────────────────────────────────
def build_resolver(records: list[dict]) -> dict:
    resolver: dict[str, list] = defaultdict(list)
    for r in records:
        if not r.get("is_latest", True):
            continue
        key = r["equipment"]
        resolver[key].append({
            "abs_path":   r["abs_path"],
            "doc_type":   r["doc_type"],
            "company_id": r["company_id"],
            "file_name":  r["file_name"],
            "rev":        r["rev"],
        })
    return dict(resolver)

# ──────────────────────────────────────────────
# Obsidian MD 인덱스 생성
# ──────────────────────────────────────────────
def write_md_index(records: list[dict], conflicts: list[dict]):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(records)
    latest_count = sum(1 for r in records if r.get("is_latest"))

    # 업체별 그룹
    by_company: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_company[f"{r['company_id']}_{r['company_name']}"].append(r)

    lines = [
        "---",
        "tags: [업무자료, 준공도서, 인덱스, 자동생성]",
        f"날짜: {today[:10]}",
        "auto_generated: true",
        "---",
        "",
        f"# 준공도서 전체 인덱스",
        f"> 자동생성: {today} | 총 {total}개 파일 | 최신 Rev: {latest_count}개",
        "",
        "## 통계",
        "",
    ]

    # 확장자 통계
    ext_counts: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    for r in records:
        ext_counts[r["file_ext"]] += 1
        type_counts[r["doc_type"]] += 1

    lines.append("| 파일 유형 | 개수 |")
    lines.append("|----------|------|")
    for ext, cnt in sorted(ext_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| .{ext.lower()} | {cnt} |")
    lines.append("")
    lines.append("| 문서 유형 | 개수 |")
    lines.append("|----------|------|")
    for dt, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {dt} | {cnt} |")
    lines.append("")

    # Rev 충돌
    if conflicts:
        lines += [
            f"## ⚠️ Rev 충돌 ({len(conflicts)}건)",
            "",
            "| 업체+설비 | 충돌 파일 | 최신 판정 |",
            "|----------|-----------|-----------|",
        ]
        for c in conflicts[:30]:  # 최대 30개
            files_str = " / ".join(c["files"][:3])
            lines.append(f"| {c['key'][:40]} | {files_str[:50]} | {c['latest']} |")
        lines.append("")

    # 업체별 목록
    lines.append("## 업체별 파일 목록")
    lines.append("")
    for company_key in sorted(by_company.keys()):
        company_records = by_company[company_key]
        company_name = company_records[0]["company_name"]
        lines.append(f"### {company_key.replace('_', '. ', 1)}")
        lines.append("")
        lines.append("| 설비 | 문서유형 | 파일명 | Rev | 크기 |")
        lines.append("|------|---------|--------|-----|------|")

        latest_only = [r for r in company_records if r.get("is_latest", True)]
        for r in sorted(latest_only, key=lambda x: (x["equipment"], x["doc_type"])):
            rev_str = r["rev"] or "-"
            fname_short = r["file_name"][:40]
            lines.append(
                f"| {r['equipment']} | {r['doc_type']} | {fname_short} | {rev_str} | {r['size_kb']}KB |"
            )
        lines.append("")

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📝 MD 인덱스: {OUTPUT_MD}")

# ──────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if not os.path.isdir(SOURCE_DIR):
        print(f"❌ 소스 디렉토리 없음: {SOURCE_DIR}")
        return

    start = datetime.now()

    # 1. 전체 스캔
    records = scan(SOURCE_DIR)

    # 2. Rev 최신 판별 + 충돌 감지
    print("🔍 Rev 충돌 분석 중...")
    records, conflicts = resolve_latest(records)
    print(f"  충돌 감지: {len(conflicts)}건")

    # 3. Equipment Resolver 인덱스
    resolver = build_resolver(records)
    equip_types = sorted(resolver.keys())
    print(f"  설비 유형: {len(equip_types)}종 — {', '.join(equip_types[:10])}{'...' if len(equip_types) > 10 else ''}")

    # 4. JSON 저장
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"💾 매니페스트: {MANIFEST_FILE} ({len(records)}개)")

    with open(RESOLVER_FILE, "w", encoding="utf-8") as f:
        json.dump(resolver, f, ensure_ascii=False, indent=2)
    print(f"💾 Equipment Resolver: {RESOLVER_FILE}")

    with open(CONFLICTS_FILE, "w", encoding="utf-8") as f:
        json.dump(conflicts, f, ensure_ascii=False, indent=2)
    print(f"💾 Rev 충돌 목록: {CONFLICTS_FILE} ({len(conflicts)}건)")

    # 5. MD 인덱스
    print("📝 Obsidian 인덱스 생성 중...")
    write_md_index(records, conflicts)

    elapsed = (datetime.now() - start).seconds
    print(f"\n✅ 완료 ({elapsed}초)")
    print(f"   총 파일: {len(records)}개")
    print(f"   최신 Rev: {sum(1 for r in records if r.get('is_latest'))}개")
    print(f"   Rev 충돌: {len(conflicts)}건")
    print(f"\n다음 단계: work_extract_xlsx.py 실행")

if __name__ == "__main__":
    main()
