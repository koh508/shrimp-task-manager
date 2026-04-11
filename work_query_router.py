"""
work_query_router.py
준공도서 질문 라우터 — obsidian_agent.py ask()에 연결

반환: 마크다운 텍스트 (ctx 문자열에 직접 주입 가능)
비용: API 0원 (로컬 파일 검색만)

확장 방법:
  새 데이터 소스 추가 = _SOURCES 리스트에 (라벨, 함수) 한 줄 추가.
  함수 시그니처: fn(q_lower: str) -> str
"""

import json
import re
from pathlib import Path
from typing import List, Optional

VAULT_DIR    = Path(r"C:\Users\User\Documents\Obsidian Vault")
WORK_INDEX   = VAULT_DIR / "SYSTEM" / "work_index"
EQUIP_MD_DIR = VAULT_DIR / "업무자료" / "준공도서" / "설비별"   # Layer 3 MD
DRAWING_IDX  = WORK_INDEX / "drawing_index.json"
MANUAL_DIR   = WORK_INDEX / "work_extracted" / "manual_chunks"
PDF_STRUCT_DIR = WORK_INDEX / "work_extracted" / "pdf_structured"

# ── 준공도서 질문 감지 키워드 ──────────────────────────────────────────
# 주의: "운전/정지/점검"은 일반 대화에도 쓰이므로 단독 감지에서 제외.
#       섹션 타입 매칭은 _SECTION_KEYWORDS에서 처리.
WORK_KEYWORDS = [
    "설비", "도면", "압력", "유량", "온도", "펌프", "버너", "절탄기", "팬",
    "보일러", "과열기", "재열기", "폐열보일러", "증기드럼", "탈기기",
    "급수펌프", "보일러급수", "탈기기급수", "드레인펌프", "condensate", "feedwater",
    "화격자", "밸브", "압축기", "응축기", "필터", "탱크",
    "economizer", "burner", "pump", "fan", "hrsg",
    "linelist", "line list", "datasheet", "data sheet",
    "준공", "시방서", "유지보수", "운전지침", "매뉴얼",
    # 정비 핵심 부품 키워드
    "베어링", "bearing", "그리스", "grease", "씰", "seal",
    "임펠러", "impeller", "커플링", "coupling", "모터", "motor",
    "rpm", "kw", "ip등급", "절연", "insulation",
]

# ── 설비 태그 패턴 (P0-0402, H0-0401 등) ─────────────────────────────
# 쿼리 문자열 내 태그 탐지용 (단어 경계 포함)
_TAG_RE = re.compile(r'\b[A-Za-z]{1,4}\d{0,2}[-_]\d{3,5}[A-Za-z]?\b')
# 파일 stem 시작부 태그 추출용 (P0-0402_한글설명 형태에서 태그만 추출)
_STEM_TAG_RE = re.compile(r'^([A-Za-z]{1,4}\d{0,2}-\d{3,5}[A-Za-z]?)(?:[-_]|$)')

# ── 설비명 패턴 ────────────────────────────────────────────────────────
_EQUIP_PATTERNS = [
    ("절탄기",    re.compile(r"절탄기|economizer", re.IGNORECASE)),
    ("과열기",    re.compile(r"과열기|superheater|sh[-\s]?\d", re.IGNORECASE)),
    ("재열기",    re.compile(r"재열기|reheater|rh[-\s]?\d", re.IGNORECASE)),
    ("폐열보일러", re.compile(r"폐열보일러|hrsg|waste.?heat", re.IGNORECASE)),
    ("버너",      re.compile(r"버너|burner", re.IGNORECASE)),
    ("증기드럼",  re.compile(r"증기드럼|steam.?drum", re.IGNORECASE)),
    ("펌프",      re.compile(r"펌프|pump", re.IGNORECASE)),
    ("팬",        re.compile(r"\bfan\b|blower", re.IGNORECASE)),
    ("밸브",      re.compile(r"밸브|valve", re.IGNORECASE)),
]

# ── 운전 섹션 타입 키워드 ──────────────────────────────────────────────
_SECTION_KEYWORDS = {
    "시동": ["시동", "기동", "start"],
    "정지": ["정지", "shutdown", "stop"],
    "점검": ["점검", "inspection", "check"],
    "비상": ["비상", "emergency", "alarm", "경보"],
    "운전": ["운전", "operation", "운영"],
    "청소": ["청소", "cleaning", "flush"],
}

