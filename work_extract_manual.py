"""
work_extract_manual.py
매뉴얼(운전지침서/유지관리) PDF/HWP → 텍스트 청킹 → JSON

출력:
  SYSTEM/work_index/work_extracted/manual_chunks/  → {company_id}_{base}.json
  SYSTEM/work_index/work_extracted/manual_log.json

수치 파이프라인(work_extract_xlsx/pdf)과 완전 분리:
  수치 → work_extracted/datasheet|linelist/  → work_num_db (표 기반)
  매뉴얼 → work_extracted/manual_chunks/     → work_text_db (벡터 검색)

API 비용: 텍스트 PDF/HWP = 0원. 스캔 PDF만 Vision 선택적.
실행: python work_extract_manual.py [--company 36] [--limit 5] [--force] [--no-vision]
"""

import os
import re
import json
import argparse
import hashlib
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber 미설치: pip install pdfplumber")
    raise

try:
    from google import genai
    from google.genai import types as gtypes
    _VISION_OK = True
except ImportError:
    _VISION_OK = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 경로
# ──────────────────────────────────────────────
VAULT_DIR     = r"C:\Users\User\Documents\Obsidian Vault"
WORK_INDEX    = os.path.join(VAULT_DIR, "SYSTEM", "work_index")
MANIFEST_FILE = os.path.join(WORK_INDEX, "file_manifest.json")
EXTRACT_BASE  = os.path.join(WORK_INDEX, "work_extracted")
OUT_DIR       = os.path.join(EXTRACT_BASE, "manual_chunks")
MANUAL_LOG    = os.path.join(EXTRACT_BASE, "manual_log.json")

os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# 청킹 설정
# ──────────────────────────────────────────────
CHUNK_TARGET   = 600    # 목표 청크 글자수
CHUNK_MAX      = 1000   # 최대 청크 글자수
CHUNK_OVERLAP  = 80     # 앞 청크 끝 N글자를 다음 청크 앞에 붙임 (문맥 연속성)
SCAN_THRESHOLD = 50     # 페이지 텍스트 이 글자 미만 → 스캔본

# ──────────────────────────────────────────────
# 섹션 헤더 패턴 (목차 기준 분리)
# ──────────────────────────────────────────────
SECTION_PAT = re.compile(
    r"^(?:"
    r"\d+[\.\)]\s+.{2,}"          # 1. 시동 절차 / 2) 정지 방법
    r"|제\s*\d+\s*[장절항]\s*.{1,}"  # 제3장 운전 / 제2절 점검
    r"|[가나다라마바사아자차카타파하]\.\s*.{2,}"  # 가. 일반사항
    r"|[A-Z][A-Z\s]{1,20}(?:\n|$)"   # CHAPTER / OPERATION
    r"|Chapter\s+\d+"               # Chapter 1
    r")",
    re.MULTILINE
)

# 무의미 라인 패턴 (페이지 번호, 머리말 등)
NOISE_PAT = re.compile(
    r"^(?:\s*[-–—]\s*\d+\s*[-–—]\s*"   # - 1 -
    r"|\s*\d+\s*(?:page|페이지|P\.)?\s*$"  # 페이지 번호
    r"|\s*(?:Rev|Revision)\s*[\d\.]+\s*$"  # Rev 0.1
    r"|\s*(?:비밀|대외비|CONFIDENTIAL)\s*$"
    r")",
    re.IGNORECASE | re.MULTILINE
)

# 설비명 정규화 (기존 패턴 재사용)
EQUIPMENT_ALIASES = {
    "절탄기":     re.compile(r"(?i)economi[sz]er|이코노마이저|\bec\b|\becon\b|절탄기"),
    "폐열보일러":  re.compile(r"(?i)hrsg|waste.?heat.?boiler|배열보일러|폐열보일러"),
    "버너":       re.compile(r"(?i)\bburner\b|점화기|버너"),
    "소각로":     re.compile(r"(?i)incinerator|소각설비|연소로|소각로"),
    "과열기":     re.compile(r"(?i)superheater|\bsh\b|s/h|과열기"),
    "재열기":     re.compile(r"(?i)reheater|\brh\b|r/h|재열기"),
    "증기드럼":   re.compile(r"(?i)steam.?drum|\bsd\b|s/d|증기드럼"),
    "펌프":       re.compile(r"(?i)\bpump\b|\bpmp\b|펌프"),
    "열교환기":   re.compile(r"(?i)heat.?exchanger|\bhex\b|\bh/e\b|열교환기"),
    "팬":         re.compile(r"(?i)\bfan\b|\bblower\b|송풍기|팬"),
    "압축기":     re.compile(r"(?i)compressor|컴프레서|압축기"),
    "탱크":       re.compile(r"(?i)\btank\b|\btk\b|탱크"),
    "필터":       re.compile(r"(?i)filter|strainer|스트레이너|필터"),
    "밸브":       re.compile(r"(?i)\bvalve\b|밸브"),
}

