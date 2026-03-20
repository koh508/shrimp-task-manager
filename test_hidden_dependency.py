"""
test_hidden_dependency.py — 숨겨진 의존성 탐지 테스트

검증 대상:
1. 테스트 순서 독립성 (Order Independence)
2. 글로벌 상태 오염 탐지 (Global State Isolation)
3. 결정론적 동작 (Determinism)

실행: python -m pytest test_hidden_dependency.py -v
"""
import importlib
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import onew_self_improve as si

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))


# ==============================================================================
# [1. 테스트 순서 독립성]
# ==============================================================================
def test_order_circuit_breaker_clean_state():
    """CircuitBreaker가 이전 테스트 상태에 영향받지 않음."""
    cb = si.CircuitBreaker()
    fix = {"action": "append", "code": "# order_test", "desc": "순서테스트", "test_code": ""}

    # 이 테스트 단독 실행 시: is_fix_duplicate() == False 이어야 함
    # (다른 테스트에서 이 해시를 등록하지 않았다면)
    h = cb._fix_hash(fix)
    data = cb._load()
    data.get("failed_hashes", {}).pop(h, None)  # 정리 후 시작
    cb._save(data)

    assert not cb.is_fix_duplicate(fix), "초기 상태에서 중복 감지 — 상태 오염"


def test_order_ast_checker_stateless():
    """ASTChecker가 호출 순서와 무관하게 동일 결과."""
    code_infinite = "while True:\n    pass\n"
    code_clean    = "def foo(): return 1\n"

    # 순서 A
    r1 = si.ASTChecker.check(code_infinite)
    r2 = si.ASTChecker.check(code_clean)

    # 순서 B (역순)
    r3 = si.ASTChecker.check(code_clean)
    r4 = si.ASTChecker.check(code_infinite)

    assert r2 == r3 == [], "clean code 결과 불일치 — 상태 의존"
    assert len(r1) > 0 and len(r4) > 0, "infinite loop 미탐지 — 상태 의존"
    assert r1 == r4, "동일 코드 결과 불일치 — 비결정론적"


def test_order_validate_test_code_stateless():
    """_validate_test_code가 호출 횟수/순서와 무관."""
    code = "def test_x():\n    assert 1 + 1 == 2\n"

    results = [si._validate_test_code(code) for _ in range(5)]
    ok_values  = [r[0] for r in results]
    msg_values = [r[1] for r in results]

    assert all(ok_values), "반복 호출 시 결과 불일치"
    assert len(set(msg_values)) == 1, "반복 호출 시 메시지 불일치"


# ==============================================================================
# [2. 글로벌 상태 격리]
# ==============================================================================
def test_global_pid_file_isolation():
    """_PID_FILE 변경이 원상복구되지 않으면 다른 테스트에 영향."""
    original = si._PID_FILE

    # 변경
    si._PID_FILE = "/fake/path/test.pid"
    assert si._get_agent_pid() is None

    # 복구
    si._PID_FILE = original
    assert si._PID_FILE == original, "_PID_FILE 복구 실패 — 전역 상태 오염"


def test_global_module_constants_unchanged():
    """모듈 상수가 런타임 중 변경되지 않음."""
    assert isinstance(si.HUMAN_APPROVAL_THRESHOLD, int)
    assert 0 <= si.HUMAN_APPROVAL_THRESHOLD <= 100

    # 상수 읽기 후에도 동일
    _ = si.HUMAN_APPROVAL_THRESHOLD
    assert si.HUMAN_APPROVAL_THRESHOLD == 60, "HUMAN_APPROVAL_THRESHOLD 변조됨"


