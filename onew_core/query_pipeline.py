"""
query_pipeline.py — 온유 Single-Shot Q&A 파이프라인

[철학]
LLM은 출력기. 파이썬이 검색·압축하여 먹여준다.
smolagents ReAct 루프 없음 → 입력 토큰 97% 절감 목표.

[파이프라인]
  1. Alias Normalize   — 변형어 → 정규 표현 (메모리 O(1))
  2. Intent Route      — FACT / SEMANTIC / HYBRID / ACTION
  3. Search Direct     — LanceDB 직접 호출 (MCP subprocess 우회)
  4. Soft Compress     — 트랙별 문장 추출, 최대 1,200자
  5. Fallback          — 형태소 부분 검색 → 역방향 학습 프롬프트
  6. LLM Single-Shot   — 도구 스키마 없이 단 1회 호출

[handle_query 반환값]
  str  → Q&A 답변 (파이프라인 처리 완료)
  None → ACTION 명령 (호출자가 agent.run()으로 처리)
"""

import os
import re
import json
import sqlite3
import logging
import functools
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ── Phase 12.5: MetricsContext (import 실패 시 None, 파이프라인 무중단) ──────
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools.metrics_collector import MetricsContext as _MetricsContext
except Exception:
    _MetricsContext = None

# ── Phase 13-B: Shadow RL (import 실패 시 비활성화, 파이프라인 무중단) ────────
try:
    from tools.shadow_rl_engine import determine_best_action as _rl_determine
    _SHADOW_RL_ON = True
except Exception:
    _SHADOW_RL_ON = False
    def _rl_determine(*a, **kw): return None

# ── Phase 16-B: RL 절대 개입 금지 구역 (Blacklist) ───────────────────────────
# ACTION 명령은 is_action_command()에서 이미 차단됨.
# 아래는 RAG 파이프라인 진입 후에도 RL hint를 거부할 추가 조건.
_RL_BLACKLIST_INTENTS = frozenset({
    "UNKNOWN",          # 검색 결과 없는 쿼리 — RL 학습 데이터 신뢰도 낮음
    "ACTION_DELEGATED", # 이미 agent로 위임된 명령
})

# ── Phase 13-B: 직전 쿼리 메트릭 스냅샷 (session_manager History Guard용) ───
_last_metrics: dict = {}

SYSTEM_DIR    = Path(__file__).parent.parent
LANCE_DB_DIR  = SYSTEM_DIR / ".onew_lance_db"
CONTACTS_DB   = SYSTEM_DIR / "contacts.db"
ENTITIES_MD   = SYSTEM_DIR / "memory" / "entities.md"

_PHONE_RE  = re.compile(r'010-\d{4}-\d{4}')
_TITLE_STR = re.compile(r'(이사|대표|과장|차장|부장|팀장|계장|주임|대리|사원|기사|조장|소장)')


def sync_entities_to_contacts() -> int:
    """memory/entities.md 인물 테이블 → contacts.db upsert.
    Returns: 처리된 인물 수."""
    if not ENTITIES_MD.exists() or not CONTACTS_DB.exists():
        return 0
    try:
        text = ENTITIES_MD.read_text(encoding="utf-8")
        count = 0
        in_person_section = False
        with sqlite3.connect(str(CONTACTS_DB)) as conn:
            for line in text.splitlines():
                line = line.strip()
                # 섹션 헤더 추적 — 인물 섹션만 파싱
                if line.startswith("## "):
                    in_person_section = "인물" in line
                    continue
                if not in_person_section:
                    continue
                if not line.startswith("|") or line.startswith("| 이름") or line.startswith("|---"):
                    continue
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) < 2:
                    continue
                raw_name = cols[0]   # 예: "홍현석 (홍대리, 현석이형)"
                memo     = cols[2] if len(cols) > 2 else ""

                # 이름·별칭 분리
                m = re.match(r'^([^(]+?)(?:\s*\(([^)]+)\))?$', raw_name)
                if not m:
                    continue
                name    = m.group(1).strip()
                aliases = [a.strip() for a in m.group(2).split(",")] if m.group(2) else []
                if not name or len(name) < 2:
                    continue

                # 전화번호 추출
                phones = _PHONE_RE.findall(memo)

                # 직함 추출 (메모에서 첫 번째)
                tm = _TITLE_STR.search(memo)
                title = tm.group(0) if tm else ""

                phones_json  = json.dumps(phones, ensure_ascii=False)
                aliases_json = json.dumps(aliases, ensure_ascii=False)

                existing = conn.execute(
                    "SELECT id FROM contacts WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    conn.execute(
                        """UPDATE contacts
                           SET phones=?, aliases=?, title=?, source='entities_md'
                           WHERE id=?""",
                        (phones_json, aliases_json, title, existing[0])
                    )
                else:
                    conn.execute(
                        """INSERT INTO contacts (name, phones, aliases, title, org, source)
                           VALUES (?, ?, ?, ?, ?, 'entities_md')""",
                        (name, phones_json, aliases_json, title, "")
                    )
                count += 1
        return count
    except Exception as e:
        logger.warning("[sync_entities_to_contacts] 실패: %s", e)
        return 0

# ── W1: 멀티턴 확장용 VAGUE_REFS (session_manager 단일 소스 사용) ──────────
try:
    from onew_core.session_manager import VAGUE_REFS as _VAGUE_REFS
    _VAGUE_REFS_RE = re.compile("|".join(re.escape(v) for v in _VAGUE_REFS))
except Exception:
    _VAGUE_REFS_RE = None

# 인물 질의 감지용 직함 키워드
_TITLE_KW = re.compile(
    r'(이사|대표|과장|차장|부장|팀장|계장|주임|대리|사원|기사|조장|소장|원장|선생|교수)'
)

# ── kiwipiepy (선택적) ─────────────────────────────────────────────────────────
try:
    from kiwipiepy import Kiwi as _Kiwi
    _kiwi = _Kiwi()
    def _tokenize(text: str) -> list[str]:
        return [t.form for t in _kiwi.tokenize(text)
                if t.tag in ('NNG', 'NNP') and len(t.form) >= 2
                and re.fullmatch(r'[가-힣]+', t.form)]
except Exception:
    _kiwi = None
    def _tokenize(text: str) -> list[str]:
        return text.split()


# ══════════════════════════════════════════════════════════════════════════════
# 0. ACTION 명령 분류 (MCP agent 위임 여부 결정)
# ══════════════════════════════════════════════════════════════════════════════

# ── 검색 boost/fallback 전역 상수 (search_direct 내 반복 생성 방지) ──────────
_TITLE_SUFFIX = re.compile(
    r'(이사|대표|과장|차장|부장|팀장|계장|주임|대리|사원|기사|조장|소장)$'
)
_BOOST_STOP: frozenset[str] = frozenset({
    "어떤", "사람", "대해", "알려", "알려줘", "줘", "있어", "없어", "몰라", "뭐야",
    "어디", "언제", "왜", "어떻게", "좀", "싶어", "이야", "하는", "했어",
    "그게", "하고", "이고", "하면", "이라", "이다", "한다", "해줘", "해줘요",
    "사람이야", "이야기", "알고", "싶어요", "인지", "뭔지", "뭔가", "기능",
    "알아", "봐줘", "찾아줘", "설명", "설명해", "설명해줘", "요약", "요약해",
})