# ── 캐시 (프로세스 수명 동안 유지, 재시작 시 자동 초기화) ───────────────
_chunk_cache: Optional[List[dict]]      = None
_drawing_cache: Optional[List[dict]]   = None
_pdf_struct_cache: Optional[List[dict]] = None


# ══════════════════════════════════════════════════════════════════════
#  공개 API
# ══════════════════════════════════════════════════════════════════════

def is_work_query(query: str) -> bool:
    """준공도서 관련 질문 여부 판단."""
    q = query.lower()
    if any(kw in q for kw in WORK_KEYWORDS):
        return True
    # 설비 태그 패턴 감지 (P0-0402, H0-0401 등)
    return bool(_TAG_RE.search(query))


def route_work_query(query: str) -> str:
    """
    등록된 모든 소스를 동시 검색, 결과를 마크다운 텍스트로 병합 반환.
    결과 없으면 "" 반환.
    질문 의도(SPEC/RELATION/MAINT)에 따른 힌트를 상단에 주입.

    ── 새 데이터 소스 추가 방법 ──────────────────────────────────────
    1. _search_xxx(q_lower: str) -> str  함수 작성
    2. 아래 _SOURCES 리스트에 ("### 라벨", _search_xxx) 한 줄 추가
    ─────────────────────────────────────────────────────────────────
    """
    q_lower = query.lower()
    intent  = classify_query(query)

    parts = []
    for label, fn in _SOURCES:
        try:
            text = fn(q_lower)
        except Exception:
            text = ""
        if text:
            parts.append(f"{label}\n{text}")

    if not parts:
        return ""

    result = "\n\n".join(parts)
    hint   = _INTENT_HINT.get(intent, "")
    return f"{hint}\n\n{result}" if hint else result


# ══════════════════════════════════════════════════════════════════════
#  소스 1: Layer 3 설비 MD (수치/제원)
# ══════════════════════════════════════════════════════════════════════

def _search_equip_md(q_lower: str) -> str:
    """
    설비명 또는 태그번호가 질문에 포함되면 Layer 3 MD 내용 반환 (파일당 2000자 제한).

    파일 종류에 따라 매칭 방식이 다름:
    - 태그 기반 파일 (P0-0402_응축수이송펌프.md) → _tag_matches() 사용
    - 카테고리 파일 (펌프.md, 밸브.md 등)       → stem 문자열 포함 여부
    """
    if not EQUIP_MD_DIR.exists():
        return ""
    found = []
    for md_file in sorted(EQUIP_MD_DIR.glob("*.md")):
        stem = md_file.stem
        tag_match = _STEM_TAG_RE.match(stem)
        if tag_match:
            # 태그 기반 파일 (P0-0402_응축수이송펌프): 태그 부분만 추출해 매칭
            if not _tag_matches(tag_match.group(1), q_lower):
                continue
        else:
            # 카테고리 파일: 단독 단어로 등장할 때만 매칭 (복합어 오탐 방지)
            # 예: "보일러급수펌프" 쿼리에서 "보일러.md", "펌프.md" 오매칭 방지
            _cat_pat = re.compile(
                r'(?<![가-힣A-Za-z])' + re.escape(stem.lower()) + r'(?![가-힣A-Za-z])'
            )
            if not _cat_pat.search(q_lower):
                continue
        content = md_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            end_idx = content.find("---", 3)
            if end_idx != -1:
                content = content[end_idx + 3:].strip()
        found.append(f"**[{stem}]**\n{content[:2000]}")
    return "\n\n".join(found)


# ══════════════════════════════════════════════════════════════════════
#  소스 2: DWG 도면 인덱스
# ══════════════════════════════════════════════════════════════════════

def _load_drawing_index() -> List[dict]:
    """drawing_index.json 로드 (모듈 레벨 캐시, 1회만 실행)."""
    global _drawing_cache
    if _drawing_cache is not None:
        return _drawing_cache
    if not DRAWING_IDX.exists():
        _drawing_cache = []
        return _drawing_cache
    with open(DRAWING_IDX, encoding="utf-8") as f:
        _drawing_cache = json.load(f)
    return _drawing_cache


