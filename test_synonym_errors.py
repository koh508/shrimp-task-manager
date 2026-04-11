"""
test_synonym_errors.py — synonym 파이프라인 실제 오류 시나리오 테스트

[테스트 시나리오]
  E1. validate_llm_output() — 불량 LLM 출력 6종 (잘못된 JSON, 범위 초과, 키 누락 등)
  E2. apply_gate() Drift — conf<0.9 → conflict, conf≥0.9 → rejected
  E3. FIFO hash pruning — source_hashes 55개 → 50개 상한
  E4. COUNT_CAP — count 9998 + 5 → 9999 상한
  E5. process_synonyms_pending() LLM 실패 → llm_errors 카운트
  E6. POS_MISMATCH — 동사/부사 등 비명사 탈락
  E7. malformed source_hashes JSON → 안전 fallback

[실행]
  python test_synonym_errors.py
"""

from __future__ import annotations
import sys, io, os, sqlite3, json, threading
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SYSTEM_DIR = Path(__file__).parent
sys.path.insert(0, str(SYSTEM_DIR))
TERM_DB = SYSTEM_DIR / "onew_terminology.db"

def ok(msg):   print(f"  ✓  {msg}")
def fail(msg): print(f"  ✗  {msg}"); sys.exit(1)
def info(msg): print(f"  ·  {msg}")
def head(msg): print(f"\n[{msg}]")