_ACTION_RE = re.compile(
    r'(일정|캘린더|추가해|등록해|삭제해|수정해|파일|저장해|만들어|보내|'
    r'클리핑|퀴즈|문제 내|편집|실행(?!하는\s*방법|하는\s*법)|검색해줘(?!.*알려)|설정|'
    r'웹.{0,6}(검색|찾아|조사)|인터넷.{0,6}(검색|찾아)|검색해봐|검색해줘|찾아봐|찾아줘|조사해봐|조사해줘|'
    r'생성해봐|생성해줘|만들어봐|만들어줘|써봐|써줘|작성해봐|작성해줘|'
    r'요청해봐|요청해줘|전달해봐|전달해줘|호출해봐|호출해줘|보내봐|보내줘|'
    r'\d+번\s*문제|기출\s*\d+번|과년도.{0,30}(문제|시행|\d+번)|'
    r'\d{2,4}년도?.{0,6}\d+회차|회차.{0,10}문제|시행.{0,10}문제|'
    r'공조냉동.{0,15}(문제|기출|회차|시행)|'
    r'오늘.{0,6}일기|어제.{0,6}일기|엊그제.{0,6}일기|그저께.{0,6}일기|일기.{0,6}읽어|일기.{0,6}보여|'
    r'오늘.{0,6}내용|어제.{0,6}내용|엊그제.{0,6}내용|그저께.{0,6}내용|'
    r'오늘.{0,6}(뭐|뭘|뭘\s*먹)|어제.{0,6}(뭐|뭘|뭘\s*먹)|엊그제.{0,6}(뭐|뭘|뭘\s*먹)|그저께.{0,6}(뭐|뭘|뭘\s*먹)|'
    r'api.{0,6}(호출|사용|횟수|현황)|사용량.{0,6}(얼마|몇|알려|보여)|'
    r'(오늘|이번달).{0,6}(api|사용량|토큰)|상태\s*보고|report_status)'
)

# 파일 경로 패턴: DAILY/2025-11-26, 2025-11-26.md, 절대경로 등
_PATH_RE = re.compile(
    r'(DAILY[\\/]\d{4}|'            # DAILY/2025-... or DAILY\2025-...
    r'\d{4}-\d{2}-\d{2}\.md|'       # 2025-11-26.md
    r'[A-Za-z]:\\|[A-Za-z]:/Users|' # 절대 윈도우 경로
    r'Processed[\\/]|OCU[\\/]|'     # 기타 Vault 폴더 직접 참조
    r'[가-힣a-zA-Z0-9\.]+_part\d+)' # 03.연기_part2 형식 파일명 참조
)

def is_action_command(query: str) -> bool:
    """MCP 도구 호출이 필요한 액션 명령이면 True."""
    if _ACTION_RE.search(query):
        return True
    # 파일 경로가 포함된 질문 → agent의 read_file 필요
    if _PATH_RE.search(query):
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# 1. Alias Normalize
# ══════════════════════════════════════════════════════════════════════════════

def alias_normalize(query: str) -> str:
    """TerminologyIndex 단일 regex 패스 정규화 (캐스케이딩 없음)."""
    query = _exam_round_normalize(query)
    try:
        from onew_core.terminology_server import get_index
        return get_index().normalize(query)
    except Exception:
        return query


# 공조냉동기계기사 회차 → 시행일 변환 테이블 (2024 공조냉동기계기사 실기 합본 목차 기준)
_EXAM_DATES: dict[tuple[int, int], str] = {
    # 2003~2009 (3회차 체계)
    ( 3, 1): "2003.4.27",  ( 3, 2): "2003.7.13",
    ( 4, 1): "2004.4.25",  ( 4, 2): "2004.9.19",
    ( 5, 1): "2005.5.1",   ( 5, 2): "2005.7.10",  ( 5, 3): "2005.9.25",
    ( 6, 1): "2006.4.23",  ( 6, 2): "2006.7.9",   ( 6, 3): "2006.9.17",
    ( 7, 1): "2007.4.22",  ( 7, 2): "2007.7.8",   ( 7, 3): "2007.10.7",
    ( 8, 1): "2008.4.20",  ( 8, 2): "2008.7.6",   ( 8, 3): "2008.9.28",
    ( 9, 1): "2009.4.19",  ( 9, 2): "2009.7.5",   ( 9, 3): "2009.9.13",
    # 2010~2019
    (10, 1): "2010.4.18",  (10, 2): "2010.7.4",   (10, 3): "2010.9.12",
    (11, 1): "2011.5.1",   (11, 2): "2011.7.24",  (11, 3): "2011.10.16",
    (12, 1): "2012.4.22",  (12, 2): "2012.7.8",   (12, 3): "2012.10.14",
    (13, 1): "2013.4.21",  (13, 2): "2013.7.14",  (13, 3): "2013.10.6",
    (14, 1): "2014.4.20",  (14, 2): "2014.7.6",   (14, 3): "2014.10.5",
    (15, 1): "2015.4.19",  (15, 2): "2015.7.15",  (15, 3): "2015.10.4",
    (16, 1): "2016.4.17",  (16, 2): "2016.6.26",  (16, 3): "2016.10.9",
    (17, 1): "2017.4.16",  (17, 2): "2017.6.25",  (17, 3): "2017.10.14",
    (18, 1): "2018.4.15",  (18, 2): "2018.6.30",  (18, 3): "2018.10.6",
    (19, 1): "2019.4.14",  (19, 2): "2019.6.29",  (19, 3): "2019.10.12",
    # 2020~2025
    (20, 1): "2020.5.24",  (20, 2): "2020.7.25",  (20, 3): "2020.10.17", (20, 4): "2020.11.29",
    (21, 1): "2021.4.24",  (21, 2): "2021.7.10",  (21, 3): "2021.10.16",
    (22, 1): "2022.5.7",   (22, 2): "2022.7.24",  (22, 3): "2022.10.16",
    (23, 1): "2023.4.23",  (23, 2): "2023.8.22",  (23, 3): "2023.10.23",
    (24, 1): "2024.4.27",  (24, 2): "2024.7.13",  (24, 3): "2024.10.19",
    (25, 1): "2025.4.26",  (25, 2): "2025.7.12",  (25, 3): "2025.10.18",
}
_ROUND_RE = re.compile(r'(\d{2,4})년도?\s*(\d)회차')

def _exam_round_normalize(query: str) -> str:
    """'23년 3회차' → '2023년 3회차 과년도 출제문제(2023.10.23 시행)' 확장."""
    m = _ROUND_RE.search(query)
    if not m:
        return query
    yr_raw, rd = int(m.group(1)), int(m.group(2))
    yr2 = yr_raw % 100  # 2023 → 23
    date_str = _EXAM_DATES.get((yr2, rd))
    if not date_str:
        return query
    yr4 = 2000 + yr2
    expanded = f"과년도 출제문제({date_str} 시행)"
    # 원문 회차 표현을 확장 표현으로 교체
    return query[:m.start()] + expanded + query[m.end():]


# ══════════════════════════════════════════════════════════════════════════════
# 2. Intent Router
# ══════════════════════════════════════════════════════════════════════════════

_FACT_KW     = {"언제", "어디", "누구", "원인", "시간", "날짜", "몇", "얼마", "몇번"}
_SEMANTIC_KW = {"어떤", "평가", "요약", "분석", "느낌", "어땠", "왜", "설명", "뭐야", "알려"}

def classify_intent(query: str) -> str:
    """FACT / SEMANTIC / HYBRID 분류. 기본값 SEMANTIC."""
    is_fact     = any(k in query for k in _FACT_KW)
    is_semantic = any(k in query for k in _SEMANTIC_KW)
    if is_fact and is_semantic:
        return "HYBRID"
    if is_fact:
        return "FACT"
    return "SEMANTIC"   # 대부분의 자연어 질문은 SEMANTIC


# ══════════════════════════════════════════════════════════════════════════════
# 3. Direct Search (LanceDB + BM25, MCP 우회)
# ══════════════════════════════════════════════════════════════════════════════

def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            key, _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
            winreg.CloseKey(k)
        except Exception:
            pass
    return key