# 운전 섹션 키워드 → section 태그
SECTION_KEYWORDS = {
    "시동":   re.compile(r"(?i)시동|start.?up|start\s*procedure|기동"),
    "정지":   re.compile(r"(?i)정지|shut.?down|stop\s*procedure"),
    "점검":   re.compile(r"(?i)점검|inspection|check\s*list|유지.?보수|maintenance"),
    "비상":   re.compile(r"(?i)비상|emergency|alarm|트립|trip"),
    "운전":   re.compile(r"(?i)운전|operation|operating\s*procedure|조작"),
    "경보":   re.compile(r"(?i)경보|alarm\s*list|경보.*설정|set\s*point"),
    "청소":   re.compile(r"(?i)청소|cleaning|세정|wash"),
}


# ──────────────────────────────────────────────
# 텍스트 정제
# ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = NOISE_PAT.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)   # 빈 줄 3개 이상 → 2개로
    text = re.sub(r"[ \t]+", " ", text)       # 연속 공백 정리
    return text.strip()


def detect_equipment(text: str) -> list[str]:
    found = []
    for name, pat in EQUIPMENT_ALIASES.items():
        if pat.search(text):
            found.append(name)
    return found


def detect_section_type(text: str) -> str:
    for stype, pat in SECTION_KEYWORDS.items():
        if pat.search(text):
            return stype
    return "일반"


def chunk_hash(text: str, source: str) -> str:
    s = f"{source}::{text[:100]}"
    return hashlib.sha256(s.encode()).hexdigest()[:16]


# ──────────────────────────────────────────────
# 텍스트 → 청크 분할
# ──────────────────────────────────────────────

def split_into_chunks(full_text: str, source_hint: str = "") -> list[dict]:
    """
    전략:
    1. 섹션 헤더 기준 1차 분리
    2. 섹션 내 CHUNK_MAX 초과 시 문단(\n\n) 기준 2차 분리
    3. 청크 간 CHUNK_OVERLAP 글자 중첩
    """
    if not full_text.strip():
        return []

    # 1차: 섹션 헤더 분리
    sections = []
    last_pos = 0
    current_header = ""

    for m in SECTION_PAT.finditer(full_text):
        if m.start() > last_pos:
            body = full_text[last_pos:m.start()].strip()
            if body:
                sections.append((current_header, body))
        current_header = m.group(0).strip()
        last_pos = m.end()

    # 마지막 섹션
    tail = full_text[last_pos:].strip()
    if tail:
        sections.append((current_header, tail))

    # 섹션이 없으면 전체를 단락 단위로 처리
    if not sections:
        sections = [("", full_text)]

    # 2차: 각 섹션을 CHUNK_MAX 기준으로 재분할
    chunks = []
    prev_tail = ""

    for header, body in sections:
        text_with_header = f"{header}\n{body}".strip() if header else body

        if len(text_with_header) <= CHUNK_MAX:
            # 작은 섹션: 그대로 1청크
            combined = (prev_tail + " " + text_with_header).strip() if prev_tail else text_with_header
            chunks.append({"header": header, "text": combined[:CHUNK_MAX]})
            prev_tail = text_with_header[-CHUNK_OVERLAP:] if len(text_with_header) > CHUNK_OVERLAP else ""
        else:
            # 큰 섹션: 문단 기준 재분할
            paragraphs = re.split(r"\n{2,}", text_with_header)
            buf = prev_tail
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if len(buf) + len(para) + 1 > CHUNK_MAX and buf:
                    chunks.append({"header": header, "text": buf.strip()})
                    buf = buf[-CHUNK_OVERLAP:] + " " + para  # overlap 유지
                else:
                    buf = buf + " " + para if buf else para
            if buf.strip():
                chunks.append({"header": header, "text": buf.strip()})
                prev_tail = buf[-CHUNK_OVERLAP:] if len(buf) > CHUNK_OVERLAP else buf
            else:
                prev_tail = ""

    return chunks


# ──────────────────────────────────────────────
# PDF 텍스트 추출
# ──────────────────────────────────────────────

def extract_pdf_text(fpath: str) -> tuple[str, list[int]]:
    """
    반환: (full_text, scan_pages)
    scan_pages: Vision 필요한 페이지 번호 목록
    """
    pages_text = []
    scan_pages = []

    try:
        with pdfplumber.open(fpath) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    t = page.extract_text() or ""
                except Exception:
                    t = ""
                if len(t.strip()) < SCAN_THRESHOLD:
                    scan_pages.append(i + 1)
                else:
                    pages_text.append(t)
    except Exception as e:
        log.warning("PDF 열기 실패 %s: %s", fpath, e)
        return "", []

    return "\n\n".join(pages_text), scan_pages


