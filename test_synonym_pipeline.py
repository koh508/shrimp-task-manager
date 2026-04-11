"""
test_synonym_pipeline.py — synonym 파이프라인 시나리오 테스트

[테스트 시나리오]
  1. enqueue_candidate() 직접 호출 → synonyms_pending DB 삽입 확인
  2. 중복 삽입 → count 누적 + EMA confidence 확인
  3. filter_step1() 탈락 케이스 확인 (STOPWORD, NON_KOREAN, LENGTH_TOO_SHORT)
  4. mark_rejected() → ALREADY_REJECTED 재등록 차단 확인
  5. recover_ttl() → 오래된 rejected 항목 pending 복구 확인
  6. WHERE fallback 시뮬레이션 → query_pipeline이 enqueue_candidate를 호출하는지 확인

[실행]
  python test_synonym_pipeline.py
"""

from __future__ import annotations
import sys
import os
import sqlite3
import io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# 경로 설정
SYSTEM_DIR = Path(__file__).parent
sys.path.insert(0, str(SYSTEM_DIR))

TERM_DB = SYSTEM_DIR / "onew_terminology.db"

# ── 색상 출력 ─────────────────────────────────────────────────────────────────
def ok(msg):  print(f"  ✓  {msg}")
def fail(msg):print(f"  ✗  {msg}"); sys.exit(1)
def info(msg):print(f"  ·  {msg}")
def head(msg):print(f"\n[{msg}]")


# ══════════════════════════════════════════════════════════════════════════════
# 헬퍼: synonyms_pending 조회
# ══════════════════════════════════════════════════════════════════════════════

