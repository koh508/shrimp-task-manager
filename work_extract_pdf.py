"""
work_extract_pdf.py
file_manifest.json에서 PDF(DATA_SHEET / LINELIST)를 읽어 수치 데이터 JSON 추출

3단 방어 구조:
  1차: pdfplumber  — 텍스트 기반 표/KV 추출 (API 0원)
  2차: camelot     — 격자형 표 (API 0원)
  3차: Gemini Vision — 스캔본 전용, 조건 게이팅 (API 비용)

Vision 호출 조건 (3가지 모두):
  1. 페이지 텍스트 < 50자  (스캔본)
  2. pdfplumber 표 0개
  3. doc_type == DATA_SHEET

출력:
  SYSTEM/work_index/work_extracted/datasheet/  → {company_id}_{base}.json
  SYSTEM/work_index/work_extracted/linelist/   → {company_id}_{base}.json
  SYSTEM/work_index/work_extracted/pdf_extract_log.json

API 비용: 스캔본만 Vision 호출. 텍스트 PDF = 0원.
실행: python work_extract_pdf.py [--company 36] [--limit 5] [--force] [--no-vision] [--vision-budget 50]
"""

import os
import re
import json
import argparse
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber 미설치. 실행: pip install pdfplumber")
    raise

try:
    import camelot
    _CAMELOT_OK = True
except ImportError:
    _CAMELOT_OK = False

# Gemini Vision은 온유 시스템과 동일한 SDK 사용
try:
    from google import genai
    from google.genai import types as gtypes
    _VISION_OK = True
except ImportError:
    _VISION_OK = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 경로 설정
# ──────────────────────────────────────────────
VAULT_DIR     = r"C:\Users\User\Documents\Obsidian Vault"
WORK_INDEX    = os.path.join(VAULT_DIR, "SYSTEM", "work_index")
MANIFEST_FILE = os.path.join(WORK_INDEX, "file_manifest.json")

EXTRACT_BASE  = os.path.join(WORK_INDEX, "work_extracted")
OUT_DATASHEET = os.path.join(EXTRACT_BASE, "datasheet")
OUT_LINELIST  = os.path.join(EXTRACT_BASE, "linelist")
EXTRACT_LOG   = os.path.join(EXTRACT_BASE, "pdf_extract_log.json")

for d in [OUT_DATASHEET, OUT_LINELIST]:
    os.makedirs(d, exist_ok=True)

# ──────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────
SCAN_TEXT_THRESHOLD = 50        # 이 글자 수 미만이면 스캔본 판단
VISION_MODEL        = "gemini-2.5-flash"
VISION_MAX_PAGES    = 8         # 파일당 Vision 최대 페이지 수

# ──────────────────────────────────────────────
# 단위 / 파라미터 정규화 패턴
# ──────────────────────────────────────────────
UNIT_PAT = re.compile(
    r"(℃|°[CF]|kPa|MPa|bar(?:a|g)?|kgf/cm2(?:G|A)?|kg/cm2(?:G|A)?|"
    r"kg/h|t/h|m3/h|Nm3/h|Nm³/h|L/min|m/s|"
    r"kW|MW|kcal/h|Mcal/h|"
    r"mm|\bm\b|inch|\"|%|ppm|pH|"
    r"rpm|Hz|\bkV\b|\bkA\b|\bV\b|\bA\b)"
)
NUM_PAT = re.compile(r"-?\d[\d,]*\.?\d*(?:\s*[~\-]\s*-?\d[\d,]*\.?\d*)?")

SKIP_PAT = re.compile(
    r"^(n/?a|tbd|tbe|-{2,}|_+|\*+|해당없음|없음|미정|검토중|refer|see|상동)$",
    re.IGNORECASE
)

# 연도 패턴 (19xx~20xx) — 값으로 잘못 추출 방지
YEAR_PAT = re.compile(r"^(19|20)\d{2}$")

# 파라미터명이 숫자만인 경우 (행번호) — skip
PARAM_NUM_ONLY = re.compile(r"^\d+$")

# 메타데이터 키워드 (파라미터명에 있으면 skip)
META_PARAM_PAT = re.compile(
    r"(?i)제작사|도면번호|문서번호|revision|프로젝트|project\s*no|"
    r"client|customer|고객사|날짜|date|sheet\s*no|rev\s*\.|승인|작성|검토"
)

