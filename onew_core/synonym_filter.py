"""
synonym_filter.py — Synonym 승인 파이프라인 Step 1 필터 + DB 큐잉

5단계 필터 중 Step 1: 언어학적 필터
  - 품사: NNG / NNP 만 허용
  - 길이: 2자 이상
  - Stopword: query_pipeline._BOOST_STOP 포함 단어 Reject

Reject 코드 (명확한 감사 추적용):
  LENGTH_TOO_SHORT  — 2자 미만
  NON_KOREAN        — 순수 한글 아님
  STOPWORD          — _BOOST_STOP 포함
  POS_MISMATCH:{tag} — NNG/NNP 아님

큐잉 규칙:
  - primary_term 미확정 시 "PENDING_LLM_DECISION" 플레이스홀더 사용
  - async_learner가 status='pending', primary_term='PENDING_LLM_DECISION' 행만
    모아 배치 LLM 호출 → primary_term 확정 후 UPDATE
  - ON CONFLICT: 중복 삽입 시 count/source_docs/confidence 최신값으로 갱신

사용:
    from onew_core.synonym_filter import filter_step1, enqueue_candidate

    ok, code = filter_step1("감온기")          # (True, "NNG")
    ok, code = filter_step1("어떤")            # (False, "STOPWORD")

    enqueue_candidate("감온기", count=3, source_docs=2)
    enqueue_candidate("오차장", primary_term="오석송", count=4, source_docs=3, confidence=0.91)
"""

from __future__ import annotations
import os
import re
import sqlite3
from datetime import datetime

# ── 경로 상수 ─────────────────────────────────────────────────────────────────
_SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TERM_DB    = os.path.join(_SYSTEM_DIR, "onew_terminology.db")

# ── kiwipiepy 형태소 분석기 ────────────────────────────────────────────────────
try:
    from kiwipiepy import Kiwi as _Kiwi
    _kiwi = _Kiwi()
except Exception:
    _kiwi = None

# ── query_pipeline 전역 상수 재사용 (중복 정의 방지) ──────────────────────────
try:
    from onew_core.query_pipeline import _BOOST_STOP
except Exception:
    _BOOST_STOP: frozenset[str] = frozenset()

# ── 허용 품사 / 패턴 상수 ─────────────────────────────────────────────────────
_ALLOW_POS  = {"NNG", "NNP"}
_KOREAN_RE  = re.compile(r'^[가-힣]{2,}$')

# LLM 결정 대기 플레이스홀더
PENDING_LLM = "PENDING_LLM_DECISION"


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: 언어학적 필터
# ══════════════════════════════════════════════════════════════════════════════

def check_pos(term: str) -> str | None:
    """
    kiwipiepy로 term의 대표 품사 반환.
    단일 형태소 → 해당 태그 반환.
    복합어(모두 NNG/NNP) → "NNP" 반환.
    분석 불가 / 혼합 품사 → None.
    """
    if _kiwi is None:
        return "NNG" if _KOREAN_RE.match(term) else None
    try:
        tokens = _kiwi.tokenize(term)
        if len(tokens) == 1:
            return tokens[0].tag
        tags = [t.tag for t in tokens]
        # 복합어: 모두 NNG/NNP → NNP
        if all(t in _ALLOW_POS for t in tags):
            return "NNP"
        # 복합어: NNG/NNP + XSN(명사파생접미사) 조합 허용
        # 예) "냉동기" → NNG(냉동)+XSN(기), "응축기" → NNG(응축)+XSN(기)
        _NOUN_ALLOW = _ALLOW_POS | {"XSN", "XPN"}
        if all(t in _NOUN_ALLOW for t in tags) and any(t in _ALLOW_POS for t in tags):
            return "NNG"
        return None
    except Exception:
        return None