@functools.lru_cache(maxsize=128)
def _embed_cached(text: str) -> tuple[float, ...]:
    """Gemini embedding-001 직접 호출 (LRU 캐시 128개). tuple 반환으로 mutable 방어."""
    api_key = _get_api_key()
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-embedding-001:embedContent?key={api_key}")
    body = json.dumps({
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_QUERY",
    }).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return tuple(json.loads(r.read())["embedding"]["values"])


def _embed(text: str) -> list[float]:
    """캐시 래퍼. 기존 호출부 인터페이스(list[float]) 유지."""
    return list(_embed_cached(text))


# ── W5: LanceDB 연결 싱글톤 캐시 ─────────────────────────────────────────────
_lance_db_cache: dict = {}   # {"conn": db_obj, "path": str}

_JOSA_STRIP = re.compile(r'(님|은|는|이|가|을|를|의|도|에|와|과|로|으로|에서|부터|한테|께)$')


def _query_surface_tokens(query: str) -> list[str]:
    """
    공백 분리 + 조사 제거로 원형 토큰 추출.
    kiwipiepy가 분리하지 못하는 '홍대리' 같은 합성 고유명사 보완용.
    """
    tokens = []
    for tok in query.split():
        t = re.sub(r'[^가-힣a-zA-Z0-9\-]', '', tok)
        t = _JOSA_STRIP.sub('', t)
        t = re.sub(r'님$', '', t)
        if len(t) >= 2:
            tokens.append(t)
    return tokens


def search_direct(query: str, limit: int = 20) -> list[dict]:
    """
    LanceDB 직접 검색 + BM25 재순위 + 표면 토큰 직접 매칭 부스트.

    부스트 로직:
      - 공백 기반 원형 토큰('홍대리' 등)이 청크 텍스트에 직접 포함되면 +0.25
      - kiwipiepy가 분리해버리는 고유명사 누락 방지

    Returns: [{text, path, score}, ...]
    """
    try:
        import lancedb
        from rank_bm25 import BM25Okapi

        if not LANCE_DB_DIR.exists():
            logger.warning("[search_direct] LanceDB 없음: %s", LANCE_DB_DIR)
            return []

        q_emb          = _embed(query)
        surface_tokens = _query_surface_tokens(query)   # 직접 매칭용 원형 토큰

        # W5: 싱글톤 캐시 (매 쿼리마다 connect() 비용 제거)
        _db_path = str(LANCE_DB_DIR)
        if _lance_db_cache.get("path") != _db_path or _lance_db_cache.get("conn") is None:
            _lance_db_cache["conn"]  = lancedb.connect(_db_path)
            _lance_db_cache["path"] = _db_path
        db   = _lance_db_cache["conn"]
        tbls = db.table_names() if hasattr(db, "table_names") else [str(t) for t in db.list_tables()]
        if "chunks" not in tbls:
            return []

        candidates = db.open_table("chunks").search(q_emb).metric("cosine").limit(limit * 2).to_list()
        if not candidates:
            return []

        texts    = [r["text"] for r in candidates]
        bm25     = BM25Okapi([_tokenize(t) for t in texts])
        bm25_raw = bm25.get_scores(_tokenize(query))
        bm25_max = max(bm25_raw) or 1

        # ── 토큰 분류: 이름 vs 일반 핵심 명사 ──────────────────────────────────
        # name_tokens  : 이름+직함 합성어 ("홍대리","정대리") → 강한 boost +0.40
        # general_tokens: 전문 용어·일반 명사 ("감온기","보일러") → 약한 boost +0.18
        # _TITLE_SUFFIX, _BOOST_STOP 는 모듈 상단 전역 상수 사용
        name_tokens    = [t for t in surface_tokens if _TITLE_SUFFIX.search(t) and len(t) >= 3]
        general_tokens = [t for t in surface_tokens
                          if len(t) >= 2 and t not in _BOOST_STOP and t not in name_tokens]

        results = []
        for i, r in enumerate(candidates):
            vec   = max(0.0, 1.0 - r.get("_distance", 1.0))
            score = vec * 0.7 + (bm25_raw[i] / bm25_max) * 0.3

            text = r["text"]
            # 인물/직급 토큰 → 강한 boost (+0.40)
            if name_tokens and any(tok in text for tok in name_tokens):
                score += 0.40
            # 일반 핵심 명사("감온기" 등) → 중간 boost (+0.18)
            # name_tokens 매칭과 독립 적용 (전문 용어 쿼리 정확도 보존)
            if general_tokens and any(tok in text for tok in general_tokens):
                score += 0.18

            if score >= 0.15:
                results.append({
                    "text":  text,
                    "path":  r.get("path", ""),
                    "score": round(min(score, 1.0), 4),
                })

        results.sort(key=lambda x: x["score"], reverse=True)

        # ── path 기반 중복 dedup: 같은 파일에서 최고점 청크 1개만 유지 ─────────
        # 단, score 상위 3개는 dedup 면제 (핵심 청크 보존)
        _seen_paths: dict[str, float] = {}
        _deduped = []
        for idx, r in enumerate(results):
            p = r["path"]
            if idx < 3 or not p:
                _deduped.append(r)
                _seen_paths[p] = r["score"]
            elif p not in _seen_paths:
                _deduped.append(r)
                _seen_paths[p] = r["score"]
            # 같은 path라도 점수 차이가 0.2 이상이면 추가 허용 (다른 내용일 가능성)
            elif r["score"] >= _seen_paths[p] - 0.20:
                pass  # 스킵
        results = _deduped[:limit]

        # ── WHERE LIKE fallback (이름 + 일반 명사 모두) ───────────────────────
        # 벡터 top-5에 없는 토큰을 문자열 직접 검색으로 보완.
        # name_tokens → 점수 0.82 (정확한 인물 매칭 우선)
        # general_tokens → 점수 0.70 (전문 용어도 구명줄 확보)
        fallback_tasks: list[tuple[str, float]] = []
        missing_general: list[str] = []   # synonym enqueue 추적용

        if name_tokens:
            top5_text = " ".join(r["text"] for r in results[:5])
            missing_names = [t for t in name_tokens if t not in top5_text]
            for tok in missing_names:
                fallback_tasks.append((tok, 0.82))

        if general_tokens:
            top5_text = " ".join(r["text"] for r in results[:5])
            missing_general = [t for t in general_tokens if t not in top5_text]
            for tok in missing_general[:3]:   # 일반 명사는 최대 3개만 (성능)
                fallback_tasks.append((tok, 0.70))

        if fallback_tasks:
            _general_tok_set = set(missing_general)
            _synonym_hits: dict[str, list[str]] = {}   # tok → [doc_paths]
            try:
                tbl = db.open_table("chunks")
                for tok, fb_score in fallback_tasks:
                    try:
                        direct_hits = (
                            tbl.search()
                            .where(f"text LIKE '%{tok}%'", prefilter=True)
                            .limit(5)
                            .to_list()
                        )
                        for h in direct_hits:
                            results.append({
                                "text":  h["text"],
                                "path":  h.get("path", ""),
                                "score": round(fb_score, 4),
                            })
                        # general_tokens 히트 → synonym 후보 수집 (name_tokens 제외)
                        if direct_hits and tok in _general_tok_set:
                            _synonym_hits[tok] = [
                                h.get("path", "") for h in direct_hits if h.get("path")
                            ]
                    except Exception:
                        pass
            except Exception:
                pass

            # synonym 후보 비동기 투입 (검색 응답 블로킹 없음)
            if _synonym_hits:
                try:
                    from onew_core.synonym_filter import enqueue_candidate as _enq
                    import threading
                    def _enqueue_batch(_hits=_synonym_hits):
                        for _tok, _paths in _hits.items():
                            _enq(_tok, source_hashes=_paths, count=1)
                    threading.Thread(target=_enqueue_batch, daemon=True).start()
                except Exception:
                    pass

            results.sort(key=lambda x: x["score"], reverse=True)
            # 중복 제거 (text 앞 80자 기준)
            seen_texts: set[str] = set()
            deduped = []
            for r in results:
                key = r["text"][:80]
                if key not in seen_texts:
                    seen_texts.add(key)
                    deduped.append(r)
            results = deduped

        return results[:limit]

    except Exception as e:
        logger.warning("[search_direct] %s", e)
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 4. Soft Compress (트랙별 문장 추출)
# ══════════════════════════════════════════════════════════════════════════════

