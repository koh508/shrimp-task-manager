# [OPTIONAL SKILL] Python Database Patterns

## SQLAlchemy Async
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
```

## LanceDB (온유 시스템 전용)
```python
import lancedb

# 연결 (읽기 전용 사용 권장)
db = lancedb.connect(LANCE_DB_DIR)
tbl = db.open_table("chunks")

# 벡터 검색
results = tbl.search(embedding).metric("cosine").limit(50).to_list()
```

⚠️ LanceDB 주의사항:
- asyncio 루프 내 스레드에서 import → deadlock 위험
- 반드시 모듈 레벨에서 preload 또는 run_in_executor 사용
- MCP subprocess에서는 별도 프로세스라 안전하나 초기화 순서 주의

## 트랜잭션 관리
```python
async with session.begin():
    session.add(obj)
# begin() 블록 벗어나면 자동 commit/rollback
```