# 파라미터명 정규화
PARAM_NORMALIZE = [
    (re.compile(r"(?i)temp(?:erature)?|온\s*도"),      "온도"),
    (re.compile(r"(?i)press(?:ure)?|압\s*력"),          "압력"),
    (re.compile(r"(?i)flow\s*rate?|유\s*량"),           "유량"),
    (re.compile(r"(?i)inlet|in(?:let)?\.?\s*|입\s*구"), "입구"),
    (re.compile(r"(?i)outlet|out(?:let)?\.?\s*|출\s*구"),"출구"),
    (re.compile(r"(?i)design|설\s*계"),                 "설계"),
    (re.compile(r"(?i)oper(?:ating)?|normal|정\s*상"),  "정상"),
    (re.compile(r"(?i)capacity|용\s*량"),               "용량"),
    (re.compile(r"(?i)speed|rpm|회\s*전"),              "회전수"),
    (re.compile(r"(?i)power|출\s*력|동\s*력"),          "동력"),
    (re.compile(r"(?i)efficiency|효\s*율"),             "효율"),
]

# 설비명 정규화 (manifest와 동일)
EQUIPMENT_ALIASES = {
    "절탄기":   re.compile(r"(?i)economi[sz]er|이코노마이저|\bec\b|\becon\b"),
    "폐열보일러": re.compile(r"(?i)hrsg|waste.?heat.?boiler|배열보일러"),
    "버너":     re.compile(r"(?i)burner|점화기"),
    "소각로":   re.compile(r"(?i)incinerator|소각설비|연소로"),
    "과열기":   re.compile(r"(?i)superheater|\bsh\b|s/h"),
    "재열기":   re.compile(r"(?i)reheater|\brh\b|r/h"),
    "증기드럼": re.compile(r"(?i)steam.?drum|\bsd\b|s/d"),
    "탈기기":   re.compile(r"(?i)deaerat|탈기"),
    "응축기":   re.compile(r"(?i)condenser|콘덴서"),
    "펌프":     re.compile(r"(?i)\bpump\b|\bpmp\b"),
    "열교환기": re.compile(r"(?i)heat.?exchanger|\bhex\b|\bh/e\b"),
    "압력용기": re.compile(r"(?i)pressure.?vessel|\bpv\b"),
    "탱크":     re.compile(r"(?i)\btank\b|\btk\b"),
    "필터":     re.compile(r"(?i)filter|strainer|스트레이너"),
    "공기압축기": re.compile(r"(?i)air.?compressor|에어컴프레서"),
    "팬":       re.compile(r"(?i)\bfan\b|\bblower\b"),
    "압축기":   re.compile(r"(?i)compressor|컴프레서"),
}

def normalize_equipment(text: str) -> str | None:
    if not text:
        return None
    for name, pat in EQUIPMENT_ALIASES.items():
        if pat.search(text):
            return name
    return None

def normalize_param(text: str) -> str:
    """파라미터명 정규화 (공백 정리 + 한영 통일)"""
    text = re.sub(r"\s+", " ", str(text)).strip()
    for pat, norm in PARAM_NORMALIZE:
        if pat.search(text):
            # 원본 유지하되 표준어 추가 (예: "Gas Inlet Temp → 입구_온도")
            break
    return text

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text))
    text = text.replace("\x00", "")
    return text.strip()

def extract_value_unit(raw: str) -> tuple[str, str]:
    raw = clean_text(raw)
    unit_m = UNIT_PAT.search(raw)
    unit = unit_m.group(0) if unit_m else ""
    stripped = raw.replace(unit, "").strip() if unit else raw
    num_m = NUM_PAT.search(stripped)
    value = num_m.group(0).replace(",", "") if num_m else stripped
    return value, unit

def chunk_hash(data: dict) -> str:
    s = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:16]

# ──────────────────────────────────────────────
# 1차: pdfplumber 텍스트 / 표 추출
# ──────────────────────────────────────────────

