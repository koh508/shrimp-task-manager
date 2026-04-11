"""스킬: python_async — asyncio TaskGroup + Queue + Lock + run_in_executor"""
import asyncio
import time

# ── 1. TaskGroup (Python 3.11+) ──────────────────────────────────────────────
async def fetch(url: str) -> str:
    await asyncio.sleep(0.01)   # I/O 시뮬레이션
    return f"fetched:{url}"

async def fetch_all(urls: list[str]) -> list[str]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(u)) for u in urls]
    return [t.result() for t in tasks]

# ── 2. asyncio.Queue — 스레드 안전 큐 ────────────────────────────────────────
async def producer_consumer() -> list[str]:
    q: asyncio.Queue[str] = asyncio.Queue()
    results: list[str] = []

    async def producer():
        for i in range(3):
            await q.put(f"item-{i}")
        await q.put(None)  # 종료 신호

    async def consumer():
        while True:
            item = await q.get()
            if item is None:
                break
            results.append(item)
            q.task_done()

    await asyncio.gather(producer(), consumer())
    return results

# ── 3. run_in_executor — 블로킹 코드 격리 ────────────────────────────────────
def blocking_op(n: int) -> int:
    time.sleep(0.01)   # 블로킹 시뮬레이션
    return n * 2

async def run_blocking() -> int:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, blocking_op, 21)
    return result

# ── 실행 + 검증 ───────────────────────────────────────────────────────────────
async def main():
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    fetched = await fetch_all(urls)
    assert len(fetched) == 3, "TaskGroup 결과 수 불일치"
    assert all(r.startswith("fetched:") for r in fetched), "TaskGroup 결과 형식 오류"
    print(f"  [1] TaskGroup : {fetched}")

    items = await producer_consumer()
    assert items == ["item-0", "item-1", "item-2"], f"Queue 결과 오류: {items}"
    print(f"  [2] Queue     : {items}")

    val = await run_blocking()
    assert val == 42, f"run_in_executor 결과 오류: {val}"
    print(f"  [3] Executor  : {val}")

if __name__ == "__main__":
    asyncio.run(main())
    print("PASS")