# ──────────────────────────────────────────────
# HWP 텍스트 추출 (hwp5txt)
# ──────────────────────────────────────────────

def extract_hwp_text(fpath: str) -> str:
    """hwp5txt → 실패 시 빈 문자열"""
    try:
        result = subprocess.run(
            ["hwp5txt", fpath],
            capture_output=True, text=True, encoding="utf-8", timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        log.debug("hwp5txt 미설치 — HWP 건너뜀. 설치: pip install olefile")
    except Exception as e:
        log.debug("hwp5txt 실패 %s: %s", Path(fpath).name, e)

    # LibreOffice 폴백 (텍스트 변환)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["soffice", "--headless", "--convert-to", "txt", "--outdir", tmpdir, fpath],
                capture_output=True, timeout=60
            )
            txt_name = Path(fpath).stem + ".txt"
            txt_path = os.path.join(tmpdir, txt_name)
            if os.path.exists(txt_path):
                return open(txt_path, encoding="utf-8", errors="replace").read()
    except Exception:
        pass

    return ""


# ──────────────────────────────────────────────
# Vision 폴백 (스캔본 전용)
# ──────────────────────────────────────────────

def extract_scan_pages_vision(
    fpath: str,
    scan_pages: list[int],
    budget: list[int],
    max_budget: int,
) -> str:
    if not _VISION_OK or not scan_pages or budget[0] >= max_budget:
        return ""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""

    try:
        import fitz
    except ImportError:
        return ""

    client = genai.Client(api_key=api_key)
    texts = []

    try:
        doc = fitz.open(fpath)
    except Exception:
        return ""

    PROMPT = "이 이미지는 산업 기계 운전/유지관리 매뉴얼 페이지입니다. 텍스트를 그대로 추출하세요. 표, 절차, 주의사항 포함. 레이아웃은 무시하고 텍스트만 출력."

    for pn in scan_pages[:5]:  # 스캔 페이지 최대 5장
        if budget[0] >= max_budget:
            break
        try:
            page = doc[pn - 1]
            pix  = page.get_pixmap(dpi=150)
            img  = pix.tobytes("png")
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[gtypes.Part.from_bytes(data=img, mime_type="image/png"), PROMPT],
            )
            budget[0] += 1
            texts.append(resp.text.strip())
        except Exception as e:
            log.debug("Vision 실패 p%d: %s", pn, e)

    doc.close()
    return "\n\n".join(texts)


# ──────────────────────────────────────────────
# 단일 파일 처리
# ──────────────────────────────────────────────

def process_manual(
    entry: dict,
    vision_budget: list[int],
    max_budget: int,
    use_vision: bool,
) -> dict:
    fpath    = entry["abs_path"]
    ext      = Path(fpath).suffix.lower()
    company_id   = entry.get("company_id", "")
    company_name = entry.get("company_name", company_id)
    equipment_hint = entry.get("equipment", "")

    result = {
        "source_path":  fpath,
        "company_id":   company_id,
        "company_name": company_name,
        "equipment":    equipment_hint,
        "doc_type":     "MANUAL",
        "rev":          entry.get("rev", ""),
        "is_latest":    entry.get("is_latest", True),
        "chunks":       [],
        "ok":           False,
        "error":        "",
        "vision_pages": 0,
    }

    # ── 텍스트 추출
    scan_pages = []
    if ext == ".pdf":
        raw_text, scan_pages = extract_pdf_text(fpath)
        if use_vision and scan_pages:
            vis_text = extract_scan_pages_vision(fpath, scan_pages, vision_budget, max_budget)
            if vis_text:
                raw_text = raw_text + "\n\n" + vis_text
                result["vision_pages"] = len(scan_pages)
    elif ext in {".hwp"}:
        raw_text = extract_hwp_text(fpath)
    elif ext in {".doc", ".docx"}:
        # LibreOffice → txt 폴백
        raw_text = extract_hwp_text(fpath)  # 동일 로직 재사용
    else:
        result["error"] = f"지원 안 됨: {ext}"
        return result

    if not raw_text.strip():
        result["ok"] = True  # 텍스트 없음 = 스캔본, 실패 아님
        return result

    # ── 정제 + 청킹
    cleaned = clean_text(raw_text)
    raw_chunks = split_into_chunks(cleaned, fpath)

    # ── 메타데이터 부착
    source_stem = Path(fpath).stem
    for idx, chunk in enumerate(raw_chunks):
        text = chunk["text"].strip()
        if len(text) < 30:  # 너무 짧은 청크 제외
            continue

        equip_list = detect_equipment(text) or ([equipment_hint] if equipment_hint else [])
        section_type = detect_section_type(text)

        result["chunks"].append({
            "chunk_idx":    idx,
            "text":         text,
            "header":       chunk.get("header", ""),
            "section_type": section_type,
            "equipment":    equip_list,
            "company_id":   company_id,
            "company_name": company_name,
            "source_file":  source_stem,
            "source_path":  fpath,
            "rev":          entry.get("rev", ""),
            "chunk_hash":   chunk_hash(text, fpath),
            "char_count":   len(text),
        })

    result["ok"] = True
    return result


