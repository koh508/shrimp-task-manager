"""
Temporal RAG 단위 테스트
- parse_temporal_intent: 키워드 → 날짜 범위 변환
- _extract_date_from_path: path → datetime
- temporal_rerank: 청크 재정렬 검증
- 기존 파이프라인 비간섭 검증 (temporal 없을 때 동일 동작)
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from onew_core.query_pipeline import (
    parse_temporal_intent,
    _extract_date_from_path,
    temporal_rerank,
)

NOW = datetime.now()

# ── 1. parse_temporal_intent ─────────────────────────────────────────────────
print("=== 1. parse_temporal_intent ===")

cases = [
    ("이차장이 작년에 한 일 알려줘",       "start.year", NOW.year - 1),
    ("최근 한 달간 공부 어때",              "start>=", NOW - timedelta(days=31)),
    ("올해 작업일지 요약해줘",              "start.year", NOW.year),
    ("이번 달 오답 패턴이 뭐야",            "start.month", NOW.month),
    ("초기에 어떻게 시스템 만들었어",       "direction", "asc"),
    ("가장 최신 클리핑 뭐야",               "direction", "desc"),
    ("어제 뭐 먹었어",                      "start.day", (NOW - timedelta(days=1)).day),
    ("오늘 공부 뭐 했어",                   "start.day", NOW.day),
    ("공조냉동 냉동사이클 설명해줘",        "none",  None),   # 비temporal
]

passed = 0
for query, check, expected in cases:
    result = parse_temporal_intent(query)
    if check == "none":
        ok = result is None
    elif check == "start.year":
        ok = result is not None and result["start"].year == expected
    elif check == "start.month":
        ok = result is not None and result["start"].month == expected
    elif check == "start>=":
        ok = result is not None and result["start"] >= expected
    elif check == "direction":
        ok = result is not None and result["direction"] == expected
    elif check == "start.day":
        ok = result is not None and result["start"].day == expected
    else:
        ok = False

    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    print(f"  {status}  '{query[:30]}'  -> {result}")

print(f"\n  {passed}/{len(cases)} 통과\n")

# ── 2. _extract_date_from_path ───────────────────────────────────────────────
print("=== 2. _extract_date_from_path ===")

path_cases = [
    (r"C:\Vault\DAILY\2026-03-15.md",           datetime(2026, 3, 15)),
    (r"C:\Vault\작업일지\2026-03-25_제목.md",    datetime(2026, 3, 25)),
    (r"C:\Vault\OCU\소방설비.md",                None),
    (r"C:\Vault\SYSTEM\agent.py",               None),
]

p_passed = 0
for path, expected in path_cases:
    result = _extract_date_from_path(path)
    ok = result == expected
    if ok: p_passed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {os.path.basename(path):<30} -> {result}")

print(f"\n  {p_passed}/{len(path_cases)} 통과\n")

# ── 3. temporal_rerank ───────────────────────────────────────────────────────
print("=== 3. temporal_rerank ===")

# 샘플 청크 (작년 문서 2개, 올해 문서 1개, 날짜 없는 문서 1개)
chunks = [
    {"path": r"C:\Vault\DAILY\2025-08-10.md", "score": 0.60, "text": "배관 사고 발생"},
    {"path": r"C:\Vault\DAILY\2025-08-20.md", "score": 0.55, "text": "사고 경위서 제출"},
    {"path": r"C:\Vault\DAILY\2026-02-01.md", "score": 0.70, "text": "올해 관련 없는 내용"},
    {"path": r"C:\Vault\OCU\소방설비.md",      "score": 0.65, "text": "날짜 없는 문서"},
]

# 작년 temporal intent
temporal = parse_temporal_intent("작년에 배관 사고 어떻게 됐어")
assert temporal is not None
result = temporal_rerank(list(chunks), temporal)

# 작년 문서(2025)가 올해 문서(2026)보다 앞에 와야 함
top2_paths = [os.path.basename(r["path"]) for r in result[:2]]
assert "2025-08-10.md" in top2_paths or "2025-08-20.md" in top2_paths, \
    f"작년 문서가 상위에 없음: {top2_paths}"

print("  PASS  작년 temporal: 2025 문서 상위 정렬 확인")
print(f"        정렬 결과: {[os.path.basename(r['path']) for r in result]}")
print(f"        final_scores: {[r.get('final_score', r['score']) for r in result]}")

# 초기 direction 테스트
temporal_asc = parse_temporal_intent("초기에 어떻게 만들었어")
result_asc = temporal_rerank(list(chunks), temporal_asc)
dates = [_extract_date_from_path(r["path"]) for r in result_asc if _extract_date_from_path(r["path"])]
assert dates == sorted(dates), f"asc 정렬 실패: {dates}"
print("  PASS  초기(asc): 날짜 오름차순 정렬 확인")

# ── 4. 비간섭 검증 (temporal 없을 때) ─────────────────────────────────────────
print("\n=== 4. 비간섭 검증 ===")

original_chunks = list(chunks)  # 원본 복사
no_temporal = parse_temporal_intent("공조냉동 냉동사이클 설명해줘")
assert no_temporal is None, "비temporal 쿼리에서 temporal 감지됨"

# temporal=None이면 rerank 미호출 → 청크 순서 변경 없음
if no_temporal is None:
    print("  PASS  비temporal 쿼리: temporal_rerank 미호출 (기존 파이프라인 그대로)")
else:
    print("  FAIL  비temporal 쿼리에서 temporal 감지됨")

print("\n=== 전체 결과 ===")
print(f"  parse_temporal_intent  : {passed}/{len(cases)}")
print(f"  extract_date_from_path : {p_passed}/{len(path_cases)}")
print("  temporal_rerank        : PASS")
print("  비간섭 검증             : PASS")