def _parse_table_rows(table: list[list]) -> list[dict]:
    """pdfplumber 또는 camelot 표 → 레코드 리스트"""
    records = []
    if not table or len(table) < 2:
        return records

    # 첫 행을 헤더로 가정
    header = [clean_text(c or "") for c in table[0]]
    if not any(header):
        header = [f"col{i}" for i in range(len(table[0]))]

    for row in table[1:]:
        if not row or not any(row):
            continue
        vals = [clean_text(c or "") for c in row]

        # 첫 컬럼 = 파라미터명
        param = vals[0] if vals else ""
        if not param or SKIP_PAT.match(param.lower()):
            continue
        # 행번호(숫자만) 또는 메타데이터 파라미터 skip
        if PARAM_NUM_ONLY.match(param):
            continue
        if META_PARAM_PAT.search(param):
            continue

        # 나머지 컬럼에서 값/단위 추출
        value_cells = [v for v in vals[1:] if v and not SKIP_PAT.match(v.lower())]
        if not value_cells:
            continue

        # 단위 컬럼 분리 (마지막 셀이 순수 단위면)
        unit = ""
        if len(value_cells) >= 2 and UNIT_PAT.fullmatch(value_cells[-1].strip()):
            unit = value_cells.pop()

        raw_v = value_cells[-1] if value_cells else ""
        v, u = extract_value_unit(raw_v)
        if not u:
            u = unit

        if not v:
            continue

        # 연도 값 제외 (2019, 2020 등)
        if YEAR_PAT.match(v.strip()):
            continue

        try:
            float(v.split("~")[0].split("-")[0].strip() or "x")
        except ValueError:
            continue  # 숫자 아닌 값 제외

        equipment = normalize_equipment(param)

        records.append({
            "parameter": normalize_param(param),
            "value":     v,
            "unit":      u,
            "equipment": equipment,
            "source":    "table",
        })

    return records


def _parse_kv_text(text: str) -> list[dict]:
    """
    텍스트에서 KEY : VALUE 또는 KEY = VALUE 패턴 추출
    예: "Gas Inlet Temp : 250 ℃" → {parameter: "온도", value: "250", unit: "℃"}
    """
    records = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if len(line) < 3:
            continue

        # 구분자 탐지: ":", "=", "│", 2+ 공백
        m = re.match(r"^(.+?)\s*[:=│]\s*(.+)$", line)
        if not m:
            # 2개 이상 공백으로 구분된 KV (PDF 컬럼 정렬)
            parts = re.split(r"\s{2,}", line)
            if len(parts) < 2:
                continue
            key, raw_v = parts[0], parts[-1]
        else:
            key, raw_v = m.group(1), m.group(2)

        key = clean_text(key)
        raw_v = clean_text(raw_v)

        if not key or not raw_v:
            continue
        if SKIP_PAT.match(raw_v.lower()):
            continue
        if META_PARAM_PAT.search(key):
            continue

        # 파라미터명에 의미 있는 키워드 있어야 함
        has_param_kw = any(
            p.search(key) for p, _ in PARAM_NORMALIZE
        )
        if not has_param_kw:
            continue

        v, u = extract_value_unit(raw_v)
        if not v:
            continue

        if YEAR_PAT.match(v.strip()):
            continue

        try:
            float(v.split("~")[0].strip() or "x")
        except ValueError:
            continue

        equipment = normalize_equipment(key) or normalize_equipment(raw_v)

        records.append({
            "parameter": normalize_param(key),
            "value":     v,
            "unit":      u,
            "equipment": equipment,
            "source":    "kv_text",
        })

    return records


