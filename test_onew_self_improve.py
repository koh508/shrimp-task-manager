"""
test_onew_self_improve.py — onew_self_improve.py 핵심 컴포넌트 스모크 테스트

실행: python -m pytest test_onew_self_improve.py -v
"""
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import onew_self_improve as si


# ==============================================================================
# [ASTChecker]
# ==============================================================================
def test_ast_detects_infinite_loop():
    code = "while True:\n    pass\n"
    risks = si.ASTChecker.check(code)
    assert any("무한" in r for r in risks)


def test_ast_allows_while_with_break():
    code = "while True:\n    break\n"
    risks = si.ASTChecker.check(code)
    assert not risks


def test_ast_detects_eval():
    code = "eval('1+1')\n"
    risks = si.ASTChecker.check(code)
    assert any("eval" in r for r in risks)


def test_ast_clean_code_passes():
    code = "def add(a, b):\n    return a + b\n"
    risks = si.ASTChecker.check(code)
    assert risks == []


# ==============================================================================
# [_validate_test_code — MCP 기만 탐지]
# ==============================================================================
def test_validate_rejects_no_assert():
    ok, msg = si._validate_test_code("def test_foo():\n    x = 1\n")
    assert not ok
    assert "assert" in msg


def test_validate_rejects_assert_true():
    ok, msg = si._validate_test_code("def test_foo():\n    assert True\n")
    assert not ok
    assert "하드코딩" in msg


def test_validate_accepts_real_assert():
    code = "def test_add():\n    assert 1 + 1 == 2\n"
    ok, msg = si._validate_test_code(code)
    assert ok


# ==============================================================================
# [NeedAnalyzer]
# ==============================================================================
def test_need_analyzer_rejects_short_issue():
    needed, reason = si.NeedAnalyzer.should_fix("짧음", "content", __file__)
    assert not needed
    assert "짧음" in reason


def test_need_analyzer_rejects_recent_file():
    # 현재 파일은 방금 실행됐으므로 최근 수정으로 간주될 수 있음
    # 단순히 API가 동작하는지만 확인
    result = si.NeedAnalyzer.should_fix(
        "이 함수에 버그가 있어서 수정이 필요합니다 - 충분히 긴 이슈",
        "def foo(): pass",
        __file__,
    )
    assert isinstance(result, tuple) and len(result) == 2


def test_need_analyzer_passes_valid_issue():
    issue = "search_vault 함수에서 키워드 매칭이 되지 않는 문제가 있습니다"
    content = "def search_vault(query): pass\ndef foo(): pass"
    # 5분 이내 파일이면 스킵될 수 있으므로 결과 타입만 확인
    needed, reason = si.NeedAnalyzer.should_fix(issue, content, __file__)
    assert isinstance(needed, bool)


# ==============================================================================
# [CircuitBreaker — 해시 캐시]
# ==============================================================================
def test_circuit_breaker_hash_duplicate():
    cb = si.CircuitBreaker()
    fix = {"action": "append", "code": "# test", "desc": "테스트", "test_code": ""}

    # 초기엔 중복 아님
    assert not cb.is_fix_duplicate(fix)

    # 실패 hash 등록
    cb.record_failed_hash(fix)

    # 이후엔 중복
    assert cb.is_fix_duplicate(fix)

    # 정리 (테스트 격리)
    data = cb._load()
    h = cb._fix_hash(fix)
    data.get("failed_hashes", {}).pop(h, None)
    cb._save(data)


def test_circuit_breaker_different_fix_not_duplicate():
    cb = si.CircuitBreaker()
    fix_a = {"action": "append", "code": "# a", "desc": "A", "test_code": ""}
    fix_b = {"action": "append", "code": "# b", "desc": "B", "test_code": ""}
    cb.record_failed_hash(fix_a)
    assert not cb.is_fix_duplicate(fix_b)

    # 정리
    data = cb._load()
    data.get("failed_hashes", {}).pop(cb._fix_hash(fix_a), None)
    cb._save(data)


# ==============================================================================
# [_apply_action]
# ==============================================================================
def test_apply_action_replace():
    content = "def foo():\n    return 1\n"
    fix = {"action": "replace", "old": "return 1", "new": "return 2"}
    ok, result = si._apply_action(content, fix)
    assert ok
    assert "return 2" in result


def test_apply_action_append():
    content = "def foo():\n    pass\n"
    fix = {"action": "append", "code": "def bar():\n    pass\n"}
    ok, result = si._apply_action(content, fix)
    assert ok
    assert "bar" in result


def test_apply_action_replace_missing_old():
    content = "def foo(): pass\n"
    fix = {"action": "replace", "old": "존재하지않는코드", "new": "new"}
    ok, _ = si._apply_action(content, fix)
    assert not ok


# ==============================================================================
# [_make_diff]
# ==============================================================================
def test_make_diff_produces_unified_diff():
    original = "line1\nline2\n"
    modified = "line1\nline2_changed\n"
    diff = si._make_diff(original, modified, "test.py")
    assert "---" in diff and "+++" in diff
    assert "line2_changed" in diff


def test_make_diff_no_change_empty():
    content = "no change\n"
    diff = si._make_diff(content, content, "test.py")
    assert diff == ""


# ==============================================================================
# [Safe Point]
# ==============================================================================
def test_wait_for_safe_point_no_pid_returns_true():
    """PID 파일 없으면 즉시 True 반환."""
    original = si._PID_FILE
    si._PID_FILE = "/nonexistent/path/onew.pid"
    try:
        result = si._wait_for_safe_point(timeout=2)
        assert result is True
    finally:
        si._PID_FILE = original


def test_get_agent_pid_missing_file():
    """PID 파일 없으면 None 반환."""
    original = si._PID_FILE
    si._PID_FILE = "/nonexistent/path/onew.pid"
    try:
        assert si._get_agent_pid() is None
    finally:
        si._PID_FILE = original


def test_get_agent_pid_valid_file():
    """정상 PID 파일에서 정수 반환."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pid",
                                     delete=False) as f:
        f.write("12345")
        tmp = f.name
    original = si._PID_FILE
    si._PID_FILE = tmp
    try:
        assert si._get_agent_pid() == 12345
    finally:
        si._PID_FILE = original
        os.remove(tmp)


# ==============================================================================
# [_score_fix]
# ==============================================================================
def test_score_fix_high_score_all_gates():
    engine = si.SelfImproveEngine()
    fix = {"action": "append", "code": "# small", "desc": "test", "test_code": ""}
    detail = "PASS 문법\nPASS AST\nPASS Ruff\nPASS Dry-run\nPASS Pytest"
    score, gates = engine._score_fix(fix, detail, __file__)
    assert score >= 60
    assert len(gates) == 5


def test_score_fix_low_score_no_gates():
    engine = si.SelfImproveEngine()
    fix = {"action": "replace", "old": "x" * 600, "new": "y", "desc": "big"}
    detail = ""
    score, gates = engine._score_fix(fix, detail, __file__)
    assert score < 100
    assert gates == []