_EVAL_KW = {"좋", "나쁘", "문제", "잘", "별로", "훌륭", "아쉽", "개선",
            "위험", "중요", "실패", "성공", "오류", "에러"}


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 5]


def _compress_fact(chunks: list[dict], query: str, max_chars: int = 1200) -> str:
    keywords = set(_tokenize(query))
    out = []
    for chunk in chunks:
        sents = _split_sentences(chunk["text"])
        for i, s in enumerate(sents):
            if any(k in s for k in keywords):
                ctx = sents[max(0, i - 1): i + 2]
                out.extend(ctx)
    return "\n".join(dict.fromkeys(out))[:max_chars]


def _compress_semantic(chunks: list[dict], query: str, max_chars: int = 1500) -> str:
    query_kw = set(_tokenize(query))
    out = []
    for chunk in chunks:
        sents = _split_sentences(chunk["text"])
        for s in sents:
            if any(k in s for k in query_kw) or any(k in s for k in _EVAL_KW):
                out.append(s)
    return "\n".join(dict.fromkeys(out))[:max_chars]


def compress_context(intent: str, chunks: list[dict], query: str) -> str:
    """의도에 따라 청크를 압축. 결과 최대 ~1,400자 (≈350 토큰)."""
    if not chunks:
        return ""

    if intent == "FACT":
        ctx = _compress_fact(chunks, query)
    elif intent == "SEMANTIC":
        ctx = _compress_semantic(chunks, query)
    else:  # HYBRID
        fact = _compress_fact(chunks, query, 600)
        sem  = _compress_semantic(chunks, query, 800)
        combined = fact + "\n" + sem
        ctx = "\n".join(dict.fromkeys(combined.split("\n")))[:1400]

    # 압축 결과가 빈 경우 → 상위 3개 청크 원문 앞부분
    if not ctx.strip():
        ctx = "\n\n".join(c["text"][:400] for c in chunks[:3])

    return ctx


def compress_context_temporal(chunks: list[dict], query: str,
                               max_chars: int = 1600) -> str:
    """
    Temporal 쿼리 전용 압축.
    날짜별로 청크를 묶어 [YYYY-MM-DD] 헤더를 붙여 LLM에 전달.
    → LLM이 날짜 순서를 인식하여 시간순 답변 가능.

    chunks는 temporal_rerank 이후 이미 날짜 정렬되어 있다고 가정.
    """
    from collections import defaultdict

    # 날짜 → 텍스트 목록으로 그루핑
    date_groups: dict[str, list[str]] = defaultdict(list)
    no_date: list[str] = []

    keywords = set(_tokenize(query))

    for chunk in chunks:
        path = chunk.get("path", "")
        date_obj = _extract_date_from_path(path)
        text = chunk.get("text", "")

        # 키워드 관련 문장 우선, 없으면 앞 200자
        sents = _split_sentences(text)
        relevant = [s for s in sents if any(k in s for k in keywords)]
        excerpt = "\n".join(relevant[:3]) if relevant else text[:200]

        if date_obj:
            date_groups[date_obj.strftime("%Y-%m-%d")].append(excerpt)
        else:
            no_date.append(excerpt)

    # 날짜 오름차순 정렬 (시간순 제공)
    lines: list[str] = []
    for date_str in sorted(date_groups.keys()):
        block = " / ".join(dict.fromkeys(date_groups[date_str]))[:300]
        lines.append(f"[{date_str}] {block}")

    if no_date:
        lines.append("[날짜미상] " + " / ".join(no_date)[:200])

    return "\n".join(lines)[:max_chars]


# ══════════════════════════════════════════════════════════════════════════════
# 5. Fallback
# ══════════════════════════════════════════════════════════════════════════════

_UNKNOWN_TEMPLATE = (
    "'{query}' 관련 정보를 Vault에서 찾지 못했습니다.\n\n"
    "혹시 이 표현이 특정 인물·장비·사건을 뜻한다면 알려주세요.\n"
    "(예: '이차장' → 이정철,  'TO-101' → 냉각탑 1호기)\n"
    "저장해두면 다음부터 바로 찾을 수 있어요."
)


def fallback_search(query: str) -> list[dict]:
    """형태소로 쪼개어 부분 키워드로 재검색."""
    try:
        tokens = _tokenize(query)
        partial = " ".join(tokens[:3]) if tokens else " ".join(query.split()[:2])
        return search_direct(partial) if partial.strip() else []
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 6. Safety & Analysis Guards
# ══════════════════════════════════════════════════════════════════════════════

# Task 2: Soft Replacement — 단정적 인과 표현 → 가능성 표현 (전체 차단 금지)
_SOFTEN_MAP: list[tuple[str, str]] = [
    ("때문입니다",    "와 관련이 있을 수 있습니다"),
    ("원인입니다",    "원인 중 하나일 수 있습니다"),
    ("확실히",        "비교적"),
    ("틀림없이",      "아마도"),
    ("명확합니다",    "보입니다"),
]

def soften_response(text: str) -> str:
    """단정적 인과 표현을 소프트 치환. 응답 전체를 날리지 않음."""
    for old, new in _SOFTEN_MAP:
        text = text.replace(old, new)
    return text


# Task 3: Narrow Medical Gate — 의료 결정 요구 쿼리만 감지
# "건강 기준", "소방 건강", "수면제 먹었다" 같은 단순 언급은 False
_MEDICAL_ADVICE_RE = re.compile(
    r'(약\s*먹어야|병원\s*가야|진단\s*받아야|처방\s*받아야|'
    r'수술\s*해야|치료\s*해야|검사\s*받아야|'
    r'이거\s*약\s*때문|이\s*증상\s*(뭐|뭔|어떤))'
)
_MEDICAL_NOTE = "[참고: 아래 내용은 일기 기록 기반 정보입니다. 의료적 판단은 전문가와 상담하세요]\n\n"

def is_medical_decision_query(query: str) -> bool:
    """의료 판단/결정 요구 쿼리 감지. 단순 기록 언급은 False."""
    return bool(_MEDICAL_ADVICE_RE.search(query))


# Task 4: Analysis Intent Routing — 패턴/원인 분석 쿼리 감지
_ANALYSIS_RE = re.compile(
    r'(패턴이|왜\s*이래|왜\s*요즘|요즘\s*왜|컨디션\s*(어때|뭐야|왜)|'
    r'이상한\s*거|분석해\s*줘|원인이\s*뭐|어떤\s*패턴|'
    r'습관이\s*(뭐|어때)|경향이|어떤\s*경향|내\s*패턴)'
)
_ANALYSIS_SYSTEM_ADDENDUM = (
    "\n\n[분석 응답 원칙]\n"
    "1. 인과관계 단정 금지 — 'A 때문에 B' 대신 'A 시기에 B가 관찰됨' 형태로 표현\n"
    "2. 가능한 관점 2~3가지 제시 (강요 금지, 선택지 형태)\n"
    "3. 확신 표현 사용 금지\n"
    "\n[출력 형식]\n"
    "1. 관찰된 흐름 (패턴 통계 + 최근 기록 근거)\n"
    "2. 가능한 해석 2~3가지\n"
    "3. 결론 없음 — 선택은 사용자에게"
)

