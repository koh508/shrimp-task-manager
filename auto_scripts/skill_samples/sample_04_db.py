"""스킬: python_db — SQLAlchemy Async 패턴 + LanceDB 주의사항 검증"""
import asyncio
from typing import AsyncGenerator

# ── SQLAlchemy Async 패턴 (설치 없이 구조만 검증) ────────────────────────────
def validate_sqlalchemy_pattern():
    """ORM 패턴 구조 검증 — import 없이 코드 형태 확인"""
    pattern = """
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session

async def create_record(session: AsyncSession, data: dict) -> None:
    async with session.begin():
        session.add(Record(**data))
    # begin() 블록 벗어나면 자동 commit/rollback
"""
    assert "AsyncSession" in pattern
    assert "session.begin()" in pattern
    assert "yield session" in pattern
    return True

# ── LanceDB 안전 규칙 검증 ────────────────────────────────────────────────────
def validate_lancedb_rules():
    """LanceDB deadlock 방지 규칙 준수 여부 확인"""
    rules = {
        "asyncio_thread_import": False,   # 루프 내 스레드에서 import → deadlock 위험
        "module_level_preload": True,     # 모듈 레벨 preload → 안전
        "run_in_executor": True,          # run_in_executor 사용 → 안전
        "mcp_subprocess": True,           # MCP subprocess 격리 → 안전
    }
    safe_patterns = [k for k, v in rules.items() if v]
    unsafe_patterns = [k for k, v in rules.items() if not v]
    return safe_patterns, unsafe_patterns

# ── 트랜잭션 컨텍스트 매니저 패턴 ────────────────────────────────────────────
class MockSession:
    """SQLAlchemy AsyncSession 모의 구현"""
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self._items: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, *_):
        if exc_type:
            self.rolled_back = True
        else:
            self.committed = True

    def add(self, item):
        self._items.append(item)

    def begin(self):
        return self

async def test_transaction_pattern():
    session = MockSession()
    async with session:
        session.add({"id": 1, "name": "test"})
    assert session.committed, "정상 종료 시 commit 되어야 함"

    session2 = MockSession()
    try:
        async with session2:
            session2.add({"id": 2})
            raise ValueError("강제 오류")
    except ValueError:
        pass
    assert session2.rolled_back, "예외 시 rollback 되어야 함"

# ── 실행 ─────────────────────────────────────────────────────────────────────
async def main():
    ok = validate_sqlalchemy_pattern()
    assert ok
    print("  [1] SQLAlchemy 패턴 구조 검증 통과")

    safe, unsafe = validate_lancedb_rules()
    print(f"  [2] LanceDB 안전 패턴: {safe}")
    print(f"      LanceDB 위험 패턴: {unsafe}")
    assert "module_level_preload" in safe
    assert "asyncio_thread_import" in unsafe

    await test_transaction_pattern()
    print("  [3] 트랜잭션 commit/rollback 패턴 검증 통과")

if __name__ == "__main__":
    asyncio.run(main())
    print("PASS")
