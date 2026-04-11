"""
test_safety_guards.py — Task 2~4 안전 가드레일 단위 테스트

[검증 항목]
- soften_response: 단정 표현 치환, 정상 텍스트 무변경
- is_medical_decision_query: 의료 결정 감지 / 오탐 방지
- is_analysis_query: 분석 쿼리 감지 / 일반 쿼리 오탐 방지
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from onew_core.query_pipeline import (
    soften_response,
    is_medical_decision_query,
    is_analysis_query,
)

pass_count = 0
fail_count = 0

def check(label: str, condition: bool):
    global pass_count, fail_count
    status = "PASS" if condition else "FAIL"
    if condition:
        pass_count += 1
    else:
        fail_count += 1
    print(f"  {status}  {label}")


# ── Task 2: soften_response ───────────────────────────────────────────────────
print("=== Task 2: soften_response ===")

r1 = soften_response("스트레스 때문입니다.")
check("'때문입니다' → 치환됨", "때문입니다" not in r1)
check("치환 후 텍스트 있음", len(r1) > 0)

r2 = soften_response("확실히 원인입니다.")
check("'확실히' + '원인입니다' 동시 치환", "확실히" not in r2 and "원인입니다" not in r2)

r3 = soften_response("오늘 날씨가 좋아요.")
check("일반 문장 무변경", r3 == "오늘 날씨가 좋아요.")

r4 = soften_response("반드시 암기해야 합니다.")  # '반드시'는 치환 대상 아님 (공부용)
check("'반드시' 미치환 (학습 표현 보호)", "반드시" in r4)

r5 = soften_response("틀림없이 그것이 명확합니다.")
check("'틀림없이' + '명확합니다' 치환", "틀림없이" not in r5 and "명확합니다" not in r5)

print()

# ── Task 3: is_medical_decision_query ─────────────────────────────────────────
print("=== Task 3: is_medical_decision_query ===")

check("'약 먹어야 해?' → True",   is_medical_decision_query("약 먹어야 해?"))
check("'병원 가야 해?' → True",   is_medical_decision_query("병원 가야 해?"))
check("'이 증상 뭐야?' → True",   is_medical_decision_query("이 증상 뭐야?"))
check("'검사 받아야 할까?' → True", is_medical_decision_query("검사 받아야 할까?"))

# 오탐 방지: 이것들은 False여야 함
check("'건강 기준 냉동용량' → False",
      not is_medical_decision_query("건강 기준 냉동용량은?"))
check("'소방 건강 규정' → False",
      not is_medical_decision_query("소방 건강 규정 알려줘"))
check("'수면제 먹었다' → False",
      not is_medical_decision_query("어제 수면제 먹었다"))
check("'약 공부했어' → False",
      not is_medical_decision_query("오늘 약 공부했어"))

print()

# ── Task 4: is_analysis_query ─────────────────────────────────────────────────
print("=== Task 4: is_analysis_query ===")

check("'요즘 왜 이렇게 피곤해?' → True",
      is_analysis_query("요즘 왜 이렇게 피곤해?"))
check("'내 패턴이 뭐야?' → True",
      is_analysis_query("내 패턴이 뭐야?"))
check("'원인이 뭐야?' → True",
      is_analysis_query("원인이 뭐야?"))
check("'컨디션 왜 이래?' → True",
      is_analysis_query("컨디션 왜 이래?"))
check("'분석해 줘' → True",
      is_analysis_query("요즘 생활 패턴 분석해 줘"))

# 오탐 방지: 일반 쿼리
check("'냉동효과 공식' → False",
      not is_analysis_query("냉동효과 공식이 뭐야?"))
check("'이차장 전화번호' → False",
      not is_analysis_query("이차장 전화번호 뭐야?"))
check("'오늘 뭐 먹었어' → False",
      not is_analysis_query("오늘 뭐 먹었어?"))
check("'공조냉동 설명해줘' → False",
      not is_analysis_query("공조냉동 냉동사이클 설명해줘"))

print()
print(f"=== 결과: {pass_count}/{pass_count+fail_count} 통과 ===")
if fail_count:
    print(f"  FAIL {fail_count}개 확인 필요")