# ── Pattern RAG Context 로더 ─────────────────────────────────────────────────
import json as _json
_PATTERN_JSON  = SYSTEM_DIR / "patterns" / "diary_patterns.json"
_pattern_cache: dict = {}      # {mtime: float, summary: str}

def _load_pattern_summary() -> str:
    """patterns/diary_patterns.json → LLM 친화적 요약 문자열.
    mtime 기반 캐시 (파일 변경 없으면 재파싱 불필요).
    """
    global _pattern_cache
    if not _PATTERN_JSON.exists():
        return ""
    mtime = _PATTERN_JSON.stat().st_mtime
    if _pattern_cache.get("mtime") == mtime:
        return _pattern_cache["summary"]

    try:
        data = _json.loads(_PATTERN_JSON.read_text(encoding="utf-8"))
    except Exception:
        return ""

    meta      = data.get("meta", {})
    mood      = data.get("mood", {})
    activity  = data.get("activity", {})
    delta     = data.get("delta", {})

    lines = [
        f"[패턴 통계 — 최근 {meta.get('period_days', '?')}일, "
        f"{meta.get('total_files', '?')}개 일기 기준]"
    ]

    # 감정 상위 3개
    top_mood = sorted(mood.items(), key=lambda x: x[1]["total"], reverse=True)[:3]
    if top_mood:
        mood_strs = [f"{n} {s['frequency_pct']}% 일수" for n, s in top_mood]
        lines.append("감정: " + " / ".join(mood_strs))

    # 활동 상위 3개
    top_act = sorted(activity.items(), key=lambda x: x[1]["total"], reverse=True)[:3]
    if top_act:
        act_strs = [f"{n} {s['frequency_pct']}% 일수" for n, s in top_act]
        lines.append("활동: " + " / ".join(act_strs))

    # 최근 7일 변화 (delta 있는 것만)
    sig_delta = [(n, d) for n, d in delta.items() if abs(d["delta"]) > 0.1]
    sig_delta.sort(key=lambda x: abs(x[1]["delta"]), reverse=True)
    if sig_delta[:3]:
        d_strs = [f"{n} {d['direction']}({d['delta']:+.1f})" for n, d in sig_delta[:3]]
        lines.append("최근 7일 변화: " + " / ".join(d_strs))

    summary = "\n".join(lines)
    _pattern_cache = {"mtime": mtime, "summary": summary}
    return summary

def is_analysis_query(query: str) -> bool:
    """패턴/원인 분석 요구 쿼리 감지. 일반 정보 질문은 False."""
    return bool(_ANALYSIS_RE.search(query))


# Task 5: Sort/Chronological Intent — "정리/요약" 시 시간순 정렬 지시
_SORT_RE = re.compile(
    r'(정리해\s*줘|정리해줘|정리\s*좀|요약해\s*줘|요약해줘|순서대로|'
    r'시간\s*순|날짜\s*순|언제부터\s*언제까지|흐름을|흐름\s*알려|변화\s*알려)'
)
_SORT_SYSTEM_ADDENDUM = (
    "\n\n[시간순 정렬 원칙]\n"
    "컨텍스트에 날짜 헤더([YYYY-MM-DD])가 있으면 반드시 날짜 오름차순으로 정보를 배열한다.\n"
    "날짜 헤더가 없는 항목은 마지막에 배치한다.\n"
    "날짜 범위가 명확하면 '~부터 ~까지' 형태로 시작과 끝을 명시한다."
)

def is_sort_query(query: str) -> bool:
    """시간순 정렬/요약 요구 쿼리 감지."""
    return bool(_SORT_RE.search(query))


# ══════════════════════════════════════════════════════════════════════════════
# 6.5 Option-B: LLM Micro-Router (3-Tier Hybrid)
# ══════════════════════════════════════════════════════════════════════════════
# Tier 1: _ACTION_RE 명확 히트 → ACTION (기존)
# Tier 2: _AMBIGUOUS_PERSONAL_RE 미해당 → SEARCH (기존 파이프라인)
# Tier 3: _AMBIGUOUS_PERSONAL_RE 해당 → LLM 1회 호출(~3 토큰) → ACTION or SEARCH
#
# [비용] gemini-2.0-flash-lite 기준 ~60 input + 3 output ≈ $0.000000045/건
# [충돌] circular import 없음 — litellm 직접 호출, obsidian_agent 미사용
# [실패] 예외 발생 시 False 반환 → Single-Shot 파이프라인 계속 (안전 fallback)

# 개인 활동 + 시간 표현이 겹치는 "회색 지대" 쿼리 탐지
_AMBIGUOUS_PERSONAL_RE = re.compile(
    r'(오늘|어제|그저께|엊그제|이번\s*주|최근|요즘|지난번|저번).{0,25}'
    r'(먹|마셨|마셔|먹었|드셨|갔어|갔나|갔지|했어|했나|했지|했냐|'
    r'뭐\s*해|뭐\s*했|뭐\s*드|뭐\s*봤|뭐\s*입|어디\s*갔|어떻게\s*했)'
    r'|'
    r'(뭘|뭐를|무엇을).{0,20}(먹었|마셨|했어|했나|했지|갔어|갔나|입었|봤어)',
    re.UNICODE
)

_MICRO_ROUTER_PROMPT = (
    "다음 질문이 (A) 파일을 직접 열어 읽어야 하는 액션 명령인지, "
    "(B) 검색으로 답할 수 있는 일반 질문인지 판단해.\n"
    "질문: \"{query}\"\n"
    "반드시 A 또는 B 한 글자만 답해. 다른 말 금지."
)


def _llm_route(query: str) -> bool:
    """
    LLM 마이크로 라우터.
    Returns True → ACTION (agent 위임), False → SEARCH (파이프라인 계속)
    실패 시 False (안전 fallback: SEARCH로 처리)
    """
    try:
        from litellm import completion as _completion
        prompt = _MICRO_ROUTER_PROMPT.format(query=query)
        resp = _completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=3,
        )
        if not resp.choices:
            logger.warning("[MicroRouter] choices 비어있음, SEARCH fallback")
            return False
        answer = resp.choices[0].message.content.strip().upper()
        is_action = answer.startswith("A")
        logger.info("[MicroRouter] query=%r → %s", query[:40], "ACTION" if is_action else "SEARCH")
        return is_action
    except Exception as e:
        logger.warning("[MicroRouter] 실패, SEARCH fallback: %s", e)
        return False


# ══════════════════════════════════════════════════════════════════════════════
# 7. LLM Single-Shot
# ══════════════════════════════════════════════════════════════════════════════

def llm_single_shot(
    context: str,
    query: str,
    system_prompt: str,
    history: list[dict] | None = None,
    model: str = "gemini/gemini-2.5-flash",
) -> str:
    """
    도구 스키마 없이 LiteLLM 단 1회 호출.
    history: [{"role": "user"|"assistant", "content": str}, ...]  최근 N턴
    """
    import litellm
    from litellm import completion

    # 시스템 프롬프트 + 검색 컨텍스트
    sys_content = system_prompt
    if context:
        sys_content += f"\n\n[Vault 검색 결과 — 아래 내용을 근거로 답변]\n{context}"

    messages: list[dict] = [{"role": "system", "content": sys_content}]

    # 최근 대화 히스토리 (컨텍스트 유지, 최대 6턴)
    if history:
        for h in history[-6:]:
            role = "assistant" if h.get("role") in ("model", "assistant") else "user"
            messages.append({"role": role, "content": h.get("text", h.get("content", ""))})

    messages.append({"role": "user", "content": query})

    try:
        resp = completion(model=model, messages=messages, temperature=0.7)
        if not resp.choices:
            logger.error("[llm] choices 비어있음 (safety block 또는 빈 응답)")
            return "[오류] 응답이 차단되었습니다. 다시 시도해주세요."
        return resp.choices[0].message.content.strip()
    except litellm.AuthenticationError:
        logger.error("[llm] API 키 오류")
        return "[오류] Gemini API 키를 확인해주세요."
    except litellm.RateLimitError:
        logger.warning("[llm] Rate limit 초과")
        return "[오류] API 요청 한도 초과. 잠시 후 다시 시도해주세요."
    except litellm.Timeout:
        logger.warning("[llm] 응답 시간 초과")
        return "[오류] 응답 시간 초과. 네트워크를 확인해주세요."
    except Exception as e:
        logger.error("[llm] 호출 실패: %s", e)
        return f"[오류] 답변 생성 실패 ({type(e).__name__}). 잠시 후 다시 시도해주세요."