def filter_step1(term: str) -> tuple[bool, str]:
    """
    Step 1: 언어학적 필터.

    Returns:
        (True,  pos_tag)      — 통과
        (False, reject_code)  — 탈락

    Reject 코드:
        LENGTH_TOO_SHORT      — 2자 미만
        NON_KOREAN            — 순수 한글 아님
        STOPWORD              — _BOOST_STOP 포함
        POS_MISMATCH:{tag}    — NNG/NNP 아님
    """
    if len(term) < 2:
        return False, "LENGTH_TOO_SHORT"

    if not _KOREAN_RE.match(term):
        return False, "NON_KOREAN"

    if term in _BOOST_STOP:
        return False, "STOPWORD"

    pos = check_pos(term)
    if pos not in _ALLOW_POS:
        return False, f"POS_MISMATCH:{pos}"

    return True, pos


def filter_candidates(candidates: list[str]) -> list[tuple[str, str]]:
    """
    후보 목록 → Step 1 통과 목록 반환: [(term, pos_tag), ...]
    """
    return [(t, info) for t in candidates
            for ok, info in [filter_step1(t)] if ok]


# ══════════════════════════════════════════════════════════════════════════════
# DB 큐잉: synonyms_pending INSERT / ON CONFLICT UPDATE
# ══════════════════════════════════════════════════════════════════════════════

_COUNT_CAP   = 9999  # count 상한 (무한 누적 방지)
_MAX_HASHES  = 50   # source_hashes FIFO 상한 (DB 비대화 방지)
_TTL_DAYS    = 7    # rejected → pending 복구 기간 (일)


def enqueue_candidate(
    variant:       str,
    primary_term:  str        = PENDING_LLM,
    count:         int        = 1,
    source_hashes: list[str]  | None = None,   # 실제 문서 경로/해시 목록
    confidence:    float      = 0.0,
    pos_tag:       str | None = None,
) -> tuple[bool, str]:
    """
    synonyms_pending 테이블에 후보 삽입.

    Step 1 통과 여부를 먼저 검사하고:
      - 탈락 → DB 미삽입, (False, reject_code) 반환
      - 통과 → INSERT or ON CONFLICT UPDATE

    ON CONFLICT(variant, primary_term):
      - count        : count + excluded.count  (누적, 상한 _COUNT_CAP)
      - source_hashes: 기존 + 신규 해시 병합, 중복 제거
      - source_docs  : len(merged source_hashes)  자동 재산출
      - confidence   : MAX(기존, 신규)
      - reviewed_at  : 갱신
      - status       : 기존이 'rejected'면 그대로 유지 (재등록 방지)

    Returns:
        (True,  "INSERTED" | "UPDATED")
        (False, reject_code)
    """
    import json as _json

    # Step 1 필터
    ok, info = filter_step1(variant)
    if not ok:
        return False, info

    resolved_pos  = pos_tag or info
    hashes        = source_hashes or []
    # 첫 삽입 시에도 FIFO 상한 적용
    if len(hashes) > _MAX_HASHES:
        hashes = hashes[-_MAX_HASHES:]
    hashes_json   = _json.dumps(hashes, ensure_ascii=False)
    source_docs   = len(set(hashes))
    now           = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    try:
        conn = sqlite3.connect(_TERM_DB)

        # ON CONFLICT 시 source_hashes 병합은 SQL만으로 불가 → 직접 처리
        existing = conn.execute(
            "SELECT id, count, source_hashes, confidence, status FROM synonyms_pending "
            "WHERE variant=? AND primary_term=?",
            (variant, primary_term),
        ).fetchone()

        if existing:
            if existing[4] == "rejected":   # rejected면 재등록 차단
                conn.close()
                return False, "ALREADY_REJECTED"

            # count 누적 (cap 적용)
            new_count = min(existing[1] + count, _COUNT_CAP)

            # source_hashes 병합·중복 제거 + FIFO 50 상한
            try:
                old_hashes = _json.loads(existing[2] or "[]")
            except Exception:
                old_hashes = []
            merged = list(dict.fromkeys(old_hashes + hashes))  # 순서 유지 중복 제거
            if len(merged) > _MAX_HASHES:                       # FIFO: 오래된 것 제거
                merged = merged[-_MAX_HASHES:]
            merged_json = _json.dumps(merged, ensure_ascii=False)
            new_docs    = len(merged)

            # Confidence Smoothing (이동 평균 + cold-start 보정)
            old_conf = existing[3] if existing[3] is not None else 0.0
            if old_conf == 0.0:
                new_conf = confidence          # cold-start: 첫 값 즉시 반영
            else:
                new_conf = old_conf * 0.7 + confidence * 0.3   # EMA

            cur = conn.execute(
                """UPDATE synonyms_pending
                   SET count=?, source_hashes=?, source_docs=?,
                       confidence=?, reviewed_at=?
                   WHERE variant=? AND primary_term=?""",
                (new_count, merged_json, new_docs,
                 round(new_conf, 4), now, variant, primary_term),
            )
            action = "UPDATED"
        else:
            cur = conn.execute(
                """INSERT INTO synonyms_pending
                   (variant, primary_term, pos_tag, count, source_docs,
                    source_hashes, confidence, status, created_at)
                   VALUES (?,?,?,?,?,?,?,'pending',?)""",
                (variant, primary_term, resolved_pos, count, source_docs,
                 hashes_json, confidence, now),
            )
            action = "INSERTED"

        conn.commit()
        conn.close()
        return True, action
    except Exception as e:
        return False, f"DB_ERROR:{e}"