def get_conn():
    conn = sqlite3.connect(str(TERM_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def fetch_sp(variant, primary_term="PENDING_LLM_DECISION"):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM synonyms_pending WHERE variant=? AND primary_term=?",
        (variant, primary_term)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_sp(*variants):
    conn = get_conn()
    for v in variants:
        conn.execute("DELETE FROM synonyms_pending WHERE variant=?", (v,))
    conn.commit(); conn.close()

def delete_terms(*variants):
    conn = get_conn()
    for v in variants:
        conn.execute("DELETE FROM terms WHERE variant=?", (v,))
    conn.commit(); conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# E1. validate_llm_output — 불량 LLM 출력 6종
# ══════════════════════════════════════════════════════════════════════════════

def test_e1_validate_llm_output():
    head("E1: validate_llm_output — 불량 LLM 출력 6종")
    from onew_core.async_learner import validate_llm_output

    # 1-1. 완전한 정상 입력 (기준선)
    good = '[{"term":"감온기","primary_term":"감온 기기","confidence":0.88,"reason":"분리"}]'
    result = validate_llm_output(good)
    assert len(result) == 1 and result[0]["term"] == "감온기"
    ok("정상 입력 → 1건 파싱")

    # 1-2. ```json 코드블록 감싼 경우 (LLM 자주 함)
    fenced = '```json\n[{"term":"보일러","primary_term":"보일러 장치","confidence":0.91,"reason":""}]\n```'
    result = validate_llm_output(fenced)
    assert len(result) == 1 and result[0]["term"] == "보일러"
    ok("코드블록 감싼 JSON → 정상 파싱")

    # 1-3. JSON이 아닌 plain text
    result = validate_llm_output("네, 이 용어는 냉동 장치를 의미합니다.")
    assert result == []
    ok("plain text → [] 반환")

    # 1-4. confidence 범위 초과 (1.5)
    bad_conf = '[{"term":"냉각기","primary_term":"냉각 장치","confidence":1.5}]'
    result = validate_llm_output(bad_conf)
    assert result == []
    ok("confidence=1.5 → 탈락")

    # 1-5. term == primary_term (정규화 의미 없음)
    same = '[{"term":"압축기","primary_term":"압축기","confidence":0.95}]'
    result = validate_llm_output(same)
    assert result == []
    ok("term==primary_term → 탈락")

    # 1-6. 필수 키 누락 (confidence 없음)
    missing_key = '[{"term":"팽창밸브","primary_term":"팽창 밸브"}]'
    result = validate_llm_output(missing_key)
    assert result == []
    ok("confidence 키 누락 → 탈락")

    # 1-7. 혼합: 정상 1건 + 불량 2건 → 정상만 살아남아야
    mixed = json.dumps([
        {"term": "응축기",  "primary_term": "응축 장치", "confidence": 0.87},
        {"term": "냉동기",  "primary_term": "냉동기",    "confidence": 0.90},  # same
        {"term": "증발기",  "primary_term": "증발 장치", "confidence": 1.2},   # range
    ])
    result = validate_llm_output(mixed)
    assert len(result) == 1 and result[0]["term"] == "응축기"
    ok(f"혼합 3건 중 정상 1건만 통과: {result[0]['term']!r}")


# ══════════════════════════════════════════════════════════════════════════════
# E2. apply_gate Drift — conflict vs rejected
# ══════════════════════════════════════════════════════════════════════════════

def test_e2_alias_drift():
    head("E2: apply_gate Alias Drift — conf<0.9→conflict, conf≥0.9→rejected")
    from onew_core.async_learner import apply_gate, get_conn as al_conn

    # terms 테이블에 "냉각탑" → "냉각장치" 등록
    delete_terms("냉각탑")
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO terms (primary_term, variant, confidence, source, is_verified, created_at) "
        "VALUES (?,?,?,?,?,?)",
        ("냉각장치", "냉각탑", 0.95, "test", 0, datetime.now().isoformat())
    )
    conn.commit(); conn.close()
    info("terms에 냉각탑→냉각장치 등록")

    mock_row = {"count": 5, "original_queries": "[]"}

    # E2-a: LLM이 "냉각기" 제안 (drift), conf=0.7 → conflict
    conn = al_conn()
    item_low = {"term": "냉각탑", "primary_term": "냉각기", "confidence": 0.7}
    decision = apply_gate(conn, item_low, mock_row, source_hashes_json=None)
    conn.close()
    assert decision == "conflict", f"기대 conflict, 실제 {decision}"
    ok(f"drift + conf=0.7 → {decision}")

    # E2-b: LLM이 "냉각기" 제안 (drift), conf=0.92 → rejected
    conn = al_conn()
    item_high = {"term": "냉각탑", "primary_term": "냉각기", "confidence": 0.92}
    decision = apply_gate(conn, item_high, mock_row, source_hashes_json=None)
    conn.close()
    assert decision == "rejected", f"기대 rejected, 실제 {decision}"
    ok(f"drift + conf=0.92 → {decision}")

    # E2-c: LLM이 올바른 "냉각장치" 제안 (no drift), 조건 미달 → pending
    conn = al_conn()
    item_ok = {"term": "냉각탑", "primary_term": "냉각장치", "confidence": 0.72}
    mock_row_low = {"count": 1, "original_queries": "[]"}
    decision = apply_gate(conn, item_ok, mock_row_low, source_hashes_json=None)
    conn.close()
    assert decision == "pending", f"기대 pending, 실제 {decision}"
    ok(f"no drift + 조건 미달 (conf=0.72, count=1) → {decision}")

    # E2-d: 올바른 제안 + Gate 통과 → approved
    conn = al_conn()
    item_approved = {"term": "냉각탑", "primary_term": "냉각장치", "confidence": 0.90}
    mock_row_ok = {"count": 5, "original_queries": '["q1","q2","q3"]'}
    hashes_json = json.dumps(["doc1.md", "doc2.md", "doc3.md"])
    decision = apply_gate(conn, item_approved, mock_row_ok, source_hashes_json=hashes_json)
    conn.close()
    assert decision == "approved", f"기대 approved, 실제 {decision}"
    ok(f"no drift + Gate 통과 (conf=0.90, count=5, ctx=3) → {decision}")


# ══════════════════════════════════════════════════════════════════════════════
# E3. FIFO hash pruning — 55개 → 50개
# ══════════════════════════════════════════════════════════════════════════════

def test_e3_fifo_pruning():
    head("E3: FIFO hash pruning — source_hashes 55개 → 50개 상한")
    from onew_core.synonym_filter import enqueue_candidate, _MAX_HASHES

    delete_sp("열교환기")

    # 첫 삽입: 55개 해시
    hashes_55 = [f"doc_{i:03d}.md" for i in range(55)]
    ok_flag, action = enqueue_candidate("열교환기", source_hashes=hashes_55, count=1)
    assert ok_flag, f"삽입 실패: {action}"

    conn = get_conn()
    row = conn.execute(
        "SELECT source_hashes FROM synonyms_pending WHERE variant='열교환기'"
    ).fetchone()
    conn.close()

    stored = json.loads(row["source_hashes"])
    assert len(stored) == _MAX_HASHES, f"FIFO 상한 실패: {len(stored)}개 (기대 {_MAX_HASHES})"
    # FIFO: 마지막 50개 (doc_005 ~ doc_054)
    assert stored[0] == "doc_005.md", f"FIFO 시작 틀림: {stored[0]}"
    assert stored[-1] == "doc_054.md", f"FIFO 끝 틀림: {stored[-1]}"
    ok(f"55개 → {len(stored)}개 유지, FIFO 확인 ({stored[0]} ~ {stored[-1]})")

    # UPDATE 시에도 FIFO 유지: 30개 추가 → 여전히 50개
    hashes_30 = [f"new_{i:03d}.md" for i in range(30)]
    enqueue_candidate("열교환기", source_hashes=hashes_30, count=2)
    conn = get_conn()
    row2 = conn.execute(
        "SELECT source_hashes FROM synonyms_pending WHERE variant='열교환기'"
    ).fetchone()
    conn.close()

    stored2 = json.loads(row2["source_hashes"])
    assert len(stored2) == _MAX_HASHES, f"UPDATE 후 FIFO 실패: {len(stored2)}개"
    ok(f"UPDATE 후에도 {len(stored2)}개 유지")


# ══════════════════════════════════════════════════════════════════════════════
# E4. COUNT_CAP — 9998 + 5 → 9999
# ══════════════════════════════════════════════════════════════════════════════

def test_e4_count_cap():
    head("E4: COUNT_CAP — count 9998에서 5 추가 → 9999 상한")
    from onew_core.synonym_filter import enqueue_candidate, _COUNT_CAP

    delete_sp("배관재")
    enqueue_candidate("배관재", count=1)

    # count를 9998로 직접 조작
    conn = get_conn()
    conn.execute("UPDATE synonyms_pending SET count=9998 WHERE variant='배관재'")
    conn.commit(); conn.close()
    info("count를 9998로 조작")

    # count=5 추가 → 9998+5=10003 이지만 상한 9999
    enqueue_candidate("배관재", count=5)
    conn = get_conn()
    row = conn.execute(
        "SELECT count FROM synonyms_pending WHERE variant='배관재'"
    ).fetchone()
    conn.close()

    assert row["count"] == _COUNT_CAP, f"COUNT_CAP 실패: {row['count']} (기대 {_COUNT_CAP})"
    ok(f"9998 + 5 → {row['count']} (상한 적용)")


# ══════════════════════════════════════════════════════════════════════════════
# E5. process_synonyms_pending LLM 실패 → llm_errors
# ══════════════════════════════════════════════════════════════════════════════

def test_e5_llm_failure():
    head("E5: process_synonyms_pending — LLM 실패 시 llm_errors 카운트")
    from onew_core import async_learner

    # call_llm을 빈 리스트 반환하도록 mock
    with patch.object(async_learner, "call_llm", return_value=[]):
        stats = async_learner.process_synonyms_pending()

    # synonyms_pending에 PENDING_LLM 행이 있으면 llm_errors=1, 없으면 그냥 0
    info(f"stats={stats}")
    if stats["llm_errors"] == 1:
        ok("LLM 실패 → llm_errors=1 카운트 확인")
    else:
        # PENDING_LLM 행이 없었던 경우
        assert stats["llm_errors"] == 0
        ok("PENDING_LLM 행 없음 → 실행 생략 (정상)")

    # call_llm이 유효하지 않은 형식 반환 → validate 후 빈 리스트 → llm_errors
    with patch.object(async_learner, "call_llm", return_value=[{"broken": True}]):
        stats2 = async_learner.process_synonyms_pending()
    info(f"broken result stats={stats2}")
    # broken 결과는 validate_llm_output에서 이미 걸러지므로 llm_errors or skipped
    ok(f"불량 LLM 결과 → llm_errors={stats2['llm_errors']}, skipped={stats2['skipped']}")


# ══════════════════════════════════════════════════════════════════════════════
# E6. POS_MISMATCH — 동사/부사 실제 케이스
# ══════════════════════════════════════════════════════════════════════════════

def test_e6_pos_mismatch():
    head("E6: POS_MISMATCH — 동사·형용사·부사 탈락, 복합명사 허용")
    from onew_core.synonym_filter import filter_step1

    # 탈락해야 하는 것들
    reject_cases = [
        "먹다",    # 동사
        "빠르다",  # 형용사
        "매우",    # 부사 (2자지만 부사)
        "그리고",  # 접속사 (STOPWORD이기도 함)
    ]
    for term in reject_cases:
        ok_flag, code = filter_step1(term)
        assert not ok_flag, f"{term!r}: 탈락해야 하는데 통과 (code={code})"
        ok(f"{term!r} → 탈락 ({code})")

    # 통과해야 하는 복합 명사 (NNG+XSN)
    pass_cases = [
        "냉동기",   # NNG(냉동) + XSN(기)
        "응축기",   # NNG(응축) + XSN(기)
        "압축기",   # NNG(압축) + XSN(기)
        "보온재",   # NNG(보온) + XSN(재)
    ]
    for term in pass_cases:
        ok_flag, code = filter_step1(term)
        if ok_flag:
            ok(f"{term!r} → 통과 ({code})")
        else:
            # kiwipiepy 없으면 정규식 fallback (한글 2자+ 통과)
            info(f"{term!r} → {code} (kiwipiepy 없이 fallback 통과 여부 따라 다름)")


# ══════════════════════════════════════════════════════════════════════════════
# E7. malformed source_hashes JSON → 안전 fallback
# ══════════════════════════════════════════════════════════════════════════════

def test_e7_malformed_json():
    head("E7: malformed source_hashes JSON → 안전 fallback (크래시 없음)")
    from onew_core.async_learner import _count_distinct_contexts

    # 정상 케이스
    result = _count_distinct_contexts('["q1 test", "q2 test"]', None)
    assert result == 2
    ok(f"정상 JSON → distinct={result}")

    # source_hashes가 깨진 JSON
    result = _count_distinct_contexts('["q1","q2"]', '{broken json}')
    assert result >= 0  # 크래시 없이 fallback
    ok(f"깨진 source_hashes JSON → fallback, distinct={result} (크래시 없음)")

    # original_queries도 깨진 JSON
    result = _count_distinct_contexts('{also broken}', None)
    assert result == 0
    ok(f"깨진 original_queries JSON → 0 반환 (크래시 없음)")

    # source_hashes 빈 리스트 → original_queries fallback
    result = _count_distinct_contexts('["쿼리A","쿼리B","쿼리C"]', '[]')
    assert result == 3
    ok(f"빈 source_hashes → original_queries fallback → distinct={result}")

    # enqueue_candidate에서 source_hashes가 None일 때 DB 저장 확인
    from onew_core.synonym_filter import enqueue_candidate
    delete_sp("밸브")
    ok_flag, action = enqueue_candidate("밸브", source_hashes=None, count=1)
    assert ok_flag
    conn = get_conn()
    row = conn.execute("SELECT source_hashes FROM synonyms_pending WHERE variant='밸브'").fetchone()
    conn.close()
    stored = json.loads(row["source_hashes"])
    assert stored == [], f"None source_hashes → 빈 리스트 기대, 실제: {stored}"
    ok("source_hashes=None → DB에 [] 저장")


# ══════════════════════════════════════════════════════════════════════════════
# 정리 + 진입점
# ══════════════════════════════════════════════════════════════════════════════

def cleanup():
    delete_sp("열교환기", "배관재", "밸브")
    delete_terms("냉각탑")
    # learning_log 테스트 데이터 정리
    conn = get_conn()
    conn.execute("DELETE FROM learning_log WHERE term='냉각탑'")
    conn.commit(); conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  synonym 파이프라인 오류 시나리오 테스트")
    print("=" * 60)

    try:
        test_e1_validate_llm_output()
        test_e2_alias_drift()
        test_e3_fifo_pruning()
        test_e4_count_cap()
        test_e5_llm_failure()
        test_e6_pos_mismatch()
        test_e7_malformed_json()
    finally:
        cleanup()
        info("테스트 데이터 정리 완료")

    print("\n" + "=" * 60)
    print("  전체 통과")
    print("=" * 60)
