# [OPTIONAL SKILL] Python Async & Concurrency

## 기본 원칙
- I/O 바운드 → asyncio (async/await)
- CPU 바운드 → multiprocessing / concurrent.futures
- 혼합 → run_in_executor로 블로킹 코드 격리

## 핵심 패턴
```python
import asyncio
from contextlib import asynccontextmanager

# async context manager
@asynccontextmanager
async def managed_resource():
    resource = await acquire()
    try:
        yield resource
    finally:
        await release(resource)

# TaskGroup (Python 3.11+)
async def fetch_all(urls: list[str]) -> list[str]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(u)) for u in urls]
    return [t.result() for t in tasks]
```

## 블로킹 코드 격리 (run_in_executor)
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_func, arg)
```

## 주의사항
- asyncio.sleep(0) — 이벤트 루프 양보 (CPU 독점 방지)
- asyncio.timeout() — Python 3.11+ 타임아웃
- 스레드 안전: asyncio.Queue, asyncio.Lock 사용