def fetch_pending_for_llm(limit: int = 50) -> list[dict]:
    """
    async_learner 배치용:
    primary_term = PENDING_LLM_DECISION 이고 status = 'pending' 인 행 반환.
    count >= 1 기준 (Step 2~4는 async_learner의 apply_gate에서 재검증).
    """
    try:
        conn = sqlite3.connect(_TERM_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, variant, pos_tag, count, source_docs,
                   source_hashes, confidence
            FROM   synonyms_pending
            WHERE  status = 'pending'
              AND  primary_term = ?
            ORDER  BY count DESC, source_docs DESC
            LIMIT  ?
            """,
            (PENDING_LLM, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def mark_rejected(row_id: int, reason: str) -> None:
    """
    synonyms_pending 행을 rejected로 마킹. rejected_at 기록.
    async_learner.apply_gate()가 'rejected' 반환 시 호출.
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        conn = sqlite3.connect(_TERM_DB)
        conn.execute(
            """UPDATE synonyms_pending
               SET status='rejected', reject_reason=?, rejected_at=?, reviewed_at=?
               WHERE id=?""",
            (reason, now, now, row_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def mark_conflict(row_id: int, reason: str) -> None:
    """
    synonyms_pending 행을 conflict(수동 검토 대기)로 마킹.
    async_learner.apply_gate()가 'conflict' 반환 시 호출.
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        conn = sqlite3.connect(_TERM_DB)
        conn.execute(
            """UPDATE synonyms_pending
               SET status='conflict', reject_reason=?, rejected_at=?, reviewed_at=?
               WHERE id=?""",
            (reason, now, now, row_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def recover_ttl(days: int = _TTL_DAYS) -> int:
    """
    TTL 복구: rejected_at 이후 days일 이상 경과한 행을 pending으로 되돌림.
    '망각의 미학' — 과거 오판을 시간이 지나면 재평가.

    Returns: 복구된 행 수
    """
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        conn = sqlite3.connect(_TERM_DB)
        cur = conn.execute(
            """UPDATE synonyms_pending
               SET status='pending', reject_reason=NULL,
                   rejected_at=NULL, reviewed_at=?
               WHERE status IN ('rejected', 'conflict')
                 AND rejected_at IS NOT NULL
                 AND rejected_at < ?""",
            (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), cutoff),
        )
        recovered = cur.rowcount
        conn.commit()
        conn.close()
        return recovered
    except Exception:
        return 0


def update_llm_result(
    row_id:      int,
    primary_term: str,
    confidence:  float,
) -> None:
    """
    async_learner가 LLM 결과를 받은 후 primary_term / confidence 업데이트.
    apply_gate 통과 여부는 async_learner가 별도 판단.
    """
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        conn = sqlite3.connect(_TERM_DB)
        conn.execute(
            """
            UPDATE synonyms_pending
            SET    primary_term = ?, confidence = ?, reviewed_at = ?
            WHERE  id = ? AND status = 'pending'
            """,
            (primary_term, confidence, now, row_id),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
