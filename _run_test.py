"""
온유 실전 테스트 스크립트 — 35문항
결과를 _test_results.json 에 저장
"""
import sys, json, time, re
from datetime import datetime

sys.path.insert(0, r"C:\Users\User\Documents\Obsidian Vault\SYSTEM")
from onew_core.system_prompt import build as build_prompt
from onew_core.query_pipeline import handle_query

sp = build_prompt("home")

# ── 35문항 정의 ──────────────────────────────────────────────────────────────
QUESTIONS = [
    # ── FACT 15개 ──────────────────────────────────────────────────────────
    {
        "id": "F01", "category": "FACT",
        "q": "산재 종결 예정일이 언제야?",
        "keywords": ["3월 20일", "2026.03.20", "종결"]
    },
    {
        "id": "F02", "category": "FACT",
        "q": "탈모약 받으러 가는 병원 이름이 뭐야?",
        "keywords": ["연세모베르의원", "연세모베르"]
    },
    {
        "id": "F03", "category": "FACT",
        "q": "3월 12일 근전도 검사 결과 신경 손상 수치가 얼마였어?",
        "keywords": ["40%", "40", "호전"]
    },
    {
        "id": "F04", "category": "FACT",
        "q": "LG그램 노트북 구매 총 비용이 얼마야?",
        "keywords": ["174만", "174", "138만"]
    },
    {
        "id": "F05", "category": "FACT",
        "q": "3월 카드값이 얼마 나왔어?",
        "keywords": ["90만원", "90만", "90"]
    },
    {
        "id": "F06", "category": "FACT",
        "q": "한라수목원 정신과 약 변경 예약 날짜가 언제야?",
        "keywords": ["3월 19일", "19일", "목요일"]
    },
    {
        "id": "F07", "category": "FACT",
        "q": "콘서타 약 용량이 몇 mg이야?",
        "keywords": ["18mg", "18", "콘서타"]
    },
    {
        "id": "F08", "category": "FACT",
        "q": "분리수거할 때 비닐류는 무슨 요일에 배출해?",
        "keywords": ["목요일", "일요일", "비닐"]
    },
    {
        "id": "F09", "category": "FACT",
        "q": "공조냉동기계기사 실기시험은 몇 월에 있어?",
        "keywords": ["4월", "5월", "실기"]
    },
    {
        "id": "F10", "category": "FACT",
        "q": "손해사정사 이름이 뭐야?",
        "keywords": ["김치안"]
    },
    {
        "id": "F11", "category": "FACT",
        "q": "API 과금이 얼마나 나왔어?",
        "keywords": ["6만6천원", "16만6천", "6만 6천", "66000"]
    },
    {
        "id": "F12", "category": "FACT",
        "q": "2월 25일에 장해 평가에서 목표한 등급이 몇 급이야?",
        "keywords": ["12급", "12등급"]
    },
    {
        "id": "F13", "category": "FACT",
        "q": "응축기 열통과율 구하는 공식에서 오염계수(Rf)는 어떻게 계산해?",
        "keywords": ["1/U", "hi", "ho", "Rf"]
    },
    {
        "id": "F14", "category": "FACT",
        "q": "양악수술 예상 비용이 얼마야?",
        "keywords": ["2350만", "2,350만", "3천만", "천만"]
    },
    {
        "id": "F15", "category": "FACT",
        "q": "3월 6일 근전도 검사 예약 시간이 몇 시야?",
        "keywords": ["13시 30분", "13:30", "오후 1시 30분"]
    },

    # ── HOWTO 10개 ─────────────────────────────────────────────────────────
    {
        "id": "H01", "category": "HOWTO",
        "q": "실손보험 청구할 때 어떤 서류가 필요해?",
        "keywords": ["지급확인원", "진료비", "영수증", "공단"]
    },
    {
        "id": "H02", "category": "HOWTO",
        "q": "공기선도 문제에서 급기량은 어떻게 계산해?",
        "keywords": ["현열부하", "SHF", "Qs", "Vs"]
    },
    {
        "id": "H03", "category": "HOWTO",
        "q": "부정적인 생각이 들 때 온유가 알려준 대처법이 뭐야?",
        "keywords": ["찬물 세수", "철봉", "물리적", "행동"]
    },
    {
        "id": "H04", "category": "HOWTO",
        "q": "온유 실행하는 방법이 뭐야?",
        "keywords": ["bat", "BAT", "바탕화면", "온유_실행"]
    },
    {
        "id": "H05", "category": "HOWTO",
        "q": "응축열량 Qc는 어떻게 계산해?",
        "keywords": ["냉각수", "비열", "유량", "온도차"]
    },
    {
        "id": "H06", "category": "HOWTO",
        "q": "분리수거 비닐류는 어떻게 배출해야 해?",
        "keywords": ["목요일", "일요일", "이틀만"]
    },
    {
        "id": "H07", "category": "HOWTO",
        "q": "공조냉동 공부할 때 단위 환산에서 주의할 점이 뭐야?",
        "keywords": ["kW", "kJ", "W", "단위"]
    },
    {
        "id": "H08", "category": "HOWTO",
        "q": "악마의 역학에서 의욕이 없을 때 어떻게 하라고 했어?",
        "keywords": ["엔트로피", "최소한", "방 청소", "10분"]
    },
    {
        "id": "H09", "category": "HOWTO",
        "q": "SSD 마이그레이션은 어떻게 했어?",
        "keywords": ["1TB", "256GB", "포맷", "마이그레이션"]
    },
    {
        "id": "H10", "category": "HOWTO",
        "q": "냉방 부하 계산에서 외기부하 현열은 어떻게 구해?",
        "keywords": ["ρ", "Cp", "온도차", "외기"]
    },

    # ── AMBIGUOUS 10개 ─────────────────────────────────────────────────────
    {
        "id": "A01", "category": "AMBIGUOUS",
        "q": "요즘 수면 컨디션 어때?",
        "keywords": ["수면", "잠", "컨디션"]
    },
    {
        "id": "A02", "category": "AMBIGUOUS",
        "q": "내 공부 패턴이 어떤 것 같아?",
        "keywords": ["공부", "인강", "패턴", "루틴"]
    },
    {
        "id": "A03", "category": "AMBIGUOUS",
        "q": "최근에 스트레스 많이 받았어?",
        "keywords": ["스트레스", "피로", "힘", "어렵"]
    },
    {
        "id": "A04", "category": "AMBIGUOUS",
        "q": "내 자존감 상태가 어때 보여?",
        "keywords": ["자존감", "외모", "자신"]
    },
    {
        "id": "A05", "category": "AMBIGUOUS",
        "q": "산재 이후 회사 복귀할 준비가 된 것 같아?",
        "keywords": ["회사", "산재", "복귀"]
    },
    {
        "id": "A06", "category": "AMBIGUOUS",
        "q": "공조냉동 시험 통과할 것 같아?",
        "keywords": ["공조냉동", "시험", "합격"]
    },
    {
        "id": "A07", "category": "AMBIGUOUS",
        "q": "양악수술 하는 게 좋을 것 같아?",
        "keywords": ["양악", "수술", "비용"]
    },
    {
        "id": "A08", "category": "AMBIGUOUS",
        "q": "요즘 운동 얼마나 하고 있어?",
        "keywords": ["운동", "재활", "철봉", "산책"]
    },
    {
        "id": "A09", "category": "AMBIGUOUS",
        "q": "AI 과금 문제가 해결됐어?",
        "keywords": ["과금", "API", "비용"]
    },
    {
        "id": "A10", "category": "AMBIGUOUS",
        "q": "온유 시스템이 잘 작동하고 있어?",
        "keywords": ["온유", "시스템", "작동"]
    },
]