def _search_drawing(q_lower: str) -> str:
    """drawing_index.json 검색 → 상위 5개 도면 경로 반환."""
    data = _load_drawing_index()
    if not data:
        return ""

    scored = []
    for d in data:
        score = 0
        eq    = (d.get("equipment") or "").lower()
        fname = d.get("file", "").lower()
        line  = (d.get("line") or "").lower()
        if line and line in q_lower:        score += 3
        if eq and eq in q_lower:            score += 2
        for tok in q_lower.split():
            if len(tok) >= 3 and tok in fname:
                score += 1
                break
        if score > 0:
            scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    lines = []
    for _, d in scored[:5]:
        eq_label = d.get("equipment") or "미분류"
        line_sfx = f", 라인: {d['line']}" if d.get("line") else ""
        lines.append(f"- {d['file']} (설비: {eq_label}{line_sfx})\n  경로: {d.get('path','')}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  소스 3: 운전 매뉴얼 청크
# ══════════════════════════════════════════════════════════════════════

def _load_all_chunks() -> List[dict]:
    """전체 manual_chunks JSON 로드 (모듈 레벨 캐시, 1회만 실행)."""
    global _chunk_cache
    if _chunk_cache is not None:
        return _chunk_cache
    chunks = []
    if not MANUAL_DIR.exists():
        _chunk_cache = chunks
        return chunks
    for jf in sorted(MANUAL_DIR.glob("*.json")):
        if jf.stem.endswith("_log") or jf.name in {"manual_log.json", "extract_log.json"}:
            continue
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
            # 구조: {"meta": {}, "chunks": [...]}
            raw = data.get("chunks", data) if isinstance(data, dict) else data
            chunks.extend(raw)
        except Exception:
            pass
    _chunk_cache = chunks
    return chunks


def _detect_section(q_lower: str) -> Optional[str]:
    for stype, kws in _SECTION_KEYWORDS.items():
        if any(kw in q_lower for kw in kws):
            return stype
    return None


def _search_manual_chunks(q_lower: str) -> str:
    """
    매뉴얼 청크를 설비명 + 섹션 타입 기준으로 검색.
    설비명도 섹션 타입도 감지 안 되면 "" 반환 (노이즈 방지).
    """
    # regex 패턴으로 감지 (한국어 + 영문 동의어 모두 커버)
    target_equip   = next((n for n, p in _EQUIP_PATTERNS if p.search(q_lower)), None)
    target_section = _detect_section(q_lower)

    if not target_equip and not target_section:
        return ""

    chunks = _load_all_chunks()
    scored = []
    q_tokens = [t for t in q_lower.split() if len(t) >= 3]

    # 설비명 없을 때는 노이즈 차단을 강화 (섹션 타입 + 텍스트 키워드 동시 필요)
    min_score = 2 if target_equip else 3

    for c in chunks:
        score = 0
        c_equip   = c.get("equipment") or []
        c_section = c.get("section_type") or ""
        c_text    = c.get("text", "").lower()

        if target_equip and target_equip in c_equip:       score += 3
        if target_section and target_section == c_section: score += 2
        if any(tok in c_text for tok in q_tokens):         score += 1

        if score >= min_score:
            scored.append((score, c))

    if not scored:
        return ""

    scored.sort(key=lambda x: x[0], reverse=True)
    lines = []
    for _, c in scored[:3]:
        header  = c.get("header", "")
        company = c.get("company_name", "")
        text    = c.get("text", "").strip()[:300]
        src     = c.get("source_file", "")
        lines.append(f"**{header}** ({company} / {src})\n{text}...")
    return "\n\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  소스 4: pdf_structured JSON (Tag-First 추출 결과)
# ══════════════════════════════════════════════════════════════════════

def _load_pdf_structured() -> List[dict]:
    """pdf_structured JSON 전체 로드 (모듈 레벨 캐시)."""
    global _pdf_struct_cache
    if _pdf_struct_cache is not None:
        return _pdf_struct_cache
    result = []
    if not PDF_STRUCT_DIR.exists():
        _pdf_struct_cache = result
        return result
    for jf in sorted(PDF_STRUCT_DIR.glob("*.json")):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
            result.append(data)
        except Exception:
            pass
    _pdf_struct_cache = result
    return result


# ── 그리스 오탐 필터 (JSON에 잔류한 노이즈 제거) ──────────────────────
_GREASE_INVALID = re.compile(
    r'\b(gun|nipple|maker|apply|use)\b|^(and|or|the|no\.?)\b',
    re.IGNORECASE
)

def _is_valid_grease(val: str) -> bool:
    """실제 그리스 제품명 여부 판단. 짧거나 동작 지시문이면 False."""
    v = val.strip()
    if len(v) < 5 or len(v) > 50:
        return False
    if _GREASE_INVALID.search(v):
        return False
    return bool(re.search(r'[A-Za-z]{2,}', v))


_VALID_INSULATION_CLASS = frozenset("ABEFHN")
_VALID_INSULATION_TEMPS = {105, 120, 130, 155, 180, 200, 220}

def _is_valid_insulation(val: str) -> bool:
    """유효한 절연 등급 여부 판단 (IEC 60085 기준)."""
    v = val.strip().upper()
    if v in _VALID_INSULATION_CLASS:
        return True
    try:
        return int(v) in _VALID_INSULATION_TEMPS
    except ValueError:
        return False


# ══════════════════════════════════════════════════════════════════════
#  클러스터 구조화 출력 — records → LLM 컨텍스트 텍스트
# ══════════════════════════════════════════════════════════════════════

# ── parameter → 한국어 표시명 ─────────────────────────────────────────
_PARAM_LABELS: dict = {
    # PERFORMANCE (Pump)
    "flow_rate":          "유량",
    "head_m":             "양정",
    "discharge_pressure": "토출압",
    "npsh_required_m":    "NPSH",
    # MOTOR
    "motor_kw":           "출력",
    "motor_rpm":          "RPM",
    "motor_voltage_V":    "모터전압",
    "motor_poles":        "극수",
    "insulation_class":   "절연등급",
    "ip_rating":          "보호등급",
    "bearing_no":         "베어링번호",
    "grease_type":        "그리스",
    "ip_rating":          "IP등급",
    # BEARING
    "bearing_no":         "베어링번호",
    "bearing_lifetime_h": "베어링수명",
    # LUBRICATION
    "grease_type":        "그리스",
    # SEAL
    "seal_type":          "씰타입",
    # MECHANICAL
    "coupling_type":      "커플링",
    # FAN (전압=모터전압과 충돌 방지 → 전체압으로 표기)
    "air_flow_m3h":       "풍량",
    "static_pressure":    "정압",
    "total_pressure":     "전체압",
    "fan_type":           "팬타입",
}

# ── section → (한국어 라벨, 출력 순서) ────────────────────────────────
_SECTION_ORDER = ["PERFORMANCE", "FAN", "MOTOR", "BEARING", "LUBRICATION", "SEAL", "MECHANICAL"]
_SECTION_KR: dict = {
    "PERFORMANCE": "펌프 성능",
    "FAN":         "팬",
    "MOTOR":       "모터",
    "BEARING":     "베어링",
    "LUBRICATION": "윤활",
    "SEAL":        "씰",
    "MECHANICAL":  "기계 사양",
}

# ── 관계 추론 규칙 (섹션 집합 → 한국어 설명) ──────────────────────────
_RELATION_RULES: list = [
    (frozenset({"MOTOR", "PERFORMANCE"}), "모터 → 펌프 구동"),
    (frozenset({"MOTOR", "FAN"}),         "모터 → 팬 구동"),
    (frozenset({"BEARING", "MOTOR"}),     "베어링 → 모터/펌프 적용"),
]

def _infer_relations(present_sections: set) -> list:
    return [desc for rule_set, desc in _RELATION_RULES if rule_set.issubset(present_sections)]


# ── 장비 유형 추론 (tag 접두사 우선 → records 파라미터 보조) ──────────────
_TAG_PREFIX_MAP = [
    (re.compile(r'^P\d',  re.IGNORECASE), "PUMP"),
    (re.compile(r'^CP\d', re.IGNORECASE), "PUMP"),   # circulation pump
    (re.compile(r'^H\d',  re.IGNORECASE), "FAN"),
    (re.compile(r'^BL',   re.IGNORECASE), "FAN"),    # blower
    (re.compile(r'^M\d',  re.IGNORECASE), "MOTOR"),
    (re.compile(r'^C\d',  re.IGNORECASE), "COMPRESSOR"),
    (re.compile(r'^V[PB]',re.IGNORECASE), "VALVE_PACKAGE"),
]
_PARAM_TYPE_SIGNALS: list = [
    ({"flow_rate", "head_m", "npsh_required_m"}, "PUMP"),
    ({"air_flow_m3h", "static_pressure", "fan_type"}, "FAN"),
    ({"motor_kw", "motor_rpm"}, "MOTOR"),
]

def _infer_equipment_type(tag: str, records: list) -> str:
    """
    tag + records 기반 장비 유형 추론.
    반환: "PUMP" / "FAN" / "MOTOR" / "COMPRESSOR" / "VALVE_PACKAGE" / "UNKNOWN"
    1차: 태그 접두사 패턴 매칭 (P0→PUMP, H0→FAN 등)
    2차: records 파라미터 집합으로 보조 판별
    """
    for pattern, equip_type in _TAG_PREFIX_MAP:
        if pattern.match(tag):
            return equip_type
    # 태그 매칭 실패 시 파라미터로 판별
    params = {r.get("parameter") for r in records}
    for signal_set, equip_type in _PARAM_TYPE_SIGNALS:
        if signal_set & params:
            return equip_type
    return "UNKNOWN"


def _format_cluster_text(tag: str, meta: dict, records: list) -> str:
    """
    records → 설비 클러스터 구조화 텍스트.
    LLM 컨텍스트 주입용. flat records가 아닌 설비 시스템 구조로 표현.
    """
    src_file  = meta.get("file", "")
    equip_type = _infer_equipment_type(tag, records)
    type_label = {
        "PUMP":          "원심펌프",
        "FAN":           "팬/송풍기",
        "MOTOR":         "전동기",
        "COMPRESSOR":    "압축기",
        "VALVE_PACKAGE": "밸브패키지",
        "UNKNOWN":       "미분류",
    }.get(equip_type, equip_type)
    lines = [f"[설비: {tag}] 유형: {type_label} ({src_file})"]

    # ── 섹션별 그룹핑 + 노이즈 필터 ─────────────────────────────────
    sections: dict = {}
    for r in records:
        param, val = r.get("parameter", ""), r.get("value", "")
        if param == "grease_type"      and not _is_valid_grease(val):     continue
        if param == "insulation_class" and not _is_valid_insulation(val): continue
        sec = r.get("section", "기타")
        sections.setdefault(sec, []).append(r)

    # ── 섹션 순서대로 출력 ────────────────────────────────────────────
    ordered = _SECTION_ORDER + [s for s in sections if s not in _SECTION_ORDER]
    for sec in ordered:
        recs = sections.get(sec)
        if not recs:
            continue
        sec_label = _SECTION_KR.get(sec, sec)
        lines.append(f"\n{sec_label}:")

        seen: set = set()   # (parameter, position) 중복 제거
        for r in recs:
            param = r.get("parameter", "")
            pos   = r.get("position")
            key   = (param, pos)
            if key in seen:
                continue
            seen.add(key)

            label = _PARAM_LABELS.get(param, param)
            pos_str  = f" ({pos})" if pos else ""
            unit_str = f" {r['unit']}" if r.get("unit") else ""
            lines.append(f"  - {label}{pos_str}: {r['value']}{unit_str}")

    # ── 관계 추론 ─────────────────────────────────────────────────────
    relations = _infer_relations(set(sections.keys()))
    if relations:
        lines.append("\n구성 관계:")
        for rel in relations:
            lines.append(f"  - {rel}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  질문 의도 분류 (rule-based, API 0원)
# ══════════════════════════════════════════════════════════════════════

_INTENT_MAINT    = ["베어링", "bearing", "그리스", "grease", "씰", "seal",
                    "정비", "교체", "점검", "수명", "절연", "윤활"]
_INTENT_RELATION = ["연결", "구동", "무슨 모터", "어떤 모터", "구성", "어떻게 연결",
                    "drives", "연결된", "같이"]
_INTENT_SPEC     = ["유량", "flow", "rpm", "압력", "pressure", "kw", "출력",
                    "전압", "극수", "양정", "npsh", "풍량", "속도", "얼마"]

def classify_query(query: str) -> str:
    """질문 의도 분류: MAINT > RELATION > SPEC > GENERAL (우선순위 순)."""
    q = query.lower()
    if any(k in q for k in _INTENT_MAINT):    return "MAINT"
    if any(k in q for k in _INTENT_RELATION): return "RELATION"
    if any(k in q for k in _INTENT_SPEC):     return "SPEC"
    return "GENERAL"

# 의도별 컨텍스트 힌트 (LLM에 전달되는 텍스트 앞에 주입)
_INTENT_HINT: dict = {
    "SPEC":     "※ [수치/사양 질문] 해당 값을 단위와 함께 간결하게 답하세요.",
    "RELATION": "※ [구성/관계 질문] 설비 간 구성 관계를 중심으로 설명하세요.",
    "MAINT": (
        "※ [정비/부품 질문] 아래 순서로 답하세요:\n"
        "  1) 해당 부품 사양 (베어링번호·그리스 종류·씰 타입·절연등급 등 데이터시트 값)\n"
        "  2) 정비 판단 기준 — 설계값과 현재 증상을 비교하여 이상 여부 판단\n"
        "     예) RPM 저하: 설계 motor_rpm vs 실측값 비교 -> 모터 결함 or 기계 저항 증가\n"
        "     예) 베어링 과열: 절연등급(허용온도) 초과 여부, 그리스 유지 주기 확인\n"
        "     예) 유량 감소: 설계 flow_rate vs 실측 비교 -> 임펠러 마모 or 씰 누설 의심\n"
        "  3) 정비 주의사항 (교체 주기, 취급 주의점)"
    ),
    "GENERAL":  "",
}


def _tag_matches(tag: str, q_lower: str) -> bool:
    """태그 매칭: 'P0-0402A/B' → 'p0-0402' 포함 여부도 인정."""
    tag_lower = tag.lower()
    if tag_lower in q_lower:
        return True
    # A/B 접미 제거: P0-0402A/B → P0-0402
    base = re.sub(r'[a-z]/[ab]$', '', tag_lower)   # P0-0402a/b → P0-0402
    base = re.sub(r'[ab]$', '', base).rstrip('-_')  # P0-0402a  → P0-0402
    return bool(base) and base in q_lower


def _search_pdf_structured(q_lower: str) -> str:
    """
    pdf_structured JSON → 태그 매칭 → 클러스터 구조화 텍스트 반환.
    태그 미감지(UNKNOWN) 및 records=[] 파일은 건너뜀.
    """
    data_list = _load_pdf_structured()
    if not data_list:
        return ""

    parts = []
    for data in data_list:
        tag = data.get("tag", "UNKNOWN")
        if tag == "UNKNOWN":
            continue
        records = data.get("records", [])
        if not records:
            continue
        # 1차: 태그 직접 매칭
        matched = _tag_matches(tag, q_lower)
        # 2차: service / service_aliases 매칭 (서비스 명칭 기반 검색)
        if not matched:
            meta = data.get("meta", {})
            service = (meta.get("service") or "").lower()
            aliases = [a.lower() for a in meta.get("service_aliases", [])]
            for svc in [service] + aliases:
                if svc and svc in q_lower:
                    matched = True
                    break
        if matched:
            parts.append(_format_cluster_text(tag, data.get("meta", {}), records))

    return "\n\n---\n\n".join(parts) if parts else ""


# ══════════════════════════════════════════════════════════════════════
#  소스 레지스트리 — 새 소스 추가 시 여기에만 한 줄 추가
# ══════════════════════════════════════════════════════════════════════
_SOURCES = [
    ("### 📊 [설비 제원 데이터]", _search_equip_md),
    ("### 📋 [구조화 데이터시트]", _search_pdf_structured),
    ("### 📐 [관련 도면]",        _search_drawing),
    ("### 📖 [운전 매뉴얼]",      _search_manual_chunks),
    # ("### 🔧 [정비 이력]",      _search_maintenance),   ← 향후 추가 예시
    # ("### 📋 [인터락 목록]",    _search_interlock),     ← 향후 추가 예시
]