def extract_with_pdfplumber(fpath: str, doc_type: str) -> tuple[list[dict], list[int]]:
    """
    pdfplumber로 전 페이지 처리
    반환: (records, scan_pages)  — scan_pages는 Vision 필요한 페이지 번호 목록
    """
    records = []
    scan_pages = []

    try:
        pdf = pdfplumber.open(fpath)
    except Exception as e:
        log.warning("pdfplumber 열기 실패 %s: %s", fpath, e)
        return records, scan_pages

    with pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # 텍스트 추출
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text_len = len(text.strip())
            is_scan = text_len < SCAN_TEXT_THRESHOLD

            # 표 추출 시도
            try:
                tables = page.extract_tables()
            except Exception:
                tables = []

            if tables:
                for tbl in tables:
                    recs = _parse_table_rows(tbl)
                    for r in recs:
                        r["page"] = page_num
                    records.extend(recs)
                log.debug("  p%d: pdfplumber 표 %d개, %d건", page_num, len(tables), len(recs))

            elif text and not is_scan:
                # 표 없지만 텍스트 있음 → KV 파싱
                recs = _parse_kv_text(text)
                for r in recs:
                    r["page"] = page_num
                records.extend(recs)
                log.debug("  p%d: KV 텍스트 %d건", page_num, len(recs))

            elif is_scan and doc_type == "DATA_SHEET":
                # 스캔본 + DATA SHEET → Vision 후보
                scan_pages.append(page_num)
                log.debug("  p%d: 스캔본 → Vision 후보", page_num)

    return records, scan_pages


# ──────────────────────────────────────────────
# 2차: camelot (격자형 표)
# ──────────────────────────────────────────────

def extract_with_camelot(fpath: str, pages_to_try: list[int]) -> list[dict]:
    """
    camelot lattice 모드로 격자형 표 추출
    pages_to_try: pdfplumber에서 표를 못 찾은 페이지들
    """
    if not _CAMELOT_OK or not pages_to_try:
        return []

    records = []
    page_str = ",".join(str(p) for p in pages_to_try[:10])  # 최대 10페이지

    try:
        tables = camelot.read_pdf(
            fpath,
            pages=page_str,
            flavor="lattice",
            suppress_stdout=True,
        )
    except Exception as e:
        log.debug("camelot 실패 %s (p%s): %s", Path(fpath).name, page_str, e)
        # lattice 실패 시 stream 모드 시도
        try:
            tables = camelot.read_pdf(
                fpath,
                pages=page_str,
                flavor="stream",
                suppress_stdout=True,
            )
        except Exception:
            return []

    for tbl in tables:
        df = tbl.df
        if df.empty or len(df) < 2:
            continue
        # DataFrame → list[list] 변환
        as_list = [df.columns.tolist()] + df.values.tolist()
        recs = _parse_table_rows(as_list)
        for r in recs:
            r["page"] = tbl.page
            r["source"] = "camelot"
        records.extend(recs)

    return records


# ──────────────────────────────────────────────
# 3차: Gemini Vision (스캔본 전용)
# ──────────────────────────────────────────────

def extract_with_vision(
    fpath: str,
    scan_pages: list[int],
    equipment_hint: str,
    budget_counter: list[int],
    max_budget: int,
) -> list[dict]:
    """
    스캔본 페이지를 Gemini Vision으로 처리
    budget_counter: [current_count] — 변경 가능한 참조
    """
    if not _VISION_OK:
        log.warning("google-genai 미설치 — Vision 건너뜀")
        return []
    if not scan_pages:
        return []
    if budget_counter[0] >= max_budget:
        log.warning("Vision 예산 소진 (%d/%d) — %s 건너뜀",
                    budget_counter[0], max_budget, Path(fpath).name)
        return []

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.warning("GEMINI_API_KEY 환경변수 없음 — Vision 건너뜀")
        return []

    records = []
    pages_to_process = scan_pages[:VISION_MAX_PAGES]

    try:
        import fitz  # PyMuPDF
    except ImportError:
        log.warning("PyMuPDF 미설치 — Vision용 이미지 변환 불가. 설치: pip install pymupdf")
        return []

    try:
        doc = fitz.open(fpath)
    except Exception as e:
        log.warning("PyMuPDF 열기 실패 %s: %s", fpath, e)
        return []

    client = genai.Client(api_key=api_key)

    VISION_PROMPT = f"""이 이미지는 산업용 기계 DATA SHEET입니다.{' 설비: ' + equipment_hint if equipment_hint else ''}

아래 형식으로 수치 데이터를 JSON 배열로 추출하세요:
[{{"parameter": "파라미터명", "value": "수치", "unit": "단위"}}]

규칙:
- 온도, 압력, 유량, 용량, 동력 등 수치 데이터만 추출
- 텍스트 설명, 회사명, 날짜는 제외
- 값이 없는 항목은 제외
- JSON만 출력 (마크다운 코드블록 없이)"""

    for page_num in pages_to_process:
        if budget_counter[0] >= max_budget:
            break

        try:
            page = doc[page_num - 1]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
        except Exception as e:
            log.warning("이미지 변환 실패 p%d: %s", page_num, e)
            continue

        try:
            response = client.models.generate_content(
                model=VISION_MODEL,
                contents=[
                    gtypes.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    VISION_PROMPT,
                ],
            )
            budget_counter[0] += 1
            raw = response.text.strip()

            # JSON 파싱
            json_m = re.search(r"\[.*\]", raw, re.DOTALL)
            if not json_m:
                continue
            parsed = json.loads(json_m.group(0))

            for item in parsed:
                param = str(item.get("parameter", "")).strip()
                value = str(item.get("value", "")).strip()
                unit  = str(item.get("unit", "")).strip()
                if not param or not value:
                    continue
                try:
                    float(value.split("~")[0].strip() or "x")
                except ValueError:
                    continue

                records.append({
                    "parameter": normalize_param(param),
                    "value":     value,
                    "unit":      unit,
                    "equipment": normalize_equipment(param) or normalize_equipment(equipment_hint),
                    "page":      page_num,
                    "source":    "vision",
                })

            log.info("  Vision p%d: %d건 (예산 %d/%d)",
                     page_num, len(parsed), budget_counter[0], max_budget)

        except Exception as e:
            log.warning("Vision API 오류 p%d: %s", page_num, e)

    doc.close()
    return records