# ──────────────────────────────────────────────
# 저장
# ──────────────────────────────────────────────

def save_result(result: dict) -> str:
    company_id = result["company_id"]
    base = Path(result["source_path"]).stem[:40]
    safe = re.sub(r"[^\w가-힣\-]", "_", base)
    fname = f"{company_id}_{safe}.json"
    out_path = os.path.join(OUT_DIR, fname)

    payload = {
        "meta": {
            "source_path":  result["source_path"],
            "company_id":   result["company_id"],
            "company_name": result["company_name"],
            "equipment":    result["equipment"],
            "doc_type":     "MANUAL",
            "rev":          result["rev"],
            "is_latest":    result["is_latest"],
            "extracted_at": datetime.now().isoformat(timespec="seconds"),
            "chunk_count":  len(result["chunks"]),
            "vision_pages": result["vision_pages"],
        },
        "chunks": result["chunks"],
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
    parser = argparse.ArgumentParser(description="매뉴얼 텍스트 청킹기")
    parser.add_argument("--company",       type=str, default=None)
    parser.add_argument("--limit",         type=int, default=None)
    parser.add_argument("--force",         action="store_true")
    parser.add_argument("--no-vision",     action="store_true")
    parser.add_argument("--vision-budget", type=int, default=30)
    parser.add_argument("--latest-only",   action="store_true", default=True)
    args = parser.parse_args()

    with open(MANIFEST_FILE, encoding="utf-8") as f:
        manifest = json.load(f)

    # company_name 로드
    company_map = {e["company_id"]: e.get("company_name", e["company_id"])
                   for e in manifest if "company_id" in e}

    # 매뉴얼 대상: MANUAL + PDF/HWP/DOC (DWG, XLS 제외)
    TEXT_EXTS = {".pdf", ".hwp", ".doc", ".docx"}
    targets = [
        e for e in manifest
        if Path(e["abs_path"]).suffix.lower() in TEXT_EXTS
        and not Path(e["abs_path"]).name.startswith("~$")
        and e.get("doc_type") == "MANUAL"
        and (not args.latest_only or e.get("is_latest", True))
        and (args.company is None or str(e.get("company_id", "")) == args.company)
    ]

    # company_name 주입
    for e in targets:
        e["company_name"] = company_map.get(str(e.get("company_id", "")), "")

    log.info("처리 대상: %d개 매뉴얼 (manifest 전체: %d개)", len(targets), len(manifest))

    if args.limit:
        targets = targets[:args.limit]

    # skip 판단
    existing = set()
    if not args.force:
        for f in os.listdir(OUT_DIR):
            if f.endswith(".json"):
                existing.add(f)

    vision_budget = [0]
    use_vision = not args.no_vision and _VISION_OK
    stats = {"processed": 0, "skipped": 0, "failed": 0,
             "total_chunks": 0, "vision_calls": 0}
    log_entries = []

    for entry in targets:
        company_id = entry.get("company_id", "00")
        base = Path(entry["abs_path"]).stem[:40]
        safe = re.sub(r"[^\w가-힣\-]", "_", base)
        fname = f"{company_id}_{safe}.json"

        if not args.force and fname in existing:
            stats["skipped"] += 1
            continue

        log.info("[MANUAL] %s", Path(entry["abs_path"]).name[:60])
        result = process_manual(entry, vision_budget, args.vision_budget, use_vision)

        if not result["ok"]:
            stats["failed"] += 1
            log_entries.append({"path": entry["abs_path"], "ok": False, "error": result["error"]})
            continue

        n = len(result["chunks"])
        if n > 0:
            out_path = save_result(result)
            log.info("  → %d청크 저장: %s", n, Path(out_path).name)
        else:
            log.info("  → 텍스트 없음 (스캔본 또는 빈 파일)")

        stats["processed"] += 1
        stats["total_chunks"] += n
        stats["vision_calls"] = vision_budget[0]
        log_entries.append({"path": entry["abs_path"], "ok": True, "chunks": n})

    # 로그
    tmp = MANUAL_LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "args": vars(args), "stats": stats, "entries": log_entries,
        }, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MANUAL_LOG)

    print(f"\n완료: 처리 {stats['processed']}개 / 스킵 {stats['skipped']}개 / 실패 {stats['failed']}개")
    print(f"총 청크: {stats['total_chunks']}개")
    print(f"Vision 호출: {stats['vision_calls']}회")


if __name__ == "__main__":
    main()