# ══════════════════════════════════════════════════════════════════════════════
# Profile Injection — contacts.db 인물 프로필 조회
# ══════════════════════════════════════════════════════════════════════════════

def _extract_name_candidates(query: str) -> list[str]:
    """
    쿼리에서 인물 이름 후보 추출.
    - 직함 바로 앞 한글 단어 (최우선)
    - 공백 분리 2~5자 한글 토큰 (kiwipiepy가 이름을 쪼개는 문제 보완)
    - 형태소 2~4자 한글 토큰 (보조)
    """
    candidates: list[str] = []

    # 1. 직함 앞 이름: "이정철 차장" → "이정철"
    for m in _TITLE_KW.finditer(query):
        before = query[:m.start()].strip()
        nm = re.search(r'([가-힣]{2,5})$', before)
        if nm:
            candidates.append(nm.group(1))

    # 2. 공백 기준 2~5자 순수 한글 토큰 (형태소 분리 전 전체 단어)
    # 조사/어미 제거: 는/은/이/가/을/를/의/도/에/와/과/로/으로/에서/부터
    _JOSA = re.compile(r'(은|는|이|가|을|를|의|도|에|와|과|로|으로|에서|부터|한테|께|님)$')
    for tok in query.split():
        tok = re.sub(r'[^가-힣]', '', tok)    # 비한글 제거
        tok = _JOSA.sub('', tok)               # 조사 제거 (는/은/이/가... )
        tok = re.sub(r'님$', '', tok)          # 존칭 님 제거 (조사 제거 후)
        if 2 <= len(tok) <= 5 and tok not in candidates:
            candidates.append(tok)

    # 3. 형태소 토큰 (위에서 못 잡은 것 보완)
    for tok in _tokenize(query):
        if 2 <= len(tok) <= 4 and re.fullmatch(r'[가-힣]+', tok):
            if tok not in candidates:
                candidates.append(tok)

    return candidates


def search_contacts(query: str) -> str:
    """
    contacts.db에서 인물 정보 조회 → 프로필 텍스트 반환.
    결과 없으면 빈 문자열.
    """
    if not CONTACTS_DB.exists():
        return ""

    candidates = _extract_name_candidates(query)
    if not candidates:
        return ""

    try:
        conn = sqlite3.connect(str(CONTACTS_DB))
        conn.row_factory = sqlite3.Row
        found: list[sqlite3.Row] = []
        seen_ids: set[int] = set()

        for name in candidates:
            rows = conn.execute(
                """SELECT id, name, phones, aliases, title, org, last_seen
                   FROM contacts
                   WHERE name LIKE ? OR aliases LIKE ?
                   LIMIT 5""",
                (f"%{name}%", f"%{name}%"),
            ).fetchall()
            for r in rows:
                if r["id"] not in seen_ids:
                    found.append(r)
                    seen_ids.add(r["id"])

        conn.close()
        if not found:
            return ""

        lines = ["[연락처 프로필]"]
        for r in found[:3]:   # 최대 3명
            try:
                phones = json.loads(r["phones"])
            except Exception:
                phones = []
            ph_str = " / ".join(phones) if phones else "번호 없음"
            parts  = [r["name"]]
            if r["title"]:
                parts.append(r["title"])
            if r["org"]:
                parts.append(f"({r['org']})")
            parts.append(f"☎ {ph_str}")
            if r["last_seen"]:
                parts.append(f"| 최근기록: {r['last_seen']}")
            lines.append("  " + "  ".join(parts))

        return "\n".join(lines)

    except Exception as e:
        logger.warning("[search_contacts] %s", e)
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# Temporal RAG — 날짜 의도 추출 + path 기반 날짜 추출 + 소프트 재정렬
# (search_direct 내부 변경 없음 — post-processing only)
# ══════════════════════════════════════════════════════════════════════════════

_TEMPORAL_KW = re.compile(
    r'(작년|지난해|재작년|올해|금년|이번\s*달|이번\s*주|최근|요즘|'
    r'오래전|초기|처음부터|예전|이전|이후|최신|가장\s*최근|그때|당시|'
    r'어제|그저께|엊그제|오늘|내일)'
)
_DATE_IN_PATH = re.compile(r'(\d{4}-\d{2}-\d{2})')


def parse_temporal_intent(query: str) -> dict | None:
    """
    쿼리에서 시간 의도를 추출.
    temporal 키워드가 없으면 None 반환 → 기존 파이프라인 그대로.

    Returns: {"start": datetime|None, "end": datetime|None, "direction": "asc"|"desc"|None}
    """
    if not _TEMPORAL_KW.search(query):
        return None

    now = datetime.now()
    q   = query

    if any(k in q for k in ("재작년",)):
        return {"start": datetime(now.year - 2, 1, 1),
                "end":   datetime(now.year - 2, 12, 31), "direction": None}

    if any(k in q for k in ("작년", "지난해")):
        return {"start": datetime(now.year - 1, 1, 1),
                "end":   datetime(now.year - 1, 12, 31), "direction": None}

    if any(k in q for k in ("올해", "금년")):
        return {"start": datetime(now.year, 1, 1), "end": now, "direction": None}

    if "이번 달" in q or "이번달" in q:
        return {"start": datetime(now.year, now.month, 1), "end": now, "direction": None}

    if "이번 주" in q or "이번주" in q:
        return {"start": now - timedelta(days=now.weekday()), "end": now, "direction": None}

    if any(k in q for k in ("최근", "요즘")):
        return {"start": now - timedelta(days=30), "end": now, "direction": None}

    if any(k in q for k in ("초기", "처음", "오래전", "예전", "당시", "그때")):
        return {"start": None, "end": None, "direction": "asc"}

    if any(k in q for k in ("최신", "이후", "가장 최근")):
        return {"start": None, "end": None, "direction": "desc"}

    if "그저께" in q or "엊그제" in q:
        d = now - timedelta(days=2)
        return {"start": datetime(d.year, d.month, d.day),
                "end":   datetime(d.year, d.month, d.day, 23, 59, 59), "direction": None}

    if "어제" in q:
        d = now - timedelta(days=1)
        return {"start": datetime(d.year, d.month, d.day),
                "end":   datetime(d.year, d.month, d.day, 23, 59, 59), "direction": None}

    if "오늘" in q:
        return {"start": datetime(now.year, now.month, now.day),
                "end":   now, "direction": None}

    return None