# ──────────────────────────────────────────────
# 단일 PDF 처리
# ──────────────────────────────────────────────

def process_pdf(
    entry: dict,
    vision_budget: list[int],
    max_budget: int,
    use_vision: bool,
) -> dict:
    fpath    = entry["abs_path"]
    doc_type = entry.get("doc_type", "DATA_SHEET")
    company_id = entry.get("company_id", "00")
    equipment  = entry.get("equipment", "")

    result = {
        "source_path": fpath,
        "company_id":  company_id,
        "equipment":   equipment,
        "doc_type":    doc_type,
        "rev":         entry.get("rev", ""),
        "is_latest":   entry.get("is_latest", True),
        "records":     [],
        "ok":          False,
        "error":       "",
        "vision_pages": 0,
    }

    # ── 1차: pdfplumber
    records, scan_pages = extract_with_pdfplumber(fpath, doc_type)
    log.debug("  pdfplumber: %d건, 스캔페이지 %d개", len(records), len(scan_pages))

    # ── 2차: camelot (pdfplumber 표 미탐지 페이지 대상)
    if _CAMELOT_OK and len(records) == 0:
        # 전체 페이지에 camelot 시도 (표 없던 파일 전체)
        cam_recs = extract_with_camelot(fpath, list(range(1, 21)))  # 최대 20페이지
        if cam_recs:
            log.debug("  camelot: %d건 추가", len(cam_recs))
            records.extend(cam_recs)

    # ── 3차: Vision (스캔본 + 예산 있을 때만)
    if use_vision and scan_pages and not records:
        vis_recs = extract_with_vision(
            fpath, scan_pages, equipment, vision_budget, max_budget
        )
        records.extend(vis_recs)
        result["vision_pages"] = len(scan_pages)

    # ── 공통 후처리
    seen = set()
    deduped = []
    for r in records:
        # 설비명 보강
        if not r.get("equipment") and equipment:
            r["equipment"] = equipment
        r["chunk_hash"] = chunk_hash({
            "path": fpath, "page": r.get("page", 0),
            "param": r.get("parameter", ""), "value": r.get("value", "")
        })
        key = r["chunk_hash"]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    result["records"] = deduped
    result["ok"] = True
    return result


# ──────────────────────────────────────────────
# 결과 저장
# ──────────────────────────────────────────────

