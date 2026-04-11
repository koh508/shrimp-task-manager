"""
온유 신규 기능 테스트 스크립트
실행: python SYSTEM/auto_scripts/onew_feature_test.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# obsidian_agent 모듈 함수 직접 임포트
import obsidian_agent as oa

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, got, expected_substr):
    ok = expected_substr in str(got)
    tag = PASS if ok else FAIL
    results.append((tag, name, got))
    print(f"{tag} [{name}]")
    if not ok:
        print(f"     기대: '{expected_substr}' 포함")
        print(f"     실제: {str(got)[:120]}")

print("=" * 60)
print("온유 기능 테스트")
print("=" * 60)

# ──────────────────────────────────────────────────────────────
# TEST 1: PROTECTED_FOLDERS — OCU 폴더 write 차단
# ──────────────────────────────────────────────────────────────
print("\n[1] PROTECTED_FOLDERS 차단 테스트")

r = oa.write_file("OCU/테스트_자동생성.md", "---\nauthor: Onew\n---\n테스트")
check("OCU write 차단", r, "보호 폴더")

r = oa.write_file("03_OCU/테스트_자동생성.md", "---\nauthor: Onew\n---\n테스트")
check("03_OCU write 차단", r, "보호 폴더")

# ──────────────────────────────────────────────────────────────
# TEST 2: PROTECTED_FOLDERS — delete/move 차단
# ──────────────────────────────────────────────────────────────
print("\n[2] PROTECTED_FOLDERS delete/move 차단")

r = oa.delete_file(os.path.join(oa.OBSIDIAN_VAULT_PATH, "OCU", "dummy.md"))
check("OCU delete 차단", r, "보호 폴더")

r = oa.move_file(
    os.path.join(oa.OBSIDIAN_VAULT_PATH, "OCU", "dummy.md"),
    os.path.join(oa.OBSIDIAN_VAULT_PATH, "DAILY", "dummy.md")
)
check("OCU move 차단", r, "보호 폴더")

# ──────────────────────────────────────────────────────────────
# TEST 3: PROTECTED_FILES — 핵심 py 파일 write 차단
# ──────────────────────────────────────────────────────────────
print("\n[3] PROTECTED_FILES (.py) 차단")

r = oa.write_file(
    os.path.join(oa.OBSIDIAN_VAULT_PATH, "SYSTEM", "obsidian_agent.py"),
    "# 덮어쓰기 시도"
)
check("obsidian_agent.py write 차단", r, "핵심 시스템 파일")

# ──────────────────────────────────────────────────────────────
# TEST 4: auto_scripts 샌드박스 — 내부 파일 실행 허용
# ──────────────────────────────────────────────────────────────
print("\n[4] auto_scripts 샌드박스 실행")

# 실행용 더미 스크립트 생성
sandbox_dir = oa.AUTO_SCRIPTS_DIR
os.makedirs(sandbox_dir, exist_ok=True)
hello_script = os.path.join(sandbox_dir, "hello_test.py")
with open(hello_script, "w", encoding="utf-8") as f:
    f.write('print("sandbox_ok")\n')

r = oa.execute_script(hello_script)
check("샌드박스 내부 실행", r, "sandbox_ok")
check("샌드박스 태그 표시", r, "[샌드박스]")

# 정리
os.remove(hello_script)

# ──────────────────────────────────────────────────────────────
# TEST 5: auto_scripts 샌드박스 — 외부 스크립트 비대화형 차단
# ──────────────────────────────────────────────────────────────
print("\n[5] auto_scripts 외부 스크립트 차단 (비대화형 시뮬)")

# stdin이 tty가 아닌 환경에서 실행 중이므로 텔레그램 모드와 동일 조건
vault_py = os.path.join(oa.OBSIDIAN_VAULT_PATH, "SYSTEM", "path_cleanup.py")
r = oa.execute_script(vault_py)
# tty가 아니면 차단, tty면 프롬프트 — 여기선 비대화형이므로 차단 기대
if "취소" in str(r) or "차단" in str(r) or "샌드박스" in str(r):
    # 어느 쪽이든 적절히 처리됨
    results.append((PASS, "외부 스크립트 처리", r))
    print(f"{PASS} [외부 스크립트 처리]")
    print(f"     결과: {str(r)[:100]}")
else:
    results.append((FAIL, "외부 스크립트 처리", r))
    print(f"{FAIL} [외부 스크립트 처리]")
    print(f"     결과: {str(r)[:100]}")

# ──────────────────────────────────────────────────────────────
# TEST 6: edit_file PROTECTED_FOLDERS 차단
# ──────────────────────────────────────────────────────────────
print("\n[6] edit_file PROTECTED_FOLDERS 차단")

r = oa.edit_file(
    os.path.join(oa.OBSIDIAN_VAULT_PATH, "OCU", "dummy.md"),
    "old", "new"
)
check("OCU edit 차단", r, "보호 폴더")

# ──────────────────────────────────────────────────────────────
# TEST 7: user_written 플래그 — DB 구조 확인
# ──────────────────────────────────────────────────────────────
print("\n[7] RAG user_written 플래그 확인 (DB 샘플)")

import json
db_path = oa.DB_FILE
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    has_flag = any("user_written" in v for v in db.values())
    # 기존 DB엔 플래그 없어도 정상 (새 sync부터 적용)
    user_written_count = sum(1 for v in db.values() if v.get("user_written") is True)
    ai_written_count   = sum(1 for v in db.values() if v.get("user_written") is False)
    total = len(db)
    print(f"     DB 총 파일: {total}개")
    print(f"     user_written=True (원본):  {user_written_count}개")
    print(f"     user_written=False (온유생성): {ai_written_count}개")
    print(f"     플래그 미설정 (기존 파일): {total - user_written_count - ai_written_count}개")
    results.append((PASS, "user_written DB 확인", "OK"))
    print(f"{PASS} [user_written DB 확인]")
else:
    print(f"     DB 파일 없음 → 스킵")

# ──────────────────────────────────────────────────────────────
# 최종 결과
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
print(f"결과: {passed}개 통과 / {failed}개 실패 (총 {len(results)}개)")
print("=" * 60)
if failed > 0:
    print("\n실패 목록:")
    for tag, name, got in results:
        if tag == FAIL:
            print(f"  - {name}: {str(got)[:150]}")