def _extract_date_from_path(path: str) -> datetime | None:
    """path 필드에서 YYYY-MM-DD 날짜 추출. 없으면 None."""
    m = _DATE_IN_PATH.search(path)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def temporal_rerank(chunks: list[dict], temporal: dict) -> list[dict]:
    """
    temporal intent 기반 소프트 재정렬.
    - 기존 score 값 변경 없음 → final_score 별도 필드 추가
    - 기간 일치: +0.20 / 동년도: +0.05 / 기간 외: -0.08
    - direction(asc/desc)만 있을 때는 날짜 정렬만 수행
    - compress_context는 text만 사용하므로 score 필드 변경과 무관
    """
    start     = temporal.get("start")
    end       = temporal.get("end")
    direction = temporal.get("direction")

    for c in chunks:
        chunk_date = _extract_date_from_path(c.get("path", ""))
        delta = 0.0

        if start and end and chunk_date:
            if start <= chunk_date <= end:
                delta = +0.20                               # 기간 일치
            elif chunk_date.year == start.year:
                delta = +0.05                               # 동년도 약한 boost
            else:
                delta = -0.08                               # 기간 벗어남 패널티

        c["final_score"] = round(min(c["score"] + delta, 1.0), 4)

    # 정렬
    if direction == "asc":
        # 오래된 문서 우선 — 날짜 없는 청크는 뒤로
        chunks.sort(key=lambda c: _extract_date_from_path(c.get("path", "")) or datetime.max)
    elif direction == "desc":
        # 최신 문서 우선 — 날짜 없는 청크는 뒤로
        chunks.sort(key=lambda c: _extract_date_from_path(c.get("path", "")) or datetime.min,
                    reverse=True)
    elif start:
        # 기간 지정 — final_score 내림차순
        chunks.sort(key=lambda c: c.get("final_score", c["score"]), reverse=True)

    logger.debug("[temporal] intent=%s applied to %d chunks", temporal, len(chunks))
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 핵심 함수
# ══════════════════════════════════════════════════════════════════════════════

def handle_query(
    query: str,
    system_prompt: str,
    history: list[dict] | None = None,
) -> Optional[str]:
    """
    Single-Shot Q&A 파이프라인.

    Returns:
        str  → 생성된 답변 (Q&A 처리 완료)
        None → ACTION 명령 감지, 호출자가 agent.run()으로 처리해야 함
    """
    # ── Phase 12.5: MetricsContext ─────────────────────────────────────────────
    _mc = _MetricsContext(query) if _MetricsContext else None

    if _mc:
        _mc.__enter__()

    try:
        result = _handle_query_inner(query, system_prompt, history, _mc)
    finally:
        if _mc:
            _mc.__exit__(None, None, None)
            # Phase 13-B: session_manager History Guard용 스냅샷
            global _last_metrics
            _last_metrics = {
                "action":      _mc._action,
                "search_hits": _mc._search_hits,
                "intent":      _mc._intent,
                "is_success":  getattr(_mc, "_is_success", True),
                "degraded":    getattr(_mc, "_degraded", False),
            }

    return result


