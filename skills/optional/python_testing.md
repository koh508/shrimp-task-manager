# [OPTIONAL SKILL] Python Testing (pytest)

## 기본 구조
```python
import pytest
from unittest.mock import patch, MagicMock

# fixture
@pytest.fixture
def client():
    return TestClient(app)

# parametrize
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
])
def test_length(input, expected):
    assert len(input) == expected
```

## Mock 패턴
```python
# 함수 패치
with patch("module.func") as mock_func:
    mock_func.return_value = "test"
    result = call_target()
    mock_func.assert_called_once_with("expected_arg")

# 비동기 mock
mock_func = AsyncMock(return_value="result")
```

## 커버리지 목표
- 핵심 비즈니스 로직: 90%+
- 실행: `pytest --cov=. --cov-report=term-missing`

## 온유 시스템 테스트 시 주의
- LanceDB mocking 금지 (실제 DB 사용 — 3/19 사고 교훈)
- MCP 서버는 subprocess 격리로 테스트