def save_result(result: dict) -> str:
    company_id = result["company_id"]
    base = Path(result["source_path"]).stem[:40]
    safe_base = re.sub(r"[^\w가-힣\-]", "_", base)
    fname = f"{company_id}_{safe_base}.json"

    out_path = os.path.join(
        OUT_DATASHEET if result["doc_type"] == "DATA_SHEET" else OUT_LINELIST,
        fname
    )
    payload = {
        "meta": {
            "source_path":  result["source_path"],
            "company_id":   result["company_id"],
            "equipment":    result["equipment"],
            "doc_type":     result["doc_type"],
            "rev":          result["rev"],
            "is_latest":    result["is_latest"],
            "extracted_at": datetime.now().isoformat(timespec="seconds"),
            "record_count": len(result["records"]),
            "vision_pages": result["vision_pages"],
        },
        "records": result["records"],
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, out_path)
    return out_path


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PDF 수치 추출기")
    parser.add_argument("--company",       type=str, default=None)
    parser.add_argument("--limit",         type=int, default=None)
    parser.add_argument("--force",         action="store_true")
    parser.add_argument("--no-vision",     action="store_true", help="Vision API 비활성화")
    parser.add_argument("--vision-budget", type=int, default=50,
                        help="Vision API 최대 호출 수 (기본 50)")
    parser.add_argument("--latest-only",   action="store_true", default=True)
    args = parser.parse_args()

    with open(MANIFEST_FILE, encoding="utf-8") as f:
        manifest = json.load(f)

    targets = [
        e for e in manifest
        if Path(e["abs_path"]).suffix.lower() == ".pdf"
        and not Path(e["abs_path"]).name.startswith("~$")
        and e.get("doc_type") in {"DATA_SHEET", "LINELIST"}
        and (not args.latest_only or e.get("is_latest", True))
        and (args.company is None or str(e.get("company_id", "")) == args.company)
    ]

    log.info("처리 대상: %d개 PDF (전체 manifest: %d개)", len(targets), len(manifest))

    if args.limit:
        targets = targets[:args.limit]
        log.info("--limit 적용: %d개만 처리", args.limit)

    # 기존 추출 파일 (skip 판단)
    existing = set()
    if not args.force:
        for d in [OUT_DATASHEET, OUT_LINELIST]:
            for f in os.listdir(d):
                if f.endswith(".json"):
                    existing.add(f)

    use_vision = not args.no_vision and _VISION_OK
    if not _VISION_OK and not args.no_vision:
        log.warning("google-genai 미설치 — Vision 비활성화")
    if not _CAMELOT_OK:
        log.warning("camelot 미설치 — 2차 표 추출 비활성화")

    vision_budget = [0]  # 변경 가능한 참조 (int wrapper)
    stats = {"processed": 0, "skipped": 0, "failed": 0, "total_records": 0, "vision_calls": 0}
    log_entries = []

    for entry in targets:
        company_id = entry.get("company_id", "00")
        base = Path(entry["abs_path"]).stem[:40]
        safe_base = re.sub(r"[^\w가-힣\-]", "_", base)
        fname = f"{company_id}_{safe_base}.json"

        if not args.force and fname in existing:
            stats["skipped"] += 1
            continue

        log.info("[%s] %s", entry.get("doc_type"), Path(entry["abs_path"]).name)
        result = process_pdf(entry, vision_budget, args.vision_budget, use_vision)

        if not result["ok"]:
            stats["failed"] += 1
            log_entries.append({"path": entry["abs_path"], "ok": False, "error": result["error"]})
            continue

        if result["records"]:
            out_path = save_result(result)
            log.info("  → %d건 저장: %s (Vision %d페이지)",
                     len(result["records"]), Path(out_path).name, result["vision_pages"])
        else:
            log.info("  → 추출 레코드 없음")

        stats["processed"] += 1
        stats["total_records"] += len(result["records"])
        stats["vision_calls"] = vision_budget[0]
        log_entries.append({
            "path":    entry["abs_path"],
            "ok":      True,
            "doc_type": result["doc_type"],
            "records": len(result["records"]),
            "vision_pages": result["vision_pages"],
        })

    # 로그 저장
    log_payload = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "args":   vars(args),
        "stats":  stats,
        "entries": log_entries,
    }
    tmp = EXTRACT_LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, EXTRACT_LOG)

    print(f"\n완료: 처리 {stats['processed']}개 / 스킵 {stats['skipped']}개 / 실패 {stats['failed']}개")
    print(f"총 추출 레코드: {stats['total_records']}건")
    print(f"Vision API 호출: {stats['vision_calls']}회")

if __name__ == "__main__":
    main()