def _handle_query_inner(
    query: str,
    system_prompt: str,
    history: list[dict] | None,
    _mc,
) -> Optional[str]:
    # ── 0. ACTION 명령 분기 ────────────────────────────────────────────────────
    if is_action_command(query):
        logger.debug("[pipeline] ACTION 위임: %s", query[:40])
        if _mc:
            _mc.set_action("ACTION_DELEGATED")
        return None

    # ── 0b. Tier 3: LLM Micro-Router (회색 지대 쿼리) ────────────────────────
    # _ACTION_RE를 통과했지만 개인 활동+시간 표현이 겹치는 경우 LLM에게 위임 여부 물음.
    # 예: "어제 뭘 드셨어요?", "지난주에 어디 갔어?" — regex 변형 무한 대응 불필요.
    if _AMBIGUOUS_PERSONAL_RE.search(query):
        if _llm_route(query):
            logger.debug("[pipeline] MicroRouter ACTION 위임: %s", query[:40])
            if _mc:
                _mc.set_action("ACTION_DELEGATED")
            return None
        # LLM이 SEARCH로 판정 → 파이프라인 계속

    # ── 1. Alias Normalize ────────────────────────────────────────────────────
    nq = alias_normalize(query)
    if nq != query:
        logger.debug("[pipeline] normalize: %r → %r", query, nq)

    # ── 2. Intent ─────────────────────────────────────────────────────────────
    intent = classify_intent(nq)
    logger.debug("[pipeline] intent=%s query=%s", intent, nq[:40])
    if _mc:
        _mc.set_intent(intent)

    # ── 2b. Soft Override (Phase 13-B) — intent 확정 후, 검색 전 ─────────────
    _rl_hint = None
    if _SHADOW_RL_ON and intent not in _RL_BLACKLIST_INTENTS:
        try:
            _prev_hit  = "HIT" if _last_metrics.get("search_hits", 0) > 0 else "NOHIT"
            _rl_state  = f"{intent}|{_prev_hit}|NONE"
            _rl_hint   = _rl_determine(_rl_state)
            if _rl_hint:
                logger.info("[Shadow RL] Override hint: %s (state=%s)", _rl_hint, _rl_state)
        except Exception:
            pass

    # ── 3. Profile Injection (contacts.db) ───────────────────────────────────
    # contacts 검색은 원본 쿼리(query)와 정규화(nq) 모두 사용
    profile_text = search_contacts(query) or search_contacts(nq)
    if profile_text:
        logger.debug("[pipeline] 프로필 주입: %s…", profile_text[:60])

    # ── 4. Query Expansion (오버 정규화 방지) ────────────────────────────────
    # alias_normalize로 치환이 일어난 경우 원본 alias 단어도 검색어에 추가.
    # 예: "오과장님은 어떤 사람이야" → normalize → "오석송님은 어떤 사람이야"
    #     alias_dict에서 "오과장"이 원본에 있고 정규화본에 없음 → 복원
    #     search_q = "오석송님은 어떤 사람이야 오과장"
    search_q = nq
    if nq != query:
        try:
            from onew_core.terminology_server import get_index as _gi
            _alias = _gi().alias_dict
            # 원본에 있고, 정규화 결과에 없는 alias 단어 수집
            recovered = [v for v in _alias if v in query and v not in nq]
            if recovered:
                search_q = nq + " " + " ".join(recovered)
                logger.debug("[pipeline] 쿼리 확장: %r + %s", nq, recovered)
        except Exception:
            pass

    # ── 4b. 멀티턴 쿼리 확장 (모호 참조어 감지 시 이전 발화 토픽 추가) ─────────
    if history and _VAGUE_REFS_RE and _VAGUE_REFS_RE.search(search_q):
        prev_tokens: list[str] = []
        for h in reversed(history[-3:]):
            if h.get("role") == "user":
                for tok in _tokenize(h.get("content", h.get("text", ""))):
                    if len(tok) >= 2 and tok not in prev_tokens:
                        prev_tokens.append(tok)
            if len(prev_tokens) >= 5:
                break
        if prev_tokens:
            search_q = search_q + " " + " ".join(prev_tokens[:5])
            logger.debug("[pipeline] 멀티턴 확장: +%s", prev_tokens[:5])

    # ── 5. Temporal Intent + Search ───────────────────────────────────────────
    temporal = parse_temporal_intent(query)

    # 특정 날짜 지정 시 날짜 문자열을 검색어에 추가 → LanceDB 날짜 매칭 강화
    if temporal:
        _t_start = temporal.get("start")
        _t_end   = temporal.get("end")
        if _t_start and _t_end and _t_start.date() == _t_end.date():
            _date_str = _t_start.strftime("%Y-%m-%d")
            search_q = search_q + f" {_date_str}"
            logger.debug("[pipeline] 날짜 주입: %s", _date_str)

    # temporal 쿼리는 후보를 더 넉넉히 가져와야 재정렬 효과가 남 (35 vs 기본 20)
    chunks = search_direct(search_q, limit=35 if temporal else 20)
    _used_fallback = False

    # ── 6. Fallback ───────────────────────────────────────────────────────────
    if not chunks:
        chunks = fallback_search(search_q)
        _used_fallback = bool(chunks)

    # ── 6b. Temporal Re-ranking (temporal 쿼리일 때만 활성화) ─────────────────
    if temporal and chunks:
        chunks = temporal_rerank(chunks, temporal)
        logger.debug("[Temporal] %s", list(temporal.items()))

    # ── 준공도서 라우터: 수치/도면/매뉴얼 데이터 자동 주입 (API 0원) ────────
    # early return 전에 실행 → Vault RAG 미매칭 업무질의도 처리 가능
    _work_ctx = ""
    try:
        import os as _os, sys as _sys
        _sys_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _sys_dir not in _sys.path:
            _sys.path.insert(0, _sys_dir)
        from work_query_router import is_work_query, route_work_query
        # alias_normalize된 nq는 설비 동의어가 과도하게 확장될 수 있으므로
        # 원본 query만으로 판단 (오탐 방지)
        if is_work_query(query):
            _work_ctx = route_work_query(query)
            if _work_ctx:
                logger.debug("[준공도서] 라우터 발화: %d자", len(_work_ctx))
    except Exception as _e:
        logger.warning("[준공도서] 라우터 오류: %s", _e)

    # ── 6c. Unknown 처리 (chunks AND profile AND work_ctx 모두 없을 때만 종료) ──
    has_profile = bool(profile_text.strip())
    if not chunks and not has_profile and not _work_ctx:
        # ── 6c-1. 인물/연락처 쿼리면 entities.md 직접 주입 ──────────────────
        _person_kw = ("연락처", "전화", "번호", "직급", "직함", "직위", "대리", "주임",
                      "과장", "차장", "부장", "팀장", "사원", "기사", "이사", "소장")
        _is_person_q = any(k in query for k in _person_kw)
        if not _is_person_q:
            # 쿼리 토큰이 entities.md 인물 이름과 겹치는지 확인
            try:
                _ent_text = ENTITIES_MD.read_text(encoding="utf-8") if ENTITIES_MD.exists() else ""
                _surface_toks = [t for t in _query_surface_tokens(query) if len(t) >= 2]
                if _ent_text and any(t in _ent_text for t in _surface_toks):
                    _is_person_q = True
            except Exception:
                _ent_text = ""
        else:
            try:
                _ent_text = ENTITIES_MD.read_text(encoding="utf-8") if ENTITIES_MD.exists() else ""
            except Exception:
                _ent_text = ""

        if _is_person_q and _ent_text.strip():
            # entities.md 내용을 컨텍스트로 직접 사용해 LLM 단답 생성
            _ent_prompt = (
                f"[사용자 인물/연락처 DB]\n{_ent_text}\n\n"
                f"위 정보만 참고해 다음 질문에 간결하게 답하시오. "
                f"모르면 '정보 없음'이라고만 하시오.\n질문: {query}"
            )
            try:
                _api_key = _get_api_key()
                _llm_url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={_api_key}"
                )
                _llm_body = json.dumps({
                    "contents": [{"parts": [{"text": _ent_prompt}]}],
                    "generationConfig": {"maxOutputTokens": 512},
                }).encode()
                _llm_req = urllib.request.Request(
                    _llm_url,
                    data=_llm_body,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(_llm_req, timeout=15) as _r:
                    _llm_resp = json.loads(_r.read())
                _ans = (_llm_resp.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", ""))
                if _ans and "정보 없음" not in _ans:
                    if _mc:
                        _mc.set_action("ENTITIES_FALLBACK")
                        _mc.set_search_hits(1)
                        _mc.set_is_success(True)
                    return _ans.strip()
            except Exception:
                pass

        # async_learner에 미탐지 용어 기록 (비동기, 실패해도 무시)
        try:
            from onew_core.async_learner import log_unknown as _lu
            tokens = _tokenize(nq)
            for tok in tokens:
                if len(tok) >= 2:
                    _lu(tok, original_query=query)
        except Exception:
            pass
        if _mc:
            _mc.set_action("UNKNOWN")
            _mc.set_search_hits(0)
            _mc.set_is_success(False)
            _mc.set_error_type("UNKNOWN_QUERY")
        return _UNKNOWN_TEMPLATE.format(query=query)

    # ── 7. Compress ───────────────────────────────────────────────────────────
    # kiwipiepy가 "감온기"→"감"+"온기", "정대리"→"대리" 등으로 쪼개는 문제 보완:
    # 원본 쿼리의 surface_tokens(2자 이상) 전체를 compress_q에 추가하여
    # 압축기가 해당 단어가 포함된 문장을 버리지 않도록 함.
    _surface_all = [t for t in _query_surface_tokens(query) if len(t) >= 2]
    compress_q = nq + (" " + " ".join(_surface_all) if _surface_all else "")

    # temporal 쿼리: 날짜 헤더 포함 압축 → LLM 시간순 인식
    if temporal and chunks:
        context = compress_context_temporal(chunks, compress_q)
        logger.debug("[pipeline] compress_context_temporal 사용: %d chars", len(context))
    else:
        context = compress_context(intent, chunks, compress_q)

    # 프로필이 있으면 컨텍스트 앞에 삽입 (LLM이 전화번호 우선 인식)
    if has_profile:
        context = profile_text + ("\n\n" + context if context else "")

    # ── 8. Single-Shot LLM ────────────────────────────────────────────────────
    # 의료 결정 쿼리 → 소프트 경고 노트 삽입
    prefix = _MEDICAL_NOTE if is_medical_decision_query(query) else ""

    # system_prompt 누적 조합 (분석 + 정렬 어덤 독립 적용)
    sp = system_prompt
    _is_pattern = False
    if is_analysis_query(query):
        sp = sp + _ANALYSIS_SYSTEM_ADDENDUM
        pattern_ctx = _load_pattern_summary()
        if pattern_ctx:
            context = pattern_ctx + ("\n\n" + context if context else "")
            logger.debug("[pipeline] Pattern RAG 주입: %d chars", len(pattern_ctx))
            _is_pattern = True
    if is_sort_query(query) or temporal:
        sp = sp + _SORT_SYSTEM_ADDENDUM

    # ── Phase 12.5: action / search_hits 확정 ────────────────────────────────
    if _mc:
        _mc.set_search_hits(len(chunks))
        _mc.set_context_chars(len(context))
        if _is_pattern:
            _mc.set_action("ANSWER_PATTERN")
        elif temporal:
            _mc.set_action("ANSWER_TEMPORAL")
        elif has_profile and not chunks:
            _mc.set_action("ANSWER_PROFILE")
        elif _used_fallback:
            _mc.set_action("ANSWER_FALLBACK")
        else:
            _mc.set_action("ANSWER_RAG")

    # ── 준공도서 컨텍스트 주입 (라우터는 early return 전에 실행됨) ────────────
    if _work_ctx:
        _work_block = (
            "[준공도서 DB 자동 검색 결과]\n"
            "아래 데이터는 사내 준공도서에서 추출한 실측값입니다. "
            "수치는 절대 변형하지 말고 그대로 인용하세요.\n\n"
            f"{_work_ctx}"
        )
        context = _work_block + ("\n\n" + context if context else "")
        logger.debug("[준공도서] 컨텍스트 주입됨: %d자", len(_work_block))

    raw = llm_single_shot(context, query, sp, history)

    # Phase 13-B: is_success / error_type 판정
    _api_error = raw and raw.startswith("[오류]")
    if _mc:
        _mc.set_resp_chars(len(raw) if raw else 0)
        if _api_error:
            _mc.set_is_success(False)
            _mc.set_error_type("API_ERROR")
        else:
            _mc.set_is_success(True)
            _mc.set_error_type("NONE")
        # RL hint가 있었다면 action override (메트릭 기록용)
        if _rl_hint:
            _mc.set_action(_rl_hint)

    # 단정적 표현 소프트 치환
    return prefix + soften_response(raw)