def fetch_row(variant: str, primary_term: str = "PENDING_LLM_DECISION") -> dict | None:
    conn = sqlite3.connect(str(TERM_DB))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM synonyms_pending WHERE variant=? AND primary_term=?",
        (variant, primary_term),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_test_rows(*variants):
    """테스트 데이터 정리."""
    conn = sqlite3.connect(str(TERM_DB))
    for v in variants:
        conn.execute("DELETE FROM synonyms_pending WHERE variant=?", (v,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Test 1: 기본 삽입
# ══════════════════════════════════════════════════════════════════════════════

def test_basic_insert():
    head("Test 1: 기본 삽입")
    from onew_core.synonym_filter import enqueue_candidate

    delete_test_rows("감온기")

    ok_flag, action = enqueue_candidate(
        "감온기",
        source_hashes=["DAILY/2024-05-10.md", "DAILY/2024-06-01.md"],
        count=2,
        confidence=0.0,
    )

    assert ok_flag, f"enqueue 실패: {action}"
    assert action == "INSERTED", f"예상 INSERTED, 실제 {action}"
    ok(f"삽입 완료 ({action})")

    row = fetch_row("감온기")
    assert row is not None, "DB에서 행 못찾음"
    assert row["count"] == 2, f"count 불일치: {row['count']}"
    assert row["status"] == "pending"
    assert row["primary_term"] == "PENDING_LLM_DECISION"
    info(f"count={row['count']}, status={row['status']}, source_docs={row['source_docs']}")
    ok("DB 내용 검증 완료")


# ══════════════════════════════════════════════════════════════════════════════
# Test 2: 중복 삽입 → count 누적 + EMA
# ══════════════════════════════════════════════════════════════════════════════

def test_update_accumulation():
    head("Test 2: 중복 삽입 → count 누적 + EMA confidence")
    from onew_core.synonym_filter import enqueue_candidate

    # 첫 삽입 (confidence=0.6)
    delete_test_rows("압축기")
    enqueue_candidate("압축기", source_hashes=["doc_a.md"], count=1, confidence=0.6)
    row1 = fetch_row("압축기")
    assert row1["confidence"] == 0.6, f"cold-start confidence 불일치: {row1['confidence']}"
    ok(f"cold-start confidence={row1['confidence']:.2f}")

    # 두 번째 삽입 (confidence=0.8) → EMA: 0.6*0.7 + 0.8*0.3 = 0.66
    enqueue_candidate("압축기", source_hashes=["doc_b.md"], count=3, confidence=0.8)
    row2 = fetch_row("압축기")
    expected_conf = round(0.6 * 0.7 + 0.8 * 0.3, 4)
    assert abs(row2["confidence"] - expected_conf) < 0.001, \
        f"EMA 불일치: 기대={expected_conf:.4f} 실제={row2['confidence']:.4f}"
    assert row2["count"] == 4, f"count 누적 불일치: {row2['count']}"
    assert row2["source_docs"] == 2, f"source_docs 불일치: {row2['source_docs']}"
    info(f"count={row2['count']}, conf={row2['confidence']:.4f} (기대 {expected_conf:.4f}), source_docs={row2['source_docs']}")
    ok("누적 + EMA 검증 완료")


# ══════════════════════════════════════════════════════════════════════════════
# Test 3: filter_step1 탈락 케이스
# ══════════════════════════════════════════════════════════════════════════════

def test_filter_rejects():
    head("Test 3: filter_step1 탈락 케이스")
    from onew_core.synonym_filter import enqueue_candidate

    cases = [
        ("가",     "LENGTH_TOO_SHORT"),
        ("hello",  "NON_KOREAN"),
        ("어떤",   "STOPWORD"),
    ]

    for term, expected_code in cases:
        ok_flag, code = enqueue_candidate(term, count=1)
        assert not ok_flag, f"{term!r}: 탈락해야 하는데 통과됨"
        assert code == expected_code, f"{term!r}: 예상={expected_code} 실제={code}"
        ok(f"{term!r} → {code}")


# ══════════════════════════════════════════════════════════════════════════════
# Test 4: mark_rejected → ALREADY_REJECTED 차단
# ══════════════════════════════════════════════════════════════════════════════

def test_rejected_block():
    head("Test 4: mark_rejected → ALREADY_REJECTED 재등록 차단")
    from onew_core.synonym_filter import enqueue_candidate, mark_rejected

    delete_test_rows("응축기")
    ok_flag, _ = enqueue_candidate("응축기", count=1, confidence=0.5)
    assert ok_flag

    row = fetch_row("응축기")
    mark_rejected(row["id"], "TEST: 수동 거부")
    ok("mark_rejected 호출 완료")

    # 재등록 시도
    ok_flag2, code2 = enqueue_candidate("응축기", count=1, confidence=0.7)
    assert not ok_flag2, "rejected 항목이 재등록됨 (차단 실패)"
    assert code2 == "ALREADY_REJECTED", f"예상 ALREADY_REJECTED, 실제 {code2}"
    ok(f"재등록 차단 확인: {code2}")


# ══════════════════════════════════════════════════════════════════════════════
# Test 5: recover_ttl → 오래된 rejected → pending 복구
# ══════════════════════════════════════════════════════════════════════════════

def test_recover_ttl():
    head("Test 5: recover_ttl → 오래된 rejected → pending 복구")
    from onew_core.synonym_filter import enqueue_candidate, mark_rejected, recover_ttl

    delete_test_rows("냉각기")
    enqueue_candidate("냉각기", count=1, confidence=0.4)
    row = fetch_row("냉각기")
    mark_rejected(row["id"], "TEST: TTL 테스트용 거부")

    # rejected_at을 8일 전으로 조작
    past = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%S")
    conn = sqlite3.connect(str(TERM_DB))
    conn.execute(
        "UPDATE synonyms_pending SET rejected_at=? WHERE id=?",
        (past, row["id"]),
    )
    conn.commit()
    conn.close()
    ok(f"rejected_at을 8일 전으로 조작: {past}")

    recovered = recover_ttl(days=7)
    assert recovered >= 1, f"복구 건수 0 (expected ≥1): {recovered}"
    ok(f"복구 건수: {recovered}개")

    row_after = fetch_row("냉각기")
    assert row_after["status"] == "pending", f"status 불일치: {row_after['status']}"
    assert row_after["rejected_at"] is None, "rejected_at이 초기화되지 않음"
    ok("status=pending, rejected_at=NULL 확인")


# ══════════════════════════════════════════════════════════════════════════════
# Test 6: WHERE fallback 시뮬레이션 → query_pipeline 연동
# ══════════════════════════════════════════════════════════════════════════════

def test_fallback_enqueue_simulation():
    """
    query_pipeline의 WHERE fallback 코드와 동일한 로직을 직접 실행해서
    enqueue_candidate()가 정상 호출되는지 검증한다.
    LanceDB 없이 호출 경로만 테스트 (DB 삽입 여부로 판단).
    """
    head("Test 6: fallback 시뮬레이션 → enqueue_candidate 연동 확인")
    from onew_core.synonym_filter import enqueue_candidate as _enq

    delete_test_rows("보온재")

    # query_pipeline WHERE fallback 블록과 동일한 패턴
    _synonym_hits = {"보온재": ["DAILY/2024-08-15.md", "DAILY/2024-09-03.md"]}

    import threading
    def _enqueue_batch(_hits=_synonym_hits):
        for _tok, _paths in _hits.items():
            _enq(_tok, source_hashes=_paths, count=1)

    t = threading.Thread(target=_enqueue_batch, daemon=True)
    t.start()
    t.join(timeout=3)

    row = fetch_row("보온재")
    assert row is not None, "스레드 enqueue 후 DB에서 행 못찾음"
    assert row["status"] == "pending"
    assert row["source_docs"] == 2
    info(f"variant={row['variant']}, source_docs={row['source_docs']}, status={row['status']}")
    ok("threading 기반 enqueue 정상 동작 확인")


# ══════════════════════════════════════════════════════════════════════════════
# Test 7: fetch_pending_for_llm → async_learner 연동 확인
# ══════════════════════════════════════════════════════════════════════════════

def test_fetch_pending():
    head("Test 7: fetch_pending_for_llm → async_learner 배치 입력 확인")
    from onew_core.synonym_filter import fetch_pending_for_llm

    rows = fetch_pending_for_llm(limit=10)
    info(f"현재 PENDING_LLM_DECISION 행: {len(rows)}개")
    if rows:
        sample = rows[0]
        assert "variant" in sample
        assert "count" in sample
        assert "source_hashes" in sample
        ok(f"샘플: variant={sample['variant']!r}, count={sample['count']}, source_docs={sample['source_docs']}")
    else:
        ok("(현재 PENDING 행 없음 — 정상)")


# ══════════════════════════════════════════════════════════════════════════════
# 정리
# ══════════════════════════════════════════════════════════════════════════════

def cleanup():
    delete_test_rows("감온기", "압축기", "응축기", "냉각기", "보온재")


# ══════════════════════════════════════════════════════════════════════════════
# 진입점
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  synonym 파이프라인 시나리오 테스트")
    print("=" * 60)

    try:
        test_basic_insert()
        test_update_accumulation()
        test_filter_rejects()
        test_rejected_block()
        test_recover_ttl()
        test_fallback_enqueue_simulation()
        test_fetch_pending()
    finally:
        cleanup()
        info("테스트 데이터 정리 완료")

    print("\n" + "=" * 60)
    print("  전체 통과")
    print("=" * 60)
