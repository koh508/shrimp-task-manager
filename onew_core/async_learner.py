"""
async_learner.py — 온유 비동기 용어 학습 파이프라인

[역할]
  query_pipeline에서 검색 미달(unknown) 용어를 배치 단위로 LLM에 전송,
  primary_term 후보를 생성하여 onew_terminology.db에 자동 등록.

[6대 가드레일]
  1. Audit 테이블  — learning_log(추적), blacklist_terms(영구 제외)
  2. LLM 출력 강제 검증 — validate_llm_output(): 타입/키/범위 검사
  3. Buffer 폭주 방지 — MAX_UNKNOWN_TERMS=5000, MAX_QUERIES_PER_TERM=10
  4. Batch 비용 제어 — BATCH_SIZE=15, ORDER BY count DESC
  5. Multi-Evidence Gate — confidence≥0.85 AND count≥3 AND contexts≥2
  6. Alias Drift 방지 — 기존 variant→primary 변경 시 pending 강등

[연동]
  query_pipeline.py의 "검색 실패" 분기에서 log_unknown(term, query) 호출.
  async_learner는 별도 프로세스(cron/수동)로 실행.

[실행]
  python async_learner.py           # 배치 처리 1회
  python async_learner.py --stats   # 버퍼/로그 통계
  python async_learner.py --pending # pending_review 목록
  python async_learner.py --init    # blacklist 기본값 초기화
  python async_learner.py --flush   # unknown_buffer 전체 초기화 (주의)
"""

from __future__ import annotations

import io
import sys
import os
import re
import json
import sqlite3
import logging
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Windows 인코딩 ────────────────────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# ── 경로 ─────────────────────────────────────────────────────────────────────
SYSTEM_DIR = Path(__file__).parent.parent
TERM_DB    = SYSTEM_DIR / "onew_terminology.db"

# ══════════════════════════════════════════════════════════════════════════════
# 가드레일 상수
# ══════════════════════════════════════════════════════════════════════════════
MAX_UNKNOWN_TERMS    = 5_000   # 버퍼 최대 항목 수
MAX_QUERIES_PER_TERM = 10      # 항목당 original_queries 최대 보존 수
BATCH_SIZE           = 15      # LLM 1회 호출 당 최대 용어 수

# Multi-Evidence Gate 기준
GATE_MIN_CONFIDENCE  = 0.85
GATE_MIN_COUNT       = 3
GATE_MIN_CONTEXTS    = 2

LLM_MODEL = "gemini/gemini-2.5-flash"

# ══════════════════════════════════════════════════════════════════════════════
# 1. DB 스키마 초기화
# ══════════════════════════════════════════════════════════════════════════════

DDL = """
-- ─────────────────────────────────────────────────────────────
-- unknown_buffer: 검색 미달 용어 수집소
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS unknown_buffer (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    term             TEXT NOT NULL UNIQUE,
    count            INTEGER DEFAULT 1,           -- 누적 등장 횟수
    original_queries TEXT  DEFAULT '[]',          -- JSON 배열, 최대 10개
    first_seen       TEXT  NOT NULL,
    last_seen        TEXT  NOT NULL,
    status           TEXT  DEFAULT 'pending'      -- pending | processed | blacklisted
);
CREATE INDEX IF NOT EXISTS idx_ub_status_count ON unknown_buffer(status, count DESC);

-- ─────────────────────────────────────────────────────────────
-- learning_log: LLM 제안 전체 감사 로그
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS learning_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    term              TEXT NOT NULL,
    suggested_primary TEXT,
    confidence        REAL,
    decision          TEXT NOT NULL,  -- approved | rejected | pending | skipped
    reason            TEXT,
    timestamp         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ll_term      ON learning_log(term);
CREATE INDEX IF NOT EXISTS idx_ll_decision  ON learning_log(decision);

-- ─────────────────────────────────────────────────────────────
-- blacklist_terms: 학습 영구 제외 단어
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS blacklist_terms (
    term      TEXT PRIMARY KEY,
    added_at  TEXT NOT NULL,
    reason    TEXT DEFAULT ''
);
"""

