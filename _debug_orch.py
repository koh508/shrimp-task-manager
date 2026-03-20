import sys, os
SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)

def log(msg):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

log("1: import OnewAgentV2")
from onew_core.agent import OnewAgentV2
log("2: import 완료")

agent = OnewAgentV2()
log("3: OnewAgentV2() 생성 완료")

from telegram.ext import Application
log("4: Application import 완료")

import os
token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
log(f"5: token={'있음' if token else '없음'}")

app = Application.builder().token(token).build()
log("6: app.build() 완료")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
log("7: scheduler 생성 완료")

import asyncio
log("8: asyncio.run 시작")

async def test():
    log("9: async 함수 진입")
    async with app:
        log("10: app.__aenter__ 완료")
        await app.start()
        log("11: app.start() 완료")
        await app.updater.start_polling(drop_pending_updates=True)
        log("12: start_polling 완료 — 봇 실행 중")
        await asyncio.sleep(3)
        await app.updater.stop()
        await app.stop()
        log("13: 정상 종료")

asyncio.run(test())
agent.close()
log("14: 완전 종료")
