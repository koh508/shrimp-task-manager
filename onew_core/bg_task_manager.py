"""
온유 백그라운드 작업 관리자 (bg_task_manager.py)
- submit(name, fn, chat_id, app) → task_id
- list_tasks() → {task_id: metadata}
- count_running() → int
"""
import asyncio
import uuid
from datetime import datetime

# task_id → {"name", "started", "status"}
_tasks: dict[str, dict] = {}

MAX_HISTORY = 20   # 완료/실패 포함 최대 보관 수


async def _runner(task_id: str, name: str, fn, chat_id: int, app) -> None:
    """백그라운드 실행 코루틴 — 완료/실패 시 텔레그램으로 알림 전송."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, fn)
        _tasks[task_id]["status"] = "완료"

        text = f"✅ *[{name}]* 완료"
        if result:
            text += f"\n{str(result)[:1000]}"
        await app.bot.send_message(chat_id, text, parse_mode="Markdown")

    except Exception as e:
        _tasks[task_id]["status"] = "실패"
        await app.bot.send_message(
            chat_id, f"❌ *[{name}]* 실패\n`{e}`", parse_mode="Markdown"
        )

    finally:
        # 오래된 완료 기록 정리 (실행중 항목은 유지)
        finished = [k for k, v in _tasks.items() if v["status"] != "실행중"]
        for k in finished[:-MAX_HISTORY]:
            _tasks.pop(k, None)


def submit(name: str, fn, chat_id: int, app) -> str:
    """
    백그라운드 작업 제출.

    Args:
        name:    작업 표시 이름 (알림 메시지에 표시)
        fn:      동기 callable (스레드풀에서 실행)
        chat_id: 알림 받을 텔레그램 chat_id
        app:     telegram.ext.Application 인스턴스

    Returns:
        task_id (6자 hex 문자열)
    """
    task_id = uuid.uuid4().hex[:6]
    _tasks[task_id] = {
        "name": name,
        "started": datetime.now().strftime("%H:%M:%S"),
        "status": "실행중",
    }
    asyncio.create_task(_runner(task_id, name, fn, chat_id, app))
    return task_id


def list_tasks() -> dict:
    """현재 등록된 모든 작업(실행중 + 최근 완료) 반환."""
    return dict(_tasks)


def count_running() -> int:
    """현재 실행 중인 작업 수 반환."""
    return sum(1 for t in _tasks.values() if t["status"] == "실행중")
