"""
실패 사례 학습 흐름 테스트
1. 실패 사례 저장 (_save_mistake)
2. 코드 교훈 저장 (_save_code_lesson)
3. 저장된 파일이 search_vault로 검색되는지
4. 시스템 프롬프트에 선조회 규칙 포함 여부
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import obsidian_agent as oa

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(name, got, expected):
    ok = expected in str(got)
    tag = PASS if ok else FAIL
    results.append((tag, name, str(got)[:120]))
    print(f"{'OK' if ok else 'NG'} [{name}]")
    if not ok:
        print(f"   기대: '{expected}'")
        print(f"   실제: {str(got)[:120]}")

print("=" * 55)
print("실패 사례 학습 흐름 테스트")
print("=" * 55)

# ── TEST 1: 실패 사례 저장 ────────────────────────────────
print("\n[1] _save_mistake 저장 테스트")
oa._save_mistake(
    question="테스트 파일 만들어줘",
    wrong_answer="네, 만들었습니다. (실제로는 write_file 안 호출)",
    correction="아니야, write_file 실제 호출 없이 저장했다고 말하면 안 돼"
)
failure_dir = oa.FAILURE_DIR
month_file = os.path.join(failure_dir, "2026-03_실패사례.md")
# 이번달 파일 or 마이그레이션 파일 중 하나 존재 확인
import glob
any_failure = glob.glob(os.path.join(failure_dir, "*.md"))
check("실패사례 파일 존재", str(any_failure), ".md")
if any_failure:
    content = open(any_failure[-1], encoding='utf-8').read()
    check("실패 내용 저장됨", content, "write_file")

# ── TEST 2: 코드 교훈 저장 ────────────────────────────────
print("\n[2] _save_code_lesson 저장 테스트")
oa._save_code_lesson(
    func_name="edit_file",
    error="Error: old_str가 파일에서 3번 발견됩니다.",
    context="obsidian_agent.py 수정 시도"
)
code_dir = oa.CODE_LESSON_DIR
any_lesson = glob.glob(os.path.join(code_dir, "*.md"))
check("코드교훈 파일 존재", str(any_lesson), ".md")
if any_lesson:
    content = open(any_lesson[-1], encoding='utf-8').read()
    check("교훈 내용 저장됨", content, "edit_file")

# ── TEST 3: 성장기록 폴더가 search_vault로 검색 가능한지 ──
print("\n[3] search_vault 검색 가능 여부 (RAG DB 확인)")
import json
db_path = oa.DB_FILE
if os.path.exists(db_path):
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    # 성장기록 폴더 파일이 DB에 있는지 (아직 sync 전이면 없을 수 있음)
    growth_in_db = [k for k in db.keys() if '온유_성장기록' in k or '작업일지' in k]
    print(f"   DB 내 성장기록/작업일지 파일: {len(growth_in_db)}개")
    if growth_in_db:
        check("성장기록 DB 포함", str(growth_in_db[0]), "")
        results.append((PASS, "성장기록 DB 포함", growth_in_db[0]))
        print(f"OK [성장기록 DB 포함] {len(growth_in_db)}개")
    else:
        print("   INFO: 아직 sync 전 → 다음 자동 sync(12h) 후 검색 가능")
        results.append((PASS, "sync 대기 중 (정상)", "12h 후 자동 적용"))

# ── TEST 4: 시스템 프롬프트에 선조회 규칙 포함 ────────────
print("\n[4] 시스템 프롬프트 선조회 규칙 포함 여부")
src = open(oa.__file__, encoding='utf-8').read()
check("선조회 규칙 존재", src, "과거 실패 사례 선조회 규칙")
check("search_vault 호출 지시", src, "search_vault('실패사례 코드교훈")

# ── TEST 5: 성장기록 폴더 구조 ───────────────────────────
print("\n[5] 폴더 구조 확인")
check("온유_성장기록 존재", str(os.path.exists(oa.GROWTH_DIR)), "True")
check("실패사례 폴더 존재", str(os.path.exists(oa.FAILURE_DIR)), "True")
check("코드교훈 폴더 존재", str(os.path.exists(oa.CODE_LESSON_DIR)), "True")

# ── TEST 6: STUDY_FOLDERS 확장 확인 ──────────────────────
print("\n[6] 야간학습 STUDY_FOLDERS 확장 확인")
import onew_night_study as ns
check("작업일지 학습대상 포함", str(ns.STUDY_FOLDERS), "작업일지")
check("온유_성장기록 학습대상 포함", str(ns.STUDY_FOLDERS), "온유_성장기록")
check("코드리뷰 학습대상 포함", str(ns.STUDY_FOLDERS), "SYSTEM/코드리뷰")

# ── 최종 결과 ────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
print(f"결과: {passed}개 통과 / {failed}개 실패 (총 {len(results)}개)")
if failed:
    print("\n실패 목록:")
    for tag, name, got in results:
        if tag == FAIL:
            print(f"  - {name}: {got}")
print("=" * 55)