def judge(response: str, keywords: list) -> str:
    if response is None:
        return "ACTION_DELEGATED"
    resp_lower = response.lower()
    matched = [k for k in keywords if k.lower() in resp_lower or k in response]
    if not matched:
        # 모호한 응답 체크 (찾지 못했다 계열)
        fail_patterns = ["찾지 못", "정보가 없", "확인되지 않", "알 수 없", "없습니다", "모르겠"]
        if any(p in response for p in fail_patterns):
            return "FAIL"
        return "PARTIAL"
    return "PASS"

results = []
print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"총 {len(QUESTIONS)}개 문항\n")

for i, item in enumerate(QUESTIONS, 1):
    q = item["q"]
    print(f"[{i:02d}/{len(QUESTIONS)}] {item['id']} {q[:40]}...")
    try:
        resp = handle_query(q, sp)
        verdict = judge(resp, item["keywords"])
        resp_preview = None if resp is None else resp[:250]
        print(f"    → {verdict}: {resp_preview[:80] if resp_preview else 'None'}\n")
    except Exception as e:
        resp = None
        resp_preview = f"ERROR: {e}"
        verdict = "FAIL"
        print(f"    → FAIL (예외): {e}\n")

    results.append({
        "id": item["id"],
        "category": item["category"],
        "question": q,
        "keywords": item["keywords"],
        "response_preview": resp_preview if resp else (resp_preview or "ACTION_DELEGATED"),
        "verdict": verdict
    })
    time.sleep(0.5)  # API 레이트 리밋 방지

# 저장
out_path = r"C:\Users\User\Documents\Obsidian Vault\SYSTEM\_test_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "test_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(results),
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n결과 저장 완료: {out_path}")

# 요약
cats = {}
for r in results:
    c = r["category"]
    v = r["verdict"]
    cats.setdefault(c, {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "ACTION_DELEGATED": 0})
    cats[c][v] = cats[c].get(v, 0) + 1

print("\n=== 카테고리별 집계 ===")
for cat, cnt in cats.items():
    print(f"{cat}: PASS={cnt.get('PASS',0)}, PARTIAL={cnt.get('PARTIAL',0)}, FAIL={cnt.get('FAIL',0)}, ACTION_DELEGATED={cnt.get('ACTION_DELEGATED',0)}")