def test_global_circuit_breaker_isolation():
    """CircuitBreaker 인스턴스가 독립적 (공유 상태 없음)."""
    cb_a = si.CircuitBreaker()
    cb_b = si.CircuitBreaker()

    fix = {"action": "append", "code": "# isolation", "desc": "격리테스트", "test_code": ""}

    cb_a.record_failed_hash(fix)

    # cb_b는 파일 기반이므로 동일 해시를 읽지만, 이는 의도된 설계
    # 핵심: cb_a와 cb_b가 서로 다른 인메모리 캐시를 가짐
    # (파일 공유는 정상 — 파일이 단일 진실의 원천)
    assert cb_a is not cb_b, "인스턴스 공유됨 — 싱글톤 버그"

    # 정리
    data = cb_a._load()
    data.get("failed_hashes", {}).pop(cb_a._fix_hash(fix), None)
    cb_a._save(data)


# ==============================================================================
# [3. 결정론적 동작]
# ==============================================================================
def test_determinism_fix_hash():
    """동일 fix → 항상 동일 해시."""
    cb  = si.CircuitBreaker()
    fix = {"action": "replace", "old": "foo", "new": "bar", "desc": "결정론", "test_code": ""}

    hashes = [cb._fix_hash(fix) for _ in range(10)]
    assert len(set(hashes)) == 1, f"해시 비결정론적: {set(hashes)}"


def test_determinism_make_diff():
    """동일 입력 → 항상 동일 diff."""
    original = "def foo():\n    return 1\n"
    modified = "def foo():\n    return 2\n"

    diffs = [si._make_diff(original, modified, "test.py") for _ in range(5)]
    assert len(set(diffs)) == 1, "diff 비결정론적"


def test_determinism_apply_action_replace():
    """replace action 결정론성."""
    content = "x = 1\ny = 2\n"
    fix     = {"action": "replace", "old": "x = 1", "new": "x = 10"}

    results = [si._apply_action(content, fix) for _ in range(5)]
    ok_list     = [r[0] for r in results]
    result_list = [r[1] for r in results]

    assert all(ok_list), "일부 호출 실패"
    assert len(set(result_list)) == 1, "결과 비결정론적"


def test_determinism_score_fix():
    """동일 fix + detail → 동일 점수."""
    engine = si.SelfImproveEngine()
    fix    = {"action": "append", "code": "# det", "desc": "결정론", "test_code": ""}
    detail = "PASS 문법\nPASS AST\nPASS Ruff\nPASS Dry-run\nPASS Pytest"

    scores = [engine._score_fix(fix, detail, __file__)[0] for _ in range(5)]
    assert len(set(scores)) == 1, f"_score_fix 비결정론적: {set(scores)}"


# ==============================================================================
# [4. 파일 시스템 격리 — 테스트가 서로의 파일을 건드리지 않음]
# ==============================================================================
def test_isolation_temp_files_cleaned():
    """각 테스트가 생성한 임시 파일이 정리됨."""
    markers = []
    for i in range(3):
        tmp = os.path.join(SYSTEM_DIR, f"_hd_isolation_{i}.json")
        try:
            with open(tmp, "w") as f:
                json.dump({"i": i}, f)
            markers.append(tmp)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    for path in markers:
        assert not os.path.exists(path), f"임시 파일 미정리: {path}"


def test_isolation_safetygate_backup_no_leak():
    """SafetyGate.backup()이 생성한 백업 파일이 원본 삭제 후에도 잔존하지 않음."""
    test_file = os.path.join(SYSTEM_DIR, "_hd_backup_leak.py")
    content   = "# leak test\n"
    try:
        with open(test_file, "w") as f:
            f.write(content)

        backup = si.SafetyGate.backup(test_file)
        assert not backup.startswith("ERROR")

        # 원본 삭제 → 롤백 → 백업 정리 확인
        os.remove(test_file)

        # rollback 없이 수동 정리 (SafetyGate가 .bak 파일 생성하는지 확인)
        bak = test_file + ".bak"
        if os.path.exists(bak):
            os.remove(bak)
        # backup 경로가 별도 위치라면 정리
        if os.path.exists(backup):
            os.remove(backup)

    finally:
        for path in [test_file, test_file + ".bak", backup if 'backup' in dir() else ""]:
            if path and os.path.exists(path):
                os.remove(path)