DEFAULT_BLACKLIST: list[tuple[str, str]] = [
    ("오늘",     "시제어"),
    ("어제",     "시제어"),
    ("내일",     "시제어"),
    ("작업",     "범용 동사"),
    ("문제",     "범용 명사"),
    ("결과",     "범용 명사"),
    ("내용",     "범용 명사"),
    ("확인",     "범용 동사"),
    ("진행",     "범용 동사"),
    ("처리",     "범용 동사"),
    ("관련",     "범용 형용사"),
    ("및",       "접속사"),
    ("또는",     "접속사"),
    ("그리고",   "접속사"),
    ("이것",     "대명사"),
    ("저것",     "대명사"),
    ("뭐야",     "의문 표현"),
    ("알려줘",   "의문 표현"),
    ("뭔지",     "의문 표현"),
]


def get_conn(db_path: Path = TERM_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_learner_db(db_path: Path = TERM_DB):
    """unknown_buffer / learning_log / blacklist_terms 테이블 생성."""
    conn = get_conn(db_path)
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    logger.info("[init] learner 테이블 초기화 완료")


def init_blacklist(db_path: Path = TERM_DB):
    """기본 blacklist 단어 등록."""
    conn = get_conn(db_path)
    now = datetime.now().isoformat()
    for term, reason in DEFAULT_BLACKLIST:
        conn.execute(
            "INSERT OR IGNORE INTO blacklist_terms (term, added_at, reason) VALUES (?,?,?)",
            (term, now, reason)
        )
    conn.commit()
    conn.close()
    print(f"  blacklist 초기화: {len(DEFAULT_BLACKLIST)}개 등록")


# ══════════════════════════════════════════════════════════════════════════════
# 2. unknown_buffer 기록 (query_pipeline에서 호출)
# ══════════════════════════════════════════════════════════════════════════════

def log_unknown(term: str, original_query: str = "",
                db_path: Path = TERM_DB):
    """
    검색 미달 용어를 unknown_buffer에 누적.
    - count 증가
    - original_queries FIFO 최대 MAX_QUERIES_PER_TERM
    - blacklist/processed 항목 무시
    이 함수는 query_pipeline.py에서 비동기로 호출된다.
    """
    term = term.strip()
    if not term or len(term) < 2:
        return
    # 길이가 너무 길면 앞 40자만 (오염 방지)
    term = term[:40]

    try:
        conn = get_conn(db_path)
        now  = datetime.now().isoformat()

        # blacklist 확인
        bl = conn.execute(
            "SELECT 1 FROM blacklist_terms WHERE term=?", (term,)
        ).fetchone()
        if bl:
            conn.close()
            return

        row = conn.execute(
            "SELECT id, count, original_queries, status FROM unknown_buffer WHERE term=?",
            (term,)
        ).fetchone()

        if row:
            if row["status"] in ("processed", "blacklisted"):
                conn.close()
                return

            # original_queries FIFO 관리
            try:
                queries: list = json.loads(row["original_queries"])
            except Exception:
                queries = []

            if original_query and original_query not in queries:
                queries.append(original_query)
                if len(queries) > MAX_QUERIES_PER_TERM:
                    queries = queries[-MAX_QUERIES_PER_TERM:]

            conn.execute("""
                UPDATE unknown_buffer
                SET count            = count + 1,
                    original_queries = ?,
                    last_seen        = ?
                WHERE id = ?
            """, (json.dumps(queries, ensure_ascii=False), now, row["id"]))
        else:
            queries = [original_query] if original_query else []
            conn.execute("""
                INSERT INTO unknown_buffer (term, count, original_queries, first_seen, last_seen)
                VALUES (?, 1, ?, ?, ?)
            """, (term, json.dumps(queries, ensure_ascii=False), now, now))

        conn.commit()
        conn.close()

        # 버퍼 폭주 확인 (비동기로 Pruning)
        _prune_if_needed(db_path)

    except Exception as e:
        logger.warning("[log_unknown] %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# 3. 버퍼 폭주 방지 (Pruning)
# ══════════════════════════════════════════════════════════════════════════════

def _prune_if_needed(db_path: Path = TERM_DB):
    """
    버퍼 항목이 MAX_UNKNOWN_TERMS 초과 시
    last_seen이 가장 오래된 pending 항목부터 삭제.
    """
    try:
        conn = get_conn(db_path)
        total = conn.execute(
            "SELECT COUNT(*) FROM unknown_buffer WHERE status='pending'"
        ).fetchone()[0]

        if total > MAX_UNKNOWN_TERMS:
            excess = total - MAX_UNKNOWN_TERMS
            conn.execute("""
                DELETE FROM unknown_buffer
                WHERE id IN (
                    SELECT id FROM unknown_buffer
                    WHERE status = 'pending'
                    ORDER BY last_seen ASC
                    LIMIT ?
                )
            """, (excess,))
            conn.commit()
            logger.info("[prune] 오래된 %d개 항목 삭제 (total=%d → %d)",
                        excess, total, MAX_UNKNOWN_TERMS)
        conn.close()
    except Exception as e:
        logger.warning("[prune] %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# 4. LLM 출력 강제 검증 (Schema Validation)
# ══════════════════════════════════════════════════════════════════════════════

_REQUIRED_KEYS = {"term", "primary_term", "confidence"}


def validate_llm_output(raw: str) -> list[dict]:
    """
    LLM 반환 JSON을 엄격하게 검증.

    유효 항목만 반환 (오류 항목은 Skip, 전체 배치 중단 없음).

    Expected:
        [{"term": str, "primary_term": str, "confidence": float 0~1}, ...]
    """
    # ── JSON 파싱 ─────────────────────────────────────────────────────────────
    raw = raw.strip()

    # LLM이 ```json ... ``` 코드블록으로 감싼 경우 제거
    fence_m = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', raw, re.IGNORECASE)
    if fence_m:
        raw = fence_m.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("[validate] JSON 파싱 실패: %s | 원문: %s…", e, raw[:120])
        return []

    if not isinstance(data, list):
        logger.error("[validate] 최상위 타입이 list가 아님: %s", type(data).__name__)
        return []

    valid = []
    for i, item in enumerate(data):
        # 타입 체크
        if not isinstance(item, dict):
            logger.warning("[validate] item[%d] dict 아님: %s", i, type(item))
            continue

        # 필수 키 체크
        missing = _REQUIRED_KEYS - item.keys()
        if missing:
            logger.warning("[validate] item[%d] 키 누락: %s", i, missing)
            continue

        # 값 타입 체크
        term         = item.get("term")
        primary_term = item.get("primary_term")
        confidence   = item.get("confidence")

        if not isinstance(term, str) or not term.strip():
            logger.warning("[validate] item[%d] term 비정상: %r", i, term)
            continue
        if not isinstance(primary_term, str) or not primary_term.strip():
            logger.warning("[validate] item[%d] primary_term 비정상: %r", i, primary_term)
            continue
        if not isinstance(confidence, (int, float)):
            logger.warning("[validate] item[%d] confidence 타입 오류: %r", i, confidence)
            continue

        confidence = float(confidence)
        if not (0.0 <= confidence <= 1.0):
            logger.warning("[validate] item[%d] confidence 범위 초과: %f", i, confidence)
            continue

        # primary_term이 term 자체와 동일하고 공백 없는 동일 문자열이면 의미 없음
        if term.strip() == primary_term.strip():
            logger.debug("[validate] item[%d] term==primary_term, skip", i)
            continue

        valid.append({
            "term":         term.strip(),
            "primary_term": primary_term.strip(),
            "confidence":   confidence,
            "reason":       str(item.get("reason", "")),
        })

    logger.debug("[validate] %d/%d 항목 유효", len(valid), len(data))
    return valid


# ══════════════════════════════════════════════════════════════════════════════
# 5. LLM 호출 (배치)
# ══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 한국어 전문 용어 정규화 AI입니다.
    아래 unknown_terms 목록의 각 항목에 대해 다음을 수행하세요:

    1. 해당 용어의 "정규 표현(primary_term)"을 제안하세요.
       - 단어 분리 교정: '냉동장치' → '냉동 장치'
       - 복합어 분리: '급수펌프' → '급수 펌프'
       - 약어/은어 확인: 'VP-008' → 'VP-008' (코드는 그대로 유지)
       - 변형 없이 그대로 써야 할 것은 primary_term을 term과 동일하게 하면 안 됩니다.
       - 정규화가 불확실하면 confidence를 낮게 주세요.

    2. confidence(0.0~1.0)를 반드시 포함하세요.
    3. 각 original_queries 문맥을 근거로 판단하세요.

    반환 형식: 오직 JSON 배열만. 설명 없음.
    [
      {"term": "원본용어", "primary_term": "정규표현", "confidence": 0.92, "reason": "분리 이유"},
      ...
    ]
""")


def _build_llm_prompt(batch: list[dict]) -> str:
    """배치 → LLM 프롬프트 문자열."""
    items = []
    for row in batch:
        try:
            queries = json.loads(row["original_queries"])[:3]  # 문맥은 최대 3개만
        except Exception:
            queries = []
        items.append({
            "term":             row["term"],
            "count":            row["count"],
            "original_queries": queries,
        })
    return json.dumps(items, ensure_ascii=False, indent=2)


def call_llm(batch: list[dict]) -> list[dict]:
    """
    LLM에 배치 전송 → 검증된 결과 반환.
    실패 시 빈 리스트 (배치 전체 스킵, 다음 배치 계속).
    """
    from litellm import completion

    user_content = _build_llm_prompt(batch)

    try:
        resp = completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system",  "content": _SYSTEM_PROMPT},
                {"role": "user",    "content": f"unknown_terms:\n{user_content}"},
            ],
            temperature=0.2,   # 낮은 온도 → 일관된 JSON 출력
        )
        raw = resp.choices[0].message.content.strip()
        return validate_llm_output(raw)

    except Exception as e:
        logger.error("[call_llm] LLM 호출 실패: %s", e)
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 6. Alias Drift 방지 + Multi-Evidence Gate
# ══════════════════════════════════════════════════════════════════════════════

def _check_alias_drift(conn: sqlite3.Connection,
                       term: str, suggested_primary: str) -> tuple[bool, str]:
    """
    이미 등록된 variant→primary 매핑이 다른 primary를 가리키는지 확인.

    Returns:
        (drift_detected: bool, existing_primary: str)
    """
    row = conn.execute(
        "SELECT primary_term FROM terms WHERE variant=?", (term,)
    ).fetchone()
    if row and row["primary_term"] != suggested_primary:
        return True, row["primary_term"]
    return False, ""


def _count_distinct_contexts(original_queries_json: str,
                              source_hashes_json: str | None = None) -> int:
    """
    고유 문맥 수 반환.
    source_hashes (실제 문서 경로 목록)가 있으면 그걸 우선 사용 — 진짜 다양성.
    없으면 original_queries 앞 10자 기준 fallback.
    """
    # source_hashes 우선 (synonyms_pending 경유 데이터)
    if source_hashes_json:
        try:
            hashes = json.loads(source_hashes_json)
            distinct = {h for h in hashes if h}
            if distinct:
                return len(distinct)
        except Exception:
            pass
    # fallback: 쿼리 텍스트 앞 10자 기준
    try:
        queries = json.loads(original_queries_json)
        distinct = {q[:10] for q in queries if q}
        return len(distinct)
    except Exception:
        return 0


def _log_decision(conn: sqlite3.Connection,
                  term: str, suggested_primary: str | None,
                  confidence: float | None, decision: str, reason: str):
    conn.execute("""
        INSERT INTO learning_log
          (term, suggested_primary, confidence, decision, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (term, suggested_primary, confidence, decision, reason,
          datetime.now().isoformat()))


def apply_gate(conn: sqlite3.Connection,
               llm_item: dict,
               buffer_row: sqlite3.Row,
               source_hashes_json: str | None = None) -> str:
    """
    Multi-Evidence Gate 평가.

    Args:
        source_hashes_json: synonyms_pending.source_hashes (실제 문서 경로 목록).
                            있으면 distinct_contexts 계산에 우선 사용.

    Returns: 'approved' | 'pending' | 'rejected'
    """
    term       = llm_item["term"]
    primary    = llm_item["primary_term"]
    confidence = llm_item["confidence"]
    count      = buffer_row["count"]
    contexts   = _count_distinct_contexts(
        buffer_row["original_queries"],
        source_hashes_json=source_hashes_json,
    )

    # ── Alias Drift 체크 (Soft Conflict Zone) ───────────────────────────────
    # confidence < 0.9  → 'conflict' (수동 검토 대기, 추후 재평가 가능)
    # confidence >= 0.9 → 'rejected' (확신도 높은 충돌, 강한 차단)
    drift, existing = _check_alias_drift(conn, term, primary)
    if drift:
        reason = f"DRIFT_DETECTED: 기존={existing!r} 신규={primary!r}"
        if confidence >= 0.9:
            logger.warning("[gate] REJECTED (high-conf drift) %s", reason)
            _log_decision(conn, term, primary, confidence, "rejected",
                          reason + " → conf≥0.9 강한차단")
            return "rejected"
        else:
            logger.warning("[gate] CONFLICT (low-conf drift) %s", reason)
            _log_decision(conn, term, primary, confidence, "conflict",
                          reason + f" → conf={confidence:.2f}<0.9 수동검토")
            return "conflict"

    # ── 자동 승인 조건 (AND) ──────────────────────────────────────────────────
    if (confidence >= GATE_MIN_CONFIDENCE
            and count    >= GATE_MIN_COUNT
            and contexts >= GATE_MIN_CONTEXTS):
        reason = (f"confidence={confidence:.2f} count={count} "
                  f"contexts={contexts} → AUTO_APPROVED")
        _log_decision(conn, term, primary, confidence, "approved", reason)
        return "approved"

    # ── 조건 미달 → pending 유지, 구체적 사유 기록 ───────────────────────────
    fails = []
    if confidence < GATE_MIN_CONFIDENCE:
        fails.append(f"confidence={confidence:.2f}<{GATE_MIN_CONFIDENCE}")
    if count < GATE_MIN_COUNT:
        fails.append(f"count={count}<{GATE_MIN_COUNT}")
    if contexts < GATE_MIN_CONTEXTS:
        fails.append(f"contexts={contexts}<{GATE_MIN_CONTEXTS}")

    reason = "CONDITION_NOT_MET: " + ", ".join(fails)
    _log_decision(conn, term, primary, confidence, "pending", reason)
    return "pending"


# ══════════════════════════════════════════════════════════════════════════════
# 7. 배치 처리 메인
# ══════════════════════════════════════════════════════════════════════════════

def _get_batch(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """
    unknown_buffer에서 count 높은 순으로 BATCH_SIZE개 반환.
    status='pending' 항목만.
    """
    return conn.execute("""
        SELECT id, term, count, original_queries, first_seen, last_seen
        FROM unknown_buffer
        WHERE status = 'pending'
        ORDER BY count DESC
        LIMIT ?
    """, (BATCH_SIZE,)).fetchall()


def _is_blacklisted(conn: sqlite3.Connection, term: str) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM blacklist_terms WHERE term=?", (term,)
    ).fetchone())


def _write_to_terminology(conn: sqlite3.Connection,
                          term: str, primary: str, confidence: float):
    """
    approved 항목을 terms 테이블에 등록.
    이미 존재하면 INSERT OR IGNORE (중복 무시).
    """
    conn.execute("""
        INSERT OR IGNORE INTO terms
          (primary_term, variant, confidence, source, is_verified, created_at)
        VALUES (?, ?, ?, 'async_learner', 0, ?)
    """, (primary, term, confidence, datetime.now().isoformat()))


def _write_to_pending_review(conn: sqlite3.Connection,
                             term: str, primary: str, confidence: float,
                             reason: str):
    """pending 항목을 terminology DB의 pending_review에 기록."""
    # pending_review 테이블이 없을 수도 있으므로 생성 보장
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_review_terms (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            term          TEXT NOT NULL,
            suggested_primary TEXT,
            confidence    REAL,
            reason        TEXT,
            created_at    TEXT
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO pending_review_terms
          (term, suggested_primary, confidence, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (term, primary, confidence, reason, datetime.now().isoformat()))


def process_batch(db_path: Path = TERM_DB) -> dict:
    """
    메인 배치 처리 함수.

    Returns:
        {approved, pending, rejected, skipped, blacklisted, llm_errors}
    """
    conn = get_conn(db_path)
    stats = dict(approved=0, pending=0, rejected=0,
                 skipped=0, blacklisted=0, llm_errors=0)

    batch = _get_batch(conn)
    if not batch:
        logger.info("[process] unknown_buffer 비어있음 (또는 처리 완료)")
        conn.close()
        return stats

    logger.info("[process] 배치 %d개 처리 시작", len(batch))
    print(f"[process] unknown_buffer에서 {len(batch)}개 용어 처리 중...")

    # ── blacklist 사전 필터 ───────────────────────────────────────────────────
    to_process: list[sqlite3.Row] = []
    for row in batch:
        if _is_blacklisted(conn, row["term"]):
            conn.execute(
                "UPDATE unknown_buffer SET status='blacklisted' WHERE id=?",
                (row["id"],)
            )
            _log_decision(conn, row["term"], None, None,
                          "skipped", "blacklist 매칭")
            stats["blacklisted"] += 1
        else:
            to_process.append(row)

    conn.commit()

    if not to_process:
        conn.close()
        return stats

    # ── LLM 호출 ─────────────────────────────────────────────────────────────
    llm_results = call_llm(to_process)

    if not llm_results:
        stats["llm_errors"] += 1
        logger.error("[process] LLM 결과 없음 — 이번 배치 스킵")
        conn.close()
        return stats

    # LLM 결과를 term 기준 딕셔너리로 변환
    llm_map: dict[str, dict] = {r["term"]: r for r in llm_results}

    # ── 결과 적용 ─────────────────────────────────────────────────────────────
    for row in to_process:
        term = row["term"]

        if term not in llm_map:
            # LLM이 해당 term을 반환하지 않음
            _log_decision(conn, term, None, None,
                          "skipped", "LLM 결과 없음")
            stats["skipped"] += 1
            continue

        item = llm_map[term]
        decision = apply_gate(conn, item, row)

        if decision == "approved":
            _write_to_terminology(conn, term, item["primary_term"], item["confidence"])
            conn.execute(
                "UPDATE unknown_buffer SET status='processed' WHERE id=?",
                (row["id"],)
            )
            stats["approved"] += 1
            print(f"  ✓ 승인: {term!r} → {item['primary_term']!r} ({item['confidence']:.2f})")

        elif decision == "conflict":
            _write_to_pending_review(
                conn, term, item["primary_term"], item["confidence"],
                "CONFLICT: Alias Drift 감지 (conf<0.9) — 수동 검토 필요"
            )
            stats["pending"] += 1
            print(f"  ⚠️  충돌: {term!r} → {item['primary_term']!r} "
                  f"(기존 매핑 충돌, conf={item['confidence']:.2f})")

        elif decision == "pending":
            _write_to_pending_review(
                conn, term, item["primary_term"], item["confidence"],
                "CONDITION_NOT_MET: Gate 조건 미달"
            )
            stats["pending"] += 1
            print(f"  ⏳ 보류: {term!r} → {item['primary_term']!r} ({item['confidence']:.2f})")

        else:  # rejected (high-conf drift)
            conn.execute(
                "UPDATE unknown_buffer SET status='processed' WHERE id=?",
                (row["id"],)
            )
            stats["rejected"] += 1
            print(f"  ✗ 거부: {term!r} → {item['primary_term']!r} "
                  f"(Drift conf≥0.9, 강한차단)")

    conn.commit()

    # ── In-memory alias_dict 갱신 (싱글톤 재로드) ────────────────────────────
    if stats["approved"] > 0:
        try:
            sys.path.insert(0, str(SYSTEM_DIR / "onew_core"))
            from terminology_server import get_index
            get_index()._reload()
            logger.info("[process] TerminologyIndex 갱신 완료")
        except Exception as e:
            logger.warning("[process] TerminologyIndex 갱신 실패: %s", e)

    conn.close()
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# 8. CLI 서브커맨드
# ══════════════════════════════════════════════════════════════════════════════

def _cmd_stats():
    conn = get_conn()
    pending_cnt = conn.execute(
        "SELECT COUNT(*) FROM unknown_buffer WHERE status='pending'"
    ).fetchone()[0]
    processed   = conn.execute(
        "SELECT COUNT(*) FROM unknown_buffer WHERE status='processed'"
    ).fetchone()[0]
    blacklisted = conn.execute(
        "SELECT COUNT(*) FROM unknown_buffer WHERE status='blacklisted'"
    ).fetchone()[0]
    top5 = conn.execute("""
        SELECT term, count FROM unknown_buffer
        WHERE status='pending'
        ORDER BY count DESC LIMIT 5
    """).fetchall()

    approved = conn.execute(
        "SELECT COUNT(*) FROM learning_log WHERE decision='approved'"
    ).fetchone()[0]
    ll_pending = conn.execute(
        "SELECT COUNT(*) FROM learning_log WHERE decision='pending'"
    ).fetchone()[0]

    conn.close()

    print(f"[unknown_buffer]")
    print(f"  대기(pending)   : {pending_cnt:,}개")
    print(f"  처리 완료        : {processed:,}개")
    print(f"  블랙리스트       : {blacklisted:,}개")
    print(f"\n[learning_log]")
    print(f"  승인(approved)  : {approved:,}개")
    print(f"  보류(pending)   : {ll_pending:,}개")
    if top5:
        print(f"\n[대기 상위 5개]")
        for r in top5:
            print(f"  {r['term']!r:20s} count={r['count']}")


def _cmd_pending():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT term, suggested_primary, confidence, reason, created_at
            FROM pending_review_terms
            ORDER BY confidence DESC
        """).fetchall()
    except Exception:
        rows = []
    conn.close()

    if not rows:
        print("pending_review_terms 비어있음")
        return

    print(f"{'term':<22} {'→ primary':<22} {'conf':>5}  이유")
    print("-" * 80)
    for r in rows:
        print(f"{r['term']:<22} {r['suggested_primary'] or '-':<22} "
              f"{r['confidence'] or 0:>5.2f}  {r['reason'] or ''}")


def _cmd_flush():
    ans = input("unknown_buffer를 전체 초기화합니다. 계속? [y/N] ").strip().lower()
    if ans != 'y':
        print("취소됨")
        return
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM unknown_buffer").fetchone()[0]
    conn.execute("DELETE FROM unknown_buffer")
    conn.commit()
    conn.close()
    print(f"  {n}개 삭제 완료")


# ══════════════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# 9. synonyms_pending 배치 처리 (synonym_filter.py 파이프라인 연결)
# ══════════════════════════════════════════════════════════════════════════════

def process_synonyms_pending(db_path: Path = TERM_DB) -> dict:
    """
    synonyms_pending에서 PENDING_LLM_DECISION 행 배치 처리.

    Flow:
      1. fetch_pending_for_llm()  → status='pending', primary_term=PENDING_LLM 행 조회
      2. call_llm()               → primary_term / confidence 결정
      3. update_llm_result()      → synonyms_pending primary_term/confidence 확정
      4. apply_gate()             → approved / pending / rejected / conflict
      5. 결과별 처리:
           approved  → terms 테이블 등록
           conflict  → mark_conflict() (TTL 재평가 대상)
           pending   → synonyms_pending에 primary_term 확정 상태로 유지
           rejected  → mark_rejected() (high-conf drift, 강한 차단)

    Returns:
        {approved, pending, rejected, skipped, llm_errors}
    """
    try:
        from onew_core.synonym_filter import (
            fetch_pending_for_llm, update_llm_result,
            mark_rejected as _sf_mark_rejected,
            mark_conflict as _sf_mark_conflict,
        )
    except ImportError as e:
        logger.error("[synonyms] synonym_filter import 실패: %s", e)
        return dict(approved=0, pending=0, rejected=0, skipped=0, llm_errors=1)

    rows = fetch_pending_for_llm(limit=BATCH_SIZE)
    if not rows:
        logger.info("[synonyms] synonyms_pending 처리 대상 없음")
        return dict(approved=0, pending=0, rejected=0, skipped=0, llm_errors=0)

    stats = dict(approved=0, pending=0, rejected=0, skipped=0, llm_errors=0)
    print(f"[synonyms] {len(rows)}개 synonym 후보 처리 중...")

    # call_llm() 입력 형식으로 변환 (variant → term 매핑)
    # original_queries는 없으므로 빈 배열 문자열 전달
    batch_for_llm = [
        {
            "term":             r["variant"],
            "count":            r["count"],
            "original_queries": "[]",
        }
        for r in rows
    ]

    llm_results = call_llm(batch_for_llm)
    if not llm_results:
        stats["llm_errors"] += 1
        logger.error("[synonyms] LLM 결과 없음 — 배치 스킵")
        return stats

    # "term" 키 없는 항목 방어 필터 (call_llm mock / 예외 경로 대비)
    llm_map: dict[str, dict] = {r["term"]: r for r in llm_results if "term" in r}
    if not llm_map:
        stats["llm_errors"] += 1
        logger.error("[synonyms] llm_map 비어있음 (유효 term 없음) — 배치 스킵")
        return stats

    conn = get_conn(db_path)

    for sp_row in rows:
        variant = sp_row["variant"]
        row_id  = sp_row["id"]

        if variant not in llm_map:
            stats["skipped"] += 1
            logger.debug("[synonyms] LLM 결과 없음(스킵): %r", variant)
            continue

        item = llm_map[variant]

        # synonyms_pending의 primary_term + confidence 확정
        update_llm_result(row_id, item["primary_term"], item["confidence"])

        # apply_gate용 mock row (sqlite3.Row 대신 dict — 동일하게 키 접근 지원)
        mock_row = {
            "count":            sp_row["count"],
            "original_queries": "[]",          # source_hashes_json이 우선 사용됨
        }
        source_hashes_json = sp_row.get("source_hashes")  # 실제 문서 경로 목록

        decision = apply_gate(conn, item, mock_row,
                              source_hashes_json=source_hashes_json)

        if decision == "approved":
            _write_to_terminology(conn, variant, item["primary_term"], item["confidence"])
            stats["approved"] += 1
            print(f"  ✓ [syn] 승인: {variant!r} → {item['primary_term']!r} "
                  f"({item['confidence']:.2f})")

        elif decision == "conflict":
            _sf_mark_conflict(row_id,
                              f"DRIFT conf={item['confidence']:.2f}: "
                              f"기존 매핑 충돌 — 수동 검토 필요")
            stats["pending"] += 1
            print(f"  ⚠️  [syn] 충돌: {variant!r} → {item['primary_term']!r} "
                  f"(conf={item['confidence']:.2f})")

        elif decision == "pending":
            # Gate 조건 미달 — primary_term은 확정됐으나 증거 부족
            # synonyms_pending에 primary_term 확정 상태로 잔류 (추가 누적 대기)
            stats["pending"] += 1
            print(f"  ⏳ [syn] 보류: {variant!r} → {item['primary_term']!r} "
                  f"({item['confidence']:.2f})")

        else:  # rejected (high-conf drift, conf >= 0.9)
            _sf_mark_rejected(row_id,
                              f"DRIFT conf≥0.9: 기존 매핑 충돌, 강한 차단")
            stats["rejected"] += 1
            print(f"  ✗ [syn] 거부: {variant!r} (Drift 강한차단)")

    if stats["approved"] > 0:
        conn.commit()
        # TerminologyIndex 갱신
        try:
            sys.path.insert(0, str(SYSTEM_DIR / "onew_core"))
            from terminology_server import get_index
            get_index()._reload()
            logger.info("[synonyms] TerminologyIndex 갱신 완료")
        except Exception as e:
            logger.warning("[synonyms] TerminologyIndex 갱신 실패: %s", e)
    else:
        conn.commit()

    conn.close()
    return stats


def run():
    """배치 1회 실행 진입점 (cron/수동) — unknown_buffer + synonyms_pending 모두 처리."""
    init_learner_db()

    # TTL 복구: 7일 경과한 rejected/conflict → pending 재평가
    try:
        from onew_core.synonym_filter import recover_ttl
        recovered = recover_ttl()
        if recovered:
            print(f"[ttl] {recovered}개 항목 pending 복구 (rejected/conflict → pending)")
    except ImportError:
        pass

    # unknown_buffer (검색 미달 용어) 처리
    result = process_batch()
    print(
        f"\n[unknown_buffer] 승인={result['approved']} 보류={result['pending']} "
        f"블랙={result['blacklisted']} 스킵={result['skipped']} "
        f"LLM오류={result['llm_errors']}"
    )

    # synonyms_pending (synonym 후보) 처리
    syn_result = process_synonyms_pending()
    print(
        f"[synonyms_pending] 승인={syn_result['approved']} 보류={syn_result['pending']} "
        f"거부={syn_result['rejected']} 스킵={syn_result['skipped']} "
        f"LLM오류={syn_result['llm_errors']}"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if "--stats" in sys.argv:
        init_learner_db()
        _cmd_stats()
    elif "--pending" in sys.argv:
        init_learner_db()
        _cmd_pending()
    elif "--init" in sys.argv:
        init_learner_db()
        init_blacklist()
        print("  [init] DB 테이블 + blacklist 초기화 완료")
    elif "--flush" in sys.argv:
        _cmd_flush()
    elif "--synonyms" in sys.argv:
        # synonyms_pending 파이프라인만 단독 실행
        init_learner_db()
        result = process_synonyms_pending()
        print(
            f"\n[synonyms] 승인={result['approved']} 보류={result['pending']} "
            f"거부={result['rejected']} 스킵={result['skipped']} "
            f"LLM오류={result['llm_errors']}"
        )
    else:
        run()
