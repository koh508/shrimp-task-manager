"""
work_build_equipment_md.py
work_extracted/ JSON 데이터 → 설비별 MD 자동 생성 (Layer 3)

출력:
  업무자료/준공도서/설비별/{설비명}.md   — 온유 RAG 검색 대상
  SYSTEM/work_index/equipment_db.json   — 설비별 수치 통합 DB

API 비용: 0원
실행: python work_build_equipment_md.py [--equipment 절탄기] [--force]
"""

import os
import re
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────
VAULT_DIR    = r"C:\Users\User\Documents\Obsidian Vault"
WORK_INDEX   = os.path.join(VAULT_DIR, "SYSTEM", "work_index")
EXTRACT_BASE = os.path.join(WORK_INDEX, "work_extracted")
MANIFEST_FILE = os.path.join(WORK_INDEX, "file_manifest.json")

OUT_MD_DIR   = os.path.join(VAULT_DIR, "업무자료", "준공도서", "설비별")
OUT_DB       = os.path.join(WORK_INDEX, "equipment_db.json")

os.makedirs(OUT_MD_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# 파라미터 정규화 — 동의어 → 표준명
# ──────────────────────────────────────────────
PARAM_GROUPS = {
    "입구온도": re.compile(
        r"(?i)(inlet|in\.?\s*|입구|입\s*구).*(temp|온도)|"
        r"(temp|온도).*(inlet|입구)|gas\s*in.*temp|연소가스.*입구.*온도"
    ),
    "출구온도": re.compile(
        r"(?i)(outlet|out\.?\s*|출구|출\s*구).*(temp|온도)|"
        r"(temp|온도).*(outlet|출구)|절탄기\s*출구온도"
    ),
    "입구압력": re.compile(
        r"(?i)(inlet|in\.?\s*|입구).*(press|압력)|"
        r"(press|압력).*(inlet|입구)"
    ),
    "출구압력": re.compile(
        r"(?i)(outlet|out\.?\s*|출구).*(press|압력)|"
        r"(press|압력).*(outlet|출구)"
    ),
    "정상운전온도": re.compile(r"(?i)온도_정상|oper.*temp|normal.*temp|정상.*온도"),
    "설계온도":     re.compile(r"(?i)온도_설계|design.*temp|설계.*온도"),
    "정상운전압력": re.compile(r"(?i)압력_정상|oper.*press|normal.*press|정상.*압력"),
    "설계압력":     re.compile(r"(?i)압력_설계|design.*press|설계.*압력"),
    "유량":         re.compile(r"(?i)유량|flow\s*rate?"),
    "용량":         re.compile(r"(?i)capacity|용량|처리량"),
    "동력":         re.compile(r"(?i)power|동력|출력|\bkw\b"),
    "효율":         re.compile(r"(?i)efficiency|효율"),
    "회전수":       re.compile(r"(?i)rpm|speed|회전"),
}

def classify_param(param_text: str) -> str:
    """파라미터명을 표준 그룹명으로 분류, 미해당이면 원본 반환"""
    for group_name, pat in PARAM_GROUPS.items():
        if pat.search(param_text):
            return group_name
    return param_text


# ──────────────────────────────────────────────
# 추출 JSON 로드
# ──────────────────────────────────────────────

def load_company_map() -> dict[str, str]:
    """manifest에서 company_id → company_name 매핑 로드"""
    try:
        manifest = json.load(open(MANIFEST_FILE, encoding="utf-8"))
        return {e["company_id"]: e.get("company_name", e["company_id"])
                for e in manifest if "company_id" in e}
    except Exception:
        return {}

def load_all_records() -> list[dict]:
    """work_extracted/ 하위 모든 JSON에서 레코드 수집"""
    company_map = load_company_map()
    all_records = []
    for subdir in ["linelist", "datasheet"]:
        dpath = os.path.join(EXTRACT_BASE, subdir)
        if not os.path.isdir(dpath):
            continue
        for fname in os.listdir(dpath):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(dpath, fname)
            try:
                data = json.load(open(fpath, encoding="utf-8"))
            except Exception as e:
                log.warning("로드 실패 %s: %s", fname, e)
                continue
            meta = data.get("meta", {})
            cid  = str(meta.get("company_id", ""))
            for r in data.get("records", []):
                r["_company_id"]   = cid
                r["_company_name"] = company_map.get(cid, cid)
                r["_doc_type"]     = meta.get("doc_type", subdir.upper())
                r["_source_file"]  = Path(meta.get("source_path", fname)).name
                r["_source_stem"]  = Path(meta.get("source_path", fname)).stem
                r["_rev"]          = meta.get("rev", "")
                r["_is_latest"]    = meta.get("is_latest", True)
                all_records.append(r)
    log.info("전체 레코드 로드: %d건", len(all_records))
    return all_records


# ──────────────────────────────────────────────
# 설비별 데이터 집계
# ──────────────────────────────────────────────

# 설비명 추가 패턴 — 파라미터명에서 설비 재추출용
EQUIP_IN_PARAM = [
    ("절탄기",   re.compile(r"절탄기|economizer|economi[sz]er", re.IGNORECASE)),
    ("과열기",   re.compile(r"과열기|superheater|\bsh[-\s]?\d", re.IGNORECASE)),
    ("재열기",   re.compile(r"재열기|reheater|\brh[-\s]?\d", re.IGNORECASE)),
    ("폐열보일러", re.compile(r"폐열보일러|hrsg|waste.?heat", re.IGNORECASE)),
    ("버너",     re.compile(r"버너|burner", re.IGNORECASE)),
    ("증기드럼", re.compile(r"증기드럼|steam.?drum", re.IGNORECASE)),
    ("펌프",     re.compile(r"펌프|\bpump\b", re.IGNORECASE)),
    ("팬",       re.compile(r"\bfan\b|\bblower\b", re.IGNORECASE)),
]

def resolve_equipment(r: dict) -> str:
    """
    1순위: 파라미터명에서 설비명 추출
    2순위: equipment 필드
    3순위: "기타"
    """
    param = r.get("parameter", "")
    for eq_name, pat in EQUIP_IN_PARAM:
        if pat.search(param):
            return eq_name
    return r.get("equipment") or "기타"


def aggregate_by_equipment(records: list[dict]) -> dict[str, list[dict]]:
    """
    equipment 필드 + 파라미터명 재추출로 레코드 그룹화
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        eq = resolve_equipment(r)
        grouped[eq].append(r)
    return dict(grouped)


def build_equipment_summary(eq_name: str, records: list[dict]) -> dict:
    """
    설비 1개의 레코드 목록 → 파라미터별 대표값 선정
    우선순위: is_latest=True > LINELIST > DATA_SHEET > source(table > kv_text)
    """
    # 최신 Rev만 우선
    latest = [r for r in records if r.get("_is_latest", True)]
    if not latest:
        latest = records

    # 파라미터 그룹별 집계
    # DATASHEET: parameter는 행번호(숫자), 실제 파라미터명은 design_value
    # LINELIST:  parameter가 실제 파라미터명 ("압력_정상", "온도_정상" 등)
    param_map: dict[str, list[dict]] = defaultdict(list)
    for r in latest:
        dv = r.get("design_value", "")
        param_label = dv if dv else r.get("parameter", "")
        group = classify_param(param_label)
        r["_param_label"] = param_label  # MD 출력용
        param_map[group].append(r)

    # 그룹별 대표값 선정 (중복 제거 + 값 정렬)
    summary: list[dict] = []
    seen_groups = set()

    for group, recs in param_map.items():
        # LINELIST 우선
        ll_recs = [r for r in recs if r.get("_doc_type") == "LINELIST"]
        best_recs = ll_recs if ll_recs else recs

        # 값별 중복 제거 — 동일 (값+단위+출처) 만 제거, 다른 출처의 다른 값은 모두 보존
        seen_vals = set()
        for r in best_recs:
            val_key = (r.get("value", ""), r.get("unit", ""), r.get("_source_file", ""))
            if val_key in seen_vals:
                continue
            seen_vals.add(val_key)
            summary.append({
                "param_group":   group,
                "parameter":     r.get("_param_label") or r.get("parameter", ""),
                "value":         r.get("value", ""),
                "unit":          r.get("unit", ""),
                "doc_type":      r.get("_doc_type", ""),
                "company_name":  r.get("_company_name", ""),
                "source_file":   r.get("_source_file", ""),
                "source_stem":   r.get("_source_stem", ""),
                "rev":           r.get("_rev", ""),
                "page":          r.get("page", ""),
            })

    # 파라미터 그룹 정렬 (중요도 순)
    priority = list(PARAM_GROUPS.keys())
    summary.sort(key=lambda x: priority.index(x["param_group"])
                 if x["param_group"] in priority else 999)

    return {
        "equipment":    eq_name,
        "record_count": len(records),
        "param_count":  len(param_map),
        "params":       summary,
    }


# ──────────────────────────────────────────────
# MD 생성
# ──────────────────────────────────────────────

SECTION_MAP = {
    "온도": ["입구온도", "출구온도", "정상운전온도", "설계온도"],
    "압력": ["입구압력", "출구압력", "정상운전압력", "설계압력"],
    "유량": ["유량"],
    "성능": ["용량", "동력", "효율", "회전수"],
}
SECTION_ICONS = {"온도": "🌡️", "압력": "⚡", "유량": "💧", "성능": "⚙️"}

def build_md(summary: dict) -> str:
    eq   = summary["equipment"]
    now  = datetime.now().strftime("%Y-%m-%d")
    params = summary["params"]

    # 출처 파일 목록 (중복 제거)
    sources = list({p["source_stem"]: p for p in params if p.get("source_stem")}.values())
    companies = list({p["company_name"] for p in params if p.get("company_name")})

    lines = [
        "---",
        f"tags: [업무자료, 준공도서, 설비별, {eq}]",
        f"설비: {eq}",
        f"날짜: {now}",
        f"레코드수: {summary['record_count']}",
        "author: work_build_equipment_md",
        "---",
        "",
        f"# {eq}",
        "",
        "## 🔧 요약",
        f"- 업체: {', '.join(companies) if companies else '미상'}",
        f"- 데이터 파일: {len(sources)}개",
        f"- 파라미터 종류: {summary['param_count']}개",
        "",
        "---",
    ]

    # ── 섹션별 출력
    handled_groups = set()
    for section, group_list in SECTION_MAP.items():
        icon = SECTION_ICONS.get(section, "")
        section_params = [p for p in params if p["param_group"] in group_list]
        if not section_params:
            continue

        lines += ["", f"## {icon} {section}", ""]
        for group in group_list:
            grp_params = [p for p in section_params if p["param_group"] == group]
            if not grp_params:
                continue
            lines.append(f"### {group}")
            for p in grp_params:
                val  = p["value"] or "-"
                unit = p["unit"]  or ""
                val_str = f"{val} {unit}".strip()
                co   = p.get("company_name", "")
                doc  = p.get("doc_type", "")
                rev  = p.get("rev", "")
                src  = p.get("source_stem", "")
                rev_str = f" Rev.{rev}" if rev else ""
                co_str  = f"{co} / " if co else ""
                lines.append(f"- **{val_str}** ({co_str}{doc}{rev_str})")
                if src:
                    lines.append(f"  - 출처: [[{src}]]")
            handled_groups.update(group_list)
            lines.append("")

    # ── 기타 파라미터 (섹션 미분류)
    other_params = [p for p in params if p["param_group"] not in handled_groups]
    if other_params:
        lines += ["## 📋 기타 수치", ""]
        seen = set()
        for p in other_params[:60]:
            key = (p["param_group"], p["value"], p.get("source_stem", ""))
            if key in seen:
                continue
            seen.add(key)
            val  = p["value"] or "-"
            unit = p["unit"]  or ""
            val_str = f"{val} {unit}".strip()
            co   = p.get("company_name", "")
            doc  = p.get("doc_type", "")
            src  = p.get("source_stem", "")
            lines.append(f"- **{p['param_group']}**: {val_str} ({co} / {doc})")
            if src:
                lines.append(f"  - 출처: [[{src}]]")
        lines.append("")

    # ── 출처 목록
    lines += ["---", "", "## 📁 출처", ""]
    for p in sources:
        stem = p.get("source_stem", "")
        co   = p.get("company_name", "")
        doc  = p.get("doc_type", "")
        if stem:
            lines.append(f"- [[{stem}]] ({co} / {doc})")

    lines += [
        "",
        "---",
        f"> 자동 생성: {now} | work_build_equipment_md.py",
        f"> 총 {summary['record_count']}개 레코드 집계",
    ]

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 파일 저장
# ──────────────────────────────────────────────

def save_md(eq_name: str, content: str) -> str:
    safe = re.sub(r"[^\w가-힣\-]", "_", eq_name)
    fpath = os.path.join(OUT_MD_DIR, f"{safe}.md")
    tmp = fpath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, fpath)
    return fpath


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="설비별 MD 자동 생성기")
    parser.add_argument("--equipment", type=str, default=None, help="특정 설비만 처리")
    parser.add_argument("--force",     action="store_true")
    parser.add_argument("--min-records", type=int, default=1,
                        help="최소 레코드 수 미만 설비 건너뜀 (기본 1)")
    args = parser.parse_args()

    records = load_all_records()
    grouped = aggregate_by_equipment(records)

    if args.equipment:
        grouped = {k: v for k, v in grouped.items() if k == args.equipment}
        if not grouped:
            log.error("설비 '%s' 데이터 없음. 가용 설비: %s",
                      args.equipment, list(aggregate_by_equipment(records).keys()))
            return

    # 기존 MD 목록 (skip 판단)
    existing = set()
    if not args.force:
        for f in os.listdir(OUT_MD_DIR):
            if f.endswith(".md"):
                existing.add(f)

    stats = {"generated": 0, "skipped": 0, "total_params": 0}
    all_summaries = {}

    for eq_name, recs in sorted(grouped.items()):
        if eq_name == "기타" and not args.equipment:
            log.info("'기타' 설비 %d건 — 건너뜀 (--equipment 기타 로 강제 처리 가능)", len(recs))
            continue
        if len(recs) < args.min_records:
            continue

        safe = re.sub(r"[^\w가-힣\-]", "_", eq_name)
        fname = f"{safe}.md"

        if not args.force and fname in existing:
            stats["skipped"] += 1
            continue

        summary = build_equipment_summary(eq_name, recs)
        all_summaries[eq_name] = summary

        md = build_md(summary)
        out_path = save_md(eq_name, md)

        stats["generated"] += 1
        stats["total_params"] += summary["param_count"]
        log.info("✅ %s.md — %d파라미터 / %d레코드",
                 eq_name, summary["param_count"], summary["record_count"])

    # equipment_db.json 저장
    db_payload = {
        "built_at":  datetime.now().isoformat(timespec="seconds"),
        "equipment": all_summaries,
    }
    tmp = OUT_DB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db_payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, OUT_DB)

    print(f"\n완료: MD {stats['generated']}개 생성 / {stats['skipped']}개 스킵")
    print(f"총 파라미터: {stats['total_params']}개")
    print(f"출력 폴더: {OUT_MD_DIR}")
    print(f"DB: {OUT_DB}")

if __name__ == "__main__":
    main()
