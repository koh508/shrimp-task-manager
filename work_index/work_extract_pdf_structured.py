"""
work_extract_pdf_structured.py
Tag-First PDF Extractor — 태그 기반 구조화 JSON 추출

출력: work_extracted/pdf_structured/{TAG}__{파일명}.json
      (태그별 1파일이 아닌 PDF별 1파일 → 충돌/덮어쓰기 방지)

실행:
  python work_extract_pdf_structured.py [--company 30] [--force]
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from datetime import datetime

import pdfplumber

# ─────────────────────────────────────────────────────
# 경로
# ─────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent            # work_index/
MANIFEST_FILE = SCRIPT_DIR / "file_manifest.json"
OUTPUT_DIR    = SCRIPT_DIR / "work_extracted" / "pdf_structured"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# 태그 패턴 (P0-0402, FD-101A, LT-2301, PIT-0301A 등)
# 구분자(-/_) 필수 → "EN1092" 같은 표준규격 번호 오매칭 방지
# ─────────────────────────────────────────────────────
TAG_PATTERN = re.compile(r'\b([A-Z]{1,4}\d{0,2}[-_]\d{3,5}[A-Z]?(?:[/][AB])?)\b')

# ─────────────────────────────────────────────────────
# 섹션 헤더 감지
# ─────────────────────────────────────────────────────
SECTION_HEADERS = {
    "BEARING":     re.compile(r'\bbearing\b', re.IGNORECASE),
    "LUBRICATION": re.compile(r'\b(lubricant|grease|oiling|윤활)\b', re.IGNORECASE),
    "MOTOR":       re.compile(r'\b(motor|전동기)\b', re.IGNORECASE),
    "SEAL":        re.compile(r'\b(seal|씰|mechanical seal|패킹)\b', re.IGNORECASE),
    "PERFORMANCE": re.compile(r'\b(operating data|performance|flow rate|유량|운전조건)\b', re.IGNORECASE),
    "MECHANICAL":  re.compile(r'\b(mechanical data|dimensions|coupling|커플링)\b', re.IGNORECASE),
    "HEADER":      re.compile(r'\b(customer item|data sheet|item no\.?)\b', re.IGNORECASE),
    # 팬 데이터시트 섹션 — "fan performance", "aerodynamic", "volume flow" 포함 줄
    "FAN":         re.compile(r'\b(fan\s+performance|fan\s+data|aerodynamic|volume\s+flow|air\s+flow|풍량)\b', re.IGNORECASE),
}

def detect_section(line: str) -> str | None:
    for name, pat in SECTION_HEADERS.items():
        if pat.search(line):
            return name
    return None


# ─────────────────────────────────────────────────────
# 파서 기본 클래스
# ─────────────────────────────────────────────────────
class BaseParser:
    name = "base"

    def parse(self, line: str, section: str, page: int, meta: dict) -> list[dict]:
        """
        한 줄씩, 현재 섹션 컨텍스트와 함께 호출됨.
        반환: record dict 목록 (없으면 [])
        """
        return []

    def _record(self, meta, section, position, parameter, value, unit,
                match_type="exact", page=None) -> dict:
        return {
            "tag":        meta["tag"],
            "section":    section,
            "position":   position,
            "parameter":  parameter,
            "value":      value,
            "unit":       unit,
            "match_type": match_type,   # "exact" | "pattern" | "fuzzy"
            "source": {
                "file":    meta["file"],
                "company": meta.get("company_id", ""),
                "page":    page,
            },
        }


# ─────────────────────────────────────────────────────
# 개별 파서 (플러그인)
# ─────────────────────────────────────────────────────

class BearingNumberParser(BaseParser):
    """
    실제 PDF 텍스트 형식:
      'Bearing DE | NDE 6210 Z C3 6210 Z C3  Type of terminal box ...'
    또는:
      'Drive end bearing: 6308-2Z'
    """
    name = "bearing_number"

    # KSB/Siemens 표준 형식: "Bearing DE | NDE 6210 Z C3 6210 Z C3 Type of ..."
    # 베어링 번호 패턴: 숫자로 시작, 1~3자 토큰 최대 2개 추가 (예: 6210 Z C3, 6308-2Z, NU 208)
    _BRG_NUM = r'\d\w{1,6}(?:\s+\w{1,3}){0,2}'
    _DENDE = re.compile(
        r'Bearing\s+DE\s*\|\s*NDE\s+'
        r'(' + _BRG_NUM + r')'          # DE 값
        r'\s+'
        r'(' + _BRG_NUM + r')'          # NDE 값
        r'(?=\s+(?:Type|[A-Z][a-z]{3,})|\s*$)',  # "Type of..." 또는 줄끝
        re.IGNORECASE
    )
    # 일반 형식 (한국 데이터시트): \b 추가로 단어 내부 "de" 오매칭 방지
    _DE  = re.compile(r'(?:drive.?end|\bDE\b)\s*(?:bearing|베어링)?\s*[:\-]\s*([\w\-]{4,15})')
    _NDE = re.compile(r'(?:non.?drive.?end|\bNDE\b|반구동측)\s*(?:bearing|베어링)?\s*[:\-]\s*([\w\-]{4,15})')

    def parse(self, line, section, page, meta):
        results = []

        # 형식 1: Bearing DE | NDE VALUE VALUE
        m = self._DENDE.search(line)
        if m:
            de_val, nde_val = m.group(1).strip(), m.group(2).strip()
            for pos, val in [("DE", de_val), ("NDE", nde_val)]:
                results.append(self._record(meta, "BEARING", pos, "bearing_no", val, "", "exact", page))
            return results

        # 형식 2: 개별 DE/NDE 줄
        for pat, pos in [(self._DE, "DE"), (self._NDE, "NDE")]:
            m = pat.search(line)
            if m:
                results.append(self._record(meta, "BEARING", pos, "bearing_no",
                                            m.group(1).strip(), "", "pattern", page))
        return results


class BearingLifetimeParser(BaseParser):
    name = "bearing_lifetime"
    _PAT = re.compile(r'[Bb]earing\s+lifetime\s+([\d,]+)\s*h')

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "BEARING", None, "bearing_lifetime_h",
                             m.group(1).replace(",", ""), "h", "exact", page)]


class LubricantParser(BaseParser):
    """
    'Lubricants Esso Unirex N3'
    '그리스 : Shell Alvania EP2'
    'Grease type: Mobil SHC Polyrex EM'
    """
    name = "lubricant"
    _PAT = re.compile(
        r'(?:Lubricant|Grease|그리스|润滑脂)[s]?\s*(?:type|종류)?\s*[:\-]?\s*'
        r'([A-Za-z][A-Za-z0-9\s\-\.]{2,35}?)(?=\s{2,}|\t|\n|$|Max\.|No\.|Type)',
        re.IGNORECASE
    )

    # 그리스 타입으로 볼 수 없는 키워드 — "grease gun", "grease nipple", "and Maker" 등
    _EXCLUDE = re.compile(
        r'\b(gun|nipple|maker|apply|use)\b|^(and|or|no\.?|the)\b',
        re.IGNORECASE
    )
    # 최소 구조 검증: 알파벳 2글자 이상 + 길이 5~50
    _MIN_LEN, _MAX_LEN = 5, 50

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        val = m.group(1).strip().rstrip(".,- ")
        if len(val) < self._MIN_LEN or len(val) > self._MAX_LEN:
            return []
        # 브랜드명이 아닌 동작 지시문/부품명 제거
        if self._EXCLUDE.search(val):
            return []
        # 알파벳 최소 2글자 포함 여부 (숫자만 있는 오매칭 방지)
        if not re.search(r'[A-Za-z]{2,}', val):
            return []
        return [self._record(meta, "LUBRICATION", None, "grease_type", val, "", "exact", page)]


class MotorKwParser(BaseParser):
    """
    'Rated power P2 25.30 kW'  ← 모터 정격 (이게 필요)
    'Power absorbed 19.84 kW'  ← 펌프 흡수동력 (제외)
    """
    name = "motor_kw"
    # "Rated power" 또는 "Motor power" 컨텍스트가 있을 때만
    _PAT = re.compile(r'(?:Rated\s+power|Motor\s+power|정격출력|P2)\s+(\d+(?:\.\d+)?)\s*kW', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        # MOTOR 섹션에서만 또는 Rated power 라벨이 있을 때만 추출
        if section not in ("MOTOR", "PERFORMANCE") and "rated" not in line.lower() and "p2" not in line.lower():
            return []
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "MOTOR", None, "motor_kw", m.group(1), "kW", "exact", page)]


class MotorPolesParser(BaseParser):
    """
    'Number of poles 4'
    '4극'
    """
    name = "motor_poles"
    _PAT = re.compile(r'(?:Number\s+of\s+poles|극수|Poles?)\s*[:\-]?\s*(\d+)', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "MOTOR", None, "motor_poles", m.group(1), "pole", "exact", page)]


class MotorSpeedParser(BaseParser):
    """'Motor speed 1777 rpm' / 'Speed of rotation 1770 rpm'"""
    name = "motor_speed"
    _PAT = re.compile(r'(?:Motor\s+speed|Speed\s+of\s+rotation|정격속도)\s+(\d+)\s*rpm', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "MOTOR", None, "motor_rpm", m.group(1), "rpm", "exact", page)]


class MotorVoltageParser(BaseParser):
    """'Rated voltage 380 V' / '380/660V'"""
    name = "motor_voltage"
    _PAT = re.compile(r'(?:Rated\s+voltage|정격전압|Voltage)\s+(\d+(?:/\d+)?)\s*V', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "MOTOR", None, "motor_voltage_V", m.group(1), "V", "exact", page)]


class InsulationParser(BaseParser):
    """
    유효한 절연 등급만 추출.
    - 'Insulation class F'         → F
    - 'Insulation 155(F) to 130(B)'→ F (괄호 안 문자 우선)
    - 'Insulation Resistance'       → 제외 (유효 등급 아님)
    """
    name = "insulation"
    # 괄호 안 클래스 우선: "155(F)" → F
    _PAT_PAREN = re.compile(r'[Ii]nsulation[^(]*\(([ABEFHN])\)', re.IGNORECASE)
    # 직접 클래스 명시: "Insulation class F" / "Insulation: F"
    _PAT_DIRECT = re.compile(
        r'[Ii]nsulation(?:\s+class)?\s*[:\-]?\s*([ABEFHN])\b',
        re.IGNORECASE
    )
    # 온도 등급 (155, 130 등 IEC 60085 표준값)
    _VALID_TEMPS = {105, 120, 130, 155, 180, 200, 220}

    def parse(self, line, section, page, meta):
        # 괄호 안 클래스가 있으면 우선
        m = self._PAT_PAREN.search(line)
        if m:
            return [self._record(meta, "MOTOR", None, "insulation_class",
                                 m.group(1).upper(), "", "exact", page)]
        # 직접 클래스 명시
        m = self._PAT_DIRECT.search(line)
        if m:
            return [self._record(meta, "MOTOR", None, "insulation_class",
                                 m.group(1).upper(), "", "exact", page)]
        return []


class IPRatingParser(BaseParser):
    """'IP55' / 'IP 55' / 'Protection class: IP55'"""
    name = "ip_rating"
    _PAT = re.compile(r'\bIP\s*(\d{2})\b')

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "MOTOR", None, "ip_rating", f"IP{m.group(1)}", "", "exact", page)]


class SealTypeParser(BaseParser):
    """
    'Shaft sealing mechanical seal'
    '메카니칼씰 / packing / gland'
    """
    name = "seal_type"
    # 형식 1: "Shaft seal Single acting mechanical seal"
    # 형식 2: "Seal type: Mechanical seal"
    _PAT = re.compile(
        r'(?:shaft\s+seal|seal\s+type|씰\s*타입|씰\s*종류)\s*[:\-]?\s*'
        r'((?:single\s+acting\s+|double\s+acting\s+|cartridge\s+)?'
        r'(?:mechanical\s+seal|gland\s+packing|lip\s+seal|packing|메카니칼씰))',
        re.IGNORECASE
    )

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "SEAL", None, "seal_type", m.group(1).strip(), "", "exact", page)]


class CouplingParser(BaseParser):
    """'Coupling type Eupex NH'"""
    name = "coupling"
    _PAT = re.compile(
        r'[Cc]oupling\s+type\s+'
        r'([A-Za-z][A-Za-z0-9\s\-]{1,20}?)'
        r'(?=\s+(?:IEC|ISO|ASME|EN\d|DIN)|\s{2,}|\t|\n|$)'
    )

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        val = m.group(1).strip()
        if len(val) > 30 or not val:
            return []
        return [self._record(meta, "MECHANICAL", None, "coupling_type", val, "", "exact", page)]


class FlowRateParser(BaseParser):
    """'Actual flow rate 96.40 m³/h'"""
    name = "flow_rate"
    _PAT = re.compile(r'(?:Actual\s+flow\s+rate|유량|Flow\s+rate)\s+([\d.]+)\s*(m³/h|m3/h|L/min)', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "PERFORMANCE", None, "flow_rate",
                             m.group(1), m.group(2), "exact", page)]


class HeadParser(BaseParser):
    """'Actual developed head 53.00 m'"""
    name = "head"
    _PAT = re.compile(r'(?:developed\s+head|양정|Total\s+head)\s+([\d.]+)\s*m\b', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "PERFORMANCE", None, "head_m", m.group(1), "m", "exact", page)]


class NPSHParser(BaseParser):
    """'NPSH required 1.76 m'"""
    name = "npsh"
    _PAT = re.compile(r'NPSH\s+required\s+([\d.]+)\s*m', re.IGNORECASE)

    def parse(self, line, section, page, meta):
        m = self._PAT.search(line)
        if not m:
            return []
        return [self._record(meta, "PERFORMANCE", None, "npsh_required_m", m.group(1), "m", "exact", page)]


class FanParser(BaseParser):
    """
    팬 고유 파라미터 추출. RPM/모터출력은 MotorSpeedParser/MotorKwParser에 위임.

    지원 형식:
      'Volume flow Qv = 12 000 m³/h'
      'Air flow: 12000 CMH'
      'Static pressure  45 mmAq'
      'Fan type: Axial'
    """
    name = "fan"

    # ── 풍량: Volume flow / Air flow / Capacity ────────────────────────
    # 공백 포함 숫자 허용 ("12 000 m³/h")
    _FLOW = re.compile(
        r'(?:volume\s+flow|air\s+flow|capacity|풍량|Qv)\s*[=:]?\s*'
        r'([1-9][\d\s,\.]*)\s*(m3/h|m³/h|cmh|cfm|m3/min)',
        re.IGNORECASE
    )

    # ── 정압: Static pressure ─────────────────────────────────────────
    _STATIC_P = re.compile(
        r'(?:static\s+pressure|정압|SP)\s*[=:\-]?\s*'
        r'([\d,\.]+)\s*(pa|mmaq|mm\s*aq|mm\s*h2o|mbar)',
        re.IGNORECASE
    )

    # ── 전압: Total pressure ──────────────────────────────────────────
    _TOTAL_P = re.compile(
        r'(?:total\s+pressure|전압|TP)\s*[=:\-]?\s*'
        r'([\d,\.]+)\s*(pa|mmaq|mm\s*aq|mbar)',
        re.IGNORECASE
    )

    # ── 팬 타입: Axial / Centrifugal ─────────────────────────────────
    _TYPE = re.compile(
        r'(?:fan\s+type|type\s+of\s+fan|팬\s*타입|팬\s*형식)\s*[=:\-]?\s*'
        r'(axial|centrifugal|원심|축류)',
        re.IGNORECASE
    )

    # ── Validation 상수 ───────────────────────────────────────────────
    _FLOW_RANGE   = (1.0, 1_000_000.0)   # m³/h 또는 CMH (산업용 전 범위)
    _PRESS_RANGE  = (0.1, 50_000.0)      # Pa 기준 (mmAq × 9.81)
    _VALID_TYPES  = {"axial", "centrifugal", "원심", "축류"}

    def _clean_num(self, s: str) -> float:
        return float(s.replace(",", "").replace(" ", ""))

    def parse(self, line: str, section: str, page: int, meta: dict) -> list[dict]:
        # 섹션 스코프: FAN 또는 PERFORMANCE 에서만 (MOTOR 섹션 오탐 방지)
        if section not in ("FAN", "PERFORMANCE", "HEADER"):
            # fan type은 어느 섹션에서도 허용
            if not self._TYPE.search(line):
                return []

        results = []

        # 풍량
        m = self._FLOW.search(line)
        if m:
            raw, unit = m.group(1), m.group(2).upper()
            try:
                val = self._clean_num(raw)
                lo, hi = self._FLOW_RANGE
                if lo <= val <= hi:
                    results.append(self._record(
                        meta, "FAN", None, "air_flow_m3h", str(val), unit, "exact", page))
            except ValueError:
                pass

        # 정압
        m = self._STATIC_P.search(line)
        if m:
            raw, unit = m.group(1), m.group(2)
            try:
                val = self._clean_num(raw)
                if 0.1 <= val <= 50_000:
                    results.append(self._record(
                        meta, "FAN", None, "static_pressure", str(val), unit.upper(), "exact", page))
            except ValueError:
                pass

        # 전압
        m = self._TOTAL_P.search(line)
        if m:
            raw, unit = m.group(1), m.group(2)
            try:
                val = self._clean_num(raw)
                if 0.1 <= val <= 50_000:
                    results.append(self._record(
                        meta, "FAN", None, "total_pressure", str(val), unit.upper(), "exact", page))
            except ValueError:
                pass

        # 팬 타입
        m = self._TYPE.search(line)
        if m:
            fan_type = m.group(1).strip()
            if fan_type.lower() in self._VALID_TYPES:
                results.append(self._record(
                    meta, "FAN", None, "fan_type", fan_type, "", "exact", page))

        return results


# ─────────────────────────────────────────────────────
# 파서 레지스트리 — 새 파서 추가 시 여기에만 한 줄
# ─────────────────────────────────────────────────────
PARSERS: list[BaseParser] = [
    BearingNumberParser(),
    BearingLifetimeParser(),
    LubricantParser(),
    MotorKwParser(),
    MotorPolesParser(),
    MotorSpeedParser(),
    MotorVoltageParser(),
    InsulationParser(),
    IPRatingParser(),
    SealTypeParser(),
    CouplingParser(),
    FlowRateParser(),
    HeadParser(),
    NPSHParser(),
    FanParser(),
]


# ─────────────────────────────────────────────────────
# 다중설비 PDF 분리 — 페이지 단위 태그 재할당
# ─────────────────────────────────────────────────────

# 페이지별 라벨 기반 태그 추출 (extract_tag와 동일 패턴)
_LABELED_TAG_PAGE = re.compile(
    r'(?:customer\s+item\s+no|tag\s*no|item\s*no)\.?\s*[:\-]?\s*'
    r'([A-Z]{1,4}\d{0,2}[-_]\d{3,5}[A-Z]?(?:[/][AB])?)',
    re.IGNORECASE
)

def _build_page_tag_map(pages_text: list[str], file_tag: str) -> dict[int, str]:
    """
    페이지별 설비 태그 맵.
    - 라벨 기반 태그 우선 (Customer item no. / Tag no.)
    - 없으면 이전 페이지 태그 유지 (carry-forward)
    """
    last_tag = file_tag
    tag_map: dict[int, str] = {}
    for page_no, text in enumerate(pages_text, start=1):
        m = _LABELED_TAG_PAGE.search(text)
        if m:
            last_tag = m.group(1)
        tag_map[page_no] = last_tag
    return tag_map


def _split_by_tag(records: list[dict], page_tag_map: dict[int, str],
                  file_tag: str) -> dict[str, list[dict]]:
    """
    records를 page_tag_map 기반으로 tag 재할당 후 tag별 분리.
    반환: {tag: [records]}
    """
    split: dict[str, list[dict]] = {}
    for r in records:
        page = r.get("source", {}).get("page", 0)
        assigned = page_tag_map.get(page, file_tag)
        r["tag"] = assigned
        split.setdefault(assigned, []).append(r)
    return split


# ─────────────────────────────────────────────────────
# 태그 추출
# ─────────────────────────────────────────────────────
def extract_tag(full_text: str) -> str | None:
    """
    'Customer item no.: P0-0402A/B' 같은 라벨이 있는 줄에서 우선 추출.
    없으면 전체 텍스트에서 첫 번째 TAG_PATTERN 매칭.
    """
    # 라벨 앞에 있는 태그 (신뢰도 높음) — P0-0402 형식 포함
    labeled = re.search(
        r'(?:customer\s+item\s+no|tag\s*no|item\s*no)\.?\s*[:\-]?\s*'
        r'([A-Z]{1,4}\d{0,2}[-_]\d{3,5}[A-Z]?(?:[/][AB])?)',
        full_text, re.IGNORECASE
    )
    if labeled:
        return labeled.group(1)

    # fallback: 전체 텍스트에서 첫 번째 태그 패턴
    m = TAG_PATTERN.search(full_text)
    return m.group(1) if m else None


# ─────────────────────────────────────────────────────
# Phase 1 경량 스캔 — anchor 키워드 → 페이지 매핑
# ─────────────────────────────────────────────────────
_FALLBACK_HEAD = 10   # fallback 시 앞에서 몇 페이지
_FALLBACK_TAIL = 10   # fallback 시 뒤에서 몇 페이지

def _locate_anchor_pages(
    pages_text: list[str],
    anchors: list[str],
) -> dict[str, list[int]]:
    """
    Phase 1: 파서 미실행 상태에서 anchor 키워드가 등장하는 페이지 번호 매핑 반환.

    - 전체 페이지 텍스트를 단순 regex.search()만 실행 (파서 없음 → 빠름)
    - 반환: {"P0-0301": [50, 57], "P0-0302": [69, 75]}  (1-indexed)
    - anchor 미발견 시 해당 키 → []
    """
    if not anchors:
        return {}

    # 앵커 여러 개 → OR 패턴으로 한 번에 처리 (루프 중첩 방지)
    per_anchor_pat = {
        a: re.compile(re.escape(a), re.IGNORECASE)
        for a in anchors
    }
    result: dict[str, list[int]] = {a: [] for a in anchors}

    for page_no, text in enumerate(pages_text, start=1):
        if not text:
            continue
        for anchor, pat in per_anchor_pat.items():
            if pat.search(text):
                result[anchor].append(page_no)

    return result


def _target_pages_from_anchors(
    anchor_pages: dict[str, list[int]],
    total_pages: int,
) -> set[int]:
    """
    anchor_pages dict → 파싱할 페이지 번호 집합 (1-indexed).
    앵커 발견 없으면 fallback: 앞 N + 뒤 N 페이지.
    """
    pages: set[int] = set()
    for pg_list in anchor_pages.values():
        pages.update(pg_list)

    if not pages:
        # fallback: 모든 앵커 미발견 → 앞/뒤 일부만 스캔
        head = list(range(1, min(_FALLBACK_HEAD + 1, total_pages + 1)))
        tail = list(range(max(1, total_pages - _FALLBACK_TAIL + 1), total_pages + 1))
        pages.update(head + tail)
        log.warning("⚠️  anchor 미발견 → fallback: 앞 %d + 뒤 %d 페이지", _FALLBACK_HEAD, _FALLBACK_TAIL)

    return pages


# ─────────────────────────────────────────────────────
# PDF 처리 (섹션 추적 + 라인별 파싱)
# ─────────────────────────────────────────────────────
def extract_from_pdf(
    pdf_path: Path,
    company_id: str = "",
    anchors: list[str] | None = None,
) -> list[dict]:
    log.info("처리: %s", pdf_path.name)

    # 1회 전체 텍스트 읽기 (태그 추출용)
    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    full_text = "\n".join(pages_text)

    tag = extract_tag(full_text) or "UNKNOWN"
    meta = {
        "tag":        tag,
        "file":       pdf_path.name,
        "company_id": company_id,
        "source_path": str(pdf_path),
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
    }

    # [Phase 1] anchor 지정 시 대상 페이지만 결정
    if anchors:
        import time as _time
        _t0 = _time.time()
        anchor_pages = _locate_anchor_pages(pages_text, anchors)
        target_pages = _target_pages_from_anchors(anchor_pages, len(pages_text))
        _anchor_elapsed = _time.time() - _t0
        _hit_count = sum(len(v) for v in anchor_pages.values())
        log.info("앵커 스캔 %.2fs | 히트 %d페이지 | 파싱대상 %d/%d페이지",
                 _anchor_elapsed, _hit_count, len(target_pages), len(pages_text))
        log.info("앵커 매핑: %s", {k: v for k, v in anchor_pages.items() if v})
    else:
        target_pages = set(range(1, len(pages_text) + 1))

    records: list[dict] = []
    current_section = "HEADER"

    # 페이지별, 라인별 파싱
    for page_no, text in enumerate(pages_text, start=1):
        if page_no not in target_pages:
            continue
        for line in text.splitlines():
            # 섹션 전환 감지
            new_section = detect_section(line)
            if new_section:
                current_section = new_section

            # 각 파서 실행
            for parser in PARSERS:
                try:
                    hits = parser.parse(line, current_section, page_no, meta)
                    records.extend(hits)
                except Exception as e:
                    log.debug("파서 %s 오류 (line=%r): %s", parser.name, line[:60], e)

    # 중복 제거 (같은 tag+section+position+parameter+value)
    seen = set()
    deduped = []
    for r in records:
        key = (r["tag"], r["section"], r["position"], r["parameter"], r["value"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    # ── 다중설비 PDF 분리 ───────────────────────────────────────────
    page_tag_map = _build_page_tag_map(pages_text, tag)
    split = _split_by_tag(deduped, page_tag_map, tag)

    results = []
    for split_tag, split_records in split.items():
        results.append({
            "meta": {
                "tag":         split_tag,
                "file":        pdf_path.name,
                "company_id":  company_id,
                "source_path": str(pdf_path),
                "split_from":  tag if split_tag != tag else None,
                "extracted_at": datetime.now().isoformat(timespec="seconds"),
            },
            "tag":     split_tag,
            "records": split_records,
        })

    if len(results) > 1:
        log.info("다중설비 분리: %s → %s", pdf_path.name,
                 [r["tag"] for r in results])
    return results


# ─────────────────────────────────────────────────────
# manifest 로드
# ─────────────────────────────────────────────────────
def load_manifest(company_filter: str | None = None) -> list[tuple[Path, str]]:
    """(pdf_path, company_id) 목록 반환"""
    if not MANIFEST_FILE.exists():
        log.error("manifest 없음: %s", MANIFEST_FILE)
        sys.exit(1)

    manifest = json.load(open(MANIFEST_FILE, encoding="utf-8"))
    results = []
    for entry in manifest:
        if entry.get("file_ext", "").upper() != "PDF":
            continue
        cid = str(entry.get("company_id", ""))
        if company_filter and cid != company_filter:
            continue
        path = Path(entry.get("abs_path", ""))
        if not path.exists():
            continue
        results.append((path, cid))
    return results


# ─────────────────────────────────────────────────────
# 출력 파일명 — 태그 + 원본 파일명 (충돌 방지)
# ─────────────────────────────────────────────────────
def make_output_path(tag: str, pdf_path: Path) -> Path:
    safe_tag  = re.sub(r'[^\w\-]', '_', tag)
    safe_name = re.sub(r'[^\w\-]', '_', pdf_path.stem)[:40]
    return OUTPUT_DIR / f"{safe_tag}__{safe_name}.json"


# ─────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Tag-First PDF Structured Extractor")
    parser.add_argument("--company", type=str, default=None, help="company_id 필터 (예: 30)")
    parser.add_argument("--force",   action="store_true",    help="기존 출력 파일 덮어쓰기")
    parser.add_argument("--anchor",  type=str, default=None,
                        help="앵커 태그/키워드 (쉼표 구분, 예: P0-0301,P0-0302)")
    args = parser.parse_args()

    anchors = [a.strip() for a in args.anchor.split(",")] if args.anchor else None

    pdf_list = load_manifest(args.company)
    log.info("대상 PDF: %d개", len(pdf_list))

    stats = {"processed": 0, "skipped": 0, "failed": 0, "total_records": 0}

    for pdf_path, cid in pdf_list:
        try:
            results = extract_from_pdf(pdf_path, cid, anchors)   # list[dict]

            for result in results:
                out = make_output_path(result["tag"], pdf_path)

                if out.exists() and not args.force:
                    log.info("스킵 (기존): %s", out.name)
                    stats["skipped"] += 1
                    continue

                tmp = out.with_suffix(".tmp")
                tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(out)

                rec_count = len(result["records"])
                stats["processed"] += 1
                stats["total_records"] += rec_count
                split_info = f" [split from {result['meta']['split_from']}]" if result["meta"].get("split_from") else ""
                log.info("✅ %s → %s (%d 레코드)%s", pdf_path.name, out.name, rec_count, split_info)

        except Exception as e:
            log.error("❌ 실패: %s → %s", pdf_path.name, e)
            stats["failed"] += 1

    print(f"\n완료: 처리 {stats['processed']} / 스킵 {stats['skipped']} / 실패 {stats['failed']}")
    print(f"총 레코드: {stats['total_records']}")
    print(f"출력: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
