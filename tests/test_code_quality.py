#!/usr/bin/env python3
"""
CodeQualityChecker 클래스에 대한 테스트
"""
import json
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from code_quality_checker import CodeQualityChecker


@pytest.fixture
def checker():
    """CodeQualityChecker의 테스트 인스턴스를 생성합니다."""
    # Create a dummy file to check against
    with open("dummy_test_file.py", "w") as f:
        f.write("import os\n\nprint('hello')")

    instance = CodeQualityChecker(target="dummy_test_file.py")
    yield instance

    # Clean up the dummy file
    os.remove("dummy_test_file.py")


@patch("subprocess.run")
def test_run_flake8_success(mock_run, checker):
    """flake8 실행이 성공하는 경우를 테스트합니다."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"./dummy_test_file.py": [{"code": "F401", "line_number": 1}]})
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    result = checker.run_flake8()

    mock_run.assert_called_with(
        ["flake8", str(checker.target), "--format=json"],
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
    )
    assert "error" not in result
    assert "./dummy_test_file.py" in result


@patch("subprocess.run")
def test_run_radon_success(mock_run, checker):
    """radon 실행이 성공하는 경우를 테스트합니다."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"dummy_test_file.py": {"cc": [{"rank": "A"}]}})
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    result = checker.run_radon()
    assert "error" not in result
    assert "dummy_test_file.py" in result


@patch("subprocess.run")
def test_run_bandit_success(mock_run, checker):
    """bandit 실행이 성공하는 경우를 테스트합니다."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"results": [{"line_number": 3}]})
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    result = checker.run_bandit()
    assert "error" not in result
    assert "results" in result


@patch("subprocess.run")
def test_tool_not_found(mock_run, checker):
    """도구를 찾을 수 없는 경우를 테스트합니다."""
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'flake8'")

    result = checker.run_flake8()
    assert "error" in result
    assert "'flake8'를 찾을 수 없습니다" in result["error"]


@patch("subprocess.run")
def test_summary_call(mock_run, checker):
    """summary 메소드가 모든 도구를 호출하는지 테스트합니다."""
    mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

    summary = checker.summary()

    assert mock_run.call_count == 3
    assert "flake8" in summary
    assert "radon" in summary
    assert "bandit" in summary
