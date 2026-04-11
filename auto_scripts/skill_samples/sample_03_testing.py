"""스킬: python_testing — pytest parametrize + fixture + mock (pytest로 실행)"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock

# ── 테스트 대상 함수 ──────────────────────────────────────────────────────────
def calculate_score(tokens_overlap: int, content_len: int) -> float:
    import math
    score = tokens_overlap * 1.5
    score -= math.log(content_len + 1) * 0.03
    return round(score, 2)

def fetch_skill(name: str) -> dict:
    """외부 의존성 — 테스트에서 mock 처리"""
    raise NotImplementedError("실제 구현은 MCP 서버 호출")

async def async_search(query: str) -> list[str]:
    """비동기 함수 — AsyncMock으로 테스트"""
    raise NotImplementedError

# ── 1. parametrize ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("overlap,length,expected", [
    (2, 100,  2.86),
    (4, 500,  5.81),
    (0, 100, -0.14),
])
def test_calculate_score(overlap, length, expected):
    result = calculate_score(overlap, length)
    assert result == expected, f"overlap={overlap} length={length}: {result} != {expected}"

# ── 2. fixture ────────────────────────────────────────────────────────────────
@pytest.fixture
def skill_data():
    return {"name": "python_async", "content": "asyncio TaskGroup", "score": 4.29}

def test_skill_data_structure(skill_data):
    assert "name" in skill_data
    assert "content" in skill_data
    assert skill_data["score"] > 1.0

# ── 3. Mock — 외부 의존성 격리 ────────────────────────────────────────────────
def test_fetch_skill_mock():
    with patch(__name__ + ".fetch_skill") as mock_fetch:
        mock_fetch.return_value = {"name": "python_async", "content": "..."}
        result = fetch_skill("python_async")
        mock_fetch.assert_called_once_with("python_async")
        assert result["name"] == "python_async"

# ── 4. AsyncMock — asyncio.run으로 동기 실행 ─────────────────────────────────
def test_async_search_mock():
    async def _run():
        with patch(__name__ + ".async_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = ["python_async.md", "python_db.md"]
            result = await async_search("async deadlock")
            assert len(result) == 2
            assert "python_async.md" in result
    asyncio.run(_run())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
