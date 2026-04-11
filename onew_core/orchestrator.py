"""
온유 오케스트레이터 (orchestrator.py)
이벤트 루프: 텔레그램 + APScheduler 통합 실행.

실행: python onew_core/orchestrator.py
     (기존 온유_실행.bat과 별도로 실행)

[구조]
- APScheduler: 시간 기반 일정 실행 → 텔레그램 알림
- Telegram: 메시지 수신 → OnewAgentV2로 처리 → 응답
- 스케줄 저장: SYSTEM/onew_schedules.json
"""
import os, sys, json, re, asyncio, logging
from datetime import datetime
from pathlib import Path

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_PATH = os.path.dirname(SYSTEM_DIR)
sys.path.insert(0, SYSTEM_DIR)

# ── 인박스 경로 ────────────────────────────────────────────────────────────────
INBOX_DIR    = os.path.join(VAULT_PATH, "inbox_filtered")
APPROVED_DIR = os.path.join(VAULT_PATH, "클리핑", "승인됨")
EMBED_QUEUE  = os.path.join(SYSTEM_DIR, "embed_queue.json")
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(APPROVED_DIR, exist_ok=True)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron    import CronTrigger
from apscheduler.triggers.date    import DateTrigger

logging.basicConfig(level=logging.WARNING)

# ── 설정 ──────────────────────────────────────────────────────────────────────
SCHEDULES_FILE = os.path.join(SYSTEM_DIR, "onew_schedules.json")

def _get_env(name: str) -> str:
    val = os.environ.get(name, "")
    if not val:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
        except:
            pass
    return val or ""

BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN")

# ── 스케줄 저장/로드 ───────────────────────────────────────────────────────────
def load_schedules() -> list:
    """저장된 스케줄 목록 반환.
    형식: [{"id": str, "label": str, "cron": str, "message": str}, ...]
    cron 예: "30 20 * * *" = 매일 20:30
    """
    if os.path.exists(SCHEDULES_FILE):
        try:
            with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_schedules(schedules: list):
    tmp = SCHEDULES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SCHEDULES_FILE)


# ── 텔레그램 알림 전송 ────────────────────────────────────────────────────────
async def send_telegram(bot, chat_id: int, text: str):
    """텔레그램으로 메시지 전송 (최대 4096자 자동 분할)."""
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id=chat_id, text=text[i:i+4096])


# ── 스케줄 실행 함수 ──────────────────────────────────────────────────────────
def make_schedule_job(bot, chat_id: int, agent, label: str, message: str):
    """스케줄 시간에 호출될 함수 반환 (클로저)."""
    async def job():
        now = datetime.now().strftime("%H:%M")
        print(f"[스케줄 실행] {now} — {label}")
        try:
            reply = agent.run(message)
            await send_telegram(bot, chat_id, f"⏰ [{label}]\n\n{reply}")
        except Exception as e:
            await send_telegram(bot, chat_id, f"⏰ [{label}] 실행 오류: {e}")
    return job


# ── 메인 오케스트레이터 ───────────────────────────────────────────────────────
class OnewOrchestrator:
    def __init__(self):
        from onew_core.agent import OnewAgentV2
        print("OnewAgentV2 초기화 중...")
        self.agent     = OnewAgentV2()
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        self.bot       = None
        self.chat_id   = None
        print("초기화 완료.")

    def _register_schedules(self):
        """onew_schedules.json에서 스케줄 불러와 APScheduler에 등록."""
        schedules = load_schedules()
        for s in schedules:
            try:
                minute, hour, *rest = s["cron"].split()
                trigger = CronTrigger(
                    minute=minute, hour=hour,
                    day=rest[0] if rest else "*",
                    month=rest[1] if len(rest) > 1 else "*",
                    day_of_week=rest[2] if len(rest) > 2 else "*",
                    timezone="Asia/Seoul",
                )
                self.scheduler.add_job(
                    make_schedule_job(self.bot, self.chat_id, self.agent,
                                      s["label"], s["message"]),
                    trigger=trigger,
                    id=s["id"],
                    replace_existing=True,
                )
                print(f"[스케줄 등록] {s['label']} ({s['cron']})")
            except Exception as e:
                print(f"[스케줄 등록 실패] {s.get('label', '?')}: {e}")

    async def _handle_telegram_message(self, update, context):
        """텔레그램 메시지 수신 → 에이전트 처리 → 응답."""
        from telegram.ext import ContextTypes
        text = update.message.text or ""
        user_id = update.message.from_user.id

        # ── 스케줄 명령 처리 (특수 명령) ──────────────────────────────────────
        if text.startswith("/schedule"):
            await self._handle_schedule_command(update, text)
            return

        # ── 코드 플래너 명령 ────────────────────────────────────────────────────
        if text.startswith("계획:") or text.startswith("계획 "):
            goal = text.split(":", 1)[-1].strip() if ":" in text else text[3:].strip()
            try:
                import onew_code_planner as _ocp
                from google import genai as _genai
                _client = _genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
                result = _ocp.receive_direction(goal, client=_client)
                await update.message.reply_text(f"📋 {result}")
            except Exception as e:
                await update.message.reply_text(f"⚠️ 계획 생성 실패: {e}")
            return

        if text in ("계획상태", "계획 상태", "plan status"):
            try:
                import onew_code_planner as _ocp
                await update.message.reply_text(_ocp.get_status())
            except Exception as e:
                await update.message.reply_text(f"⚠️ {e}")
            return

        if text in ("플래너로그", "계획로그", "plan log"):
            try:
                import onew_code_planner as _ocp
                await update.message.reply_text(_ocp.get_log())
            except Exception as e:
                await update.message.reply_text(f"⚠️ {e}")
            return

        if text in ("승인", "플래너승인", "plan approve"):
            try:
                import onew_code_planner as _ocp
                await update.message.reply_text(_ocp.approve_plan())
            except Exception as e:
                await update.message.reply_text(f"⚠️ {e}")
            return

        # ── 일반 질문 → 에이전트 (최근 플래너 컨텍스트 주입) ──────────────────
        await update.message.reply_text("처리 중...")
        try:
            query = text
            try:
                import onew_code_planner as _ocp
                recent = _ocp.get_recent_context()
                if recent:
                    query = f"{recent}\n\n{text}"
            except Exception:
                pass
            reply = self.agent.run(query)
            await send_telegram(context.bot, update.message.chat_id, reply)
        except Exception as e:
            await update.message.reply_text(f"오류: {e}")

    async def _handle_schedule_command(self, update, text: str):
        """
        스케줄 명령 처리.
        /schedule list                         — 현재 스케줄 목록
        /schedule add HH:MM 라벨 메시지        — 매일 HH:MM에 메시지로 에이전트 실행
        /schedule del 라벨                     — 스케줄 삭제
        """
        parts = text.strip().split(maxsplit=3)
        cmd   = parts[1] if len(parts) > 1 else "list"

        if cmd == "list":
            schedules = load_schedules()
            if not schedules:
                await update.message.reply_text("등록된 스케줄 없음.")
                return
            lines = ["[등록된 스케줄]"]
            for s in schedules:
                lines.append(f"• {s['label']} ({s['cron']}) → {s['message'][:30]}")
            await update.message.reply_text("\n".join(lines))

        elif cmd == "add" and len(parts) >= 4:
            # /schedule add 20:30 저녁알림 오늘 공조냉동 복습할 내용 알려줘
            time_str = parts[2]   # "20:30"
            rest     = parts[3]   # "저녁알림 메시지내용"
            label, _, message = rest.partition(" ")
            try:
                hour, minute = time_str.split(":")
                import uuid
                new_s = {
                    "id":      str(uuid.uuid4())[:8],
                    "label":   label,
                    "cron":    f"{minute} {hour} * * *",
                    "message": message,
                }
                schedules = load_schedules()
                schedules.append(new_s)
                save_schedules(schedules)
                # 런타임에도 즉시 등록
                trigger = CronTrigger(minute=minute, hour=hour, timezone="Asia/Seoul")
                self.scheduler.add_job(
                    make_schedule_job(context.bot if hasattr(self, 'context') else self.bot,
                                      update.message.chat_id, self.agent, label, message),
                    trigger=trigger, id=new_s["id"], replace_existing=True,
                )
                await update.message.reply_text(f"✅ 스케줄 등록: {label} 매일 {time_str}")
            except Exception as e:
                await update.message.reply_text(f"등록 실패: {e}\n사용법: /schedule add HH:MM 라벨 메시지")

        elif cmd == "del" and len(parts) >= 3:
            label = parts[2]
            schedules = load_schedules()
            target = [s for s in schedules if s["label"] == label]
            if not target:
                await update.message.reply_text(f"'{label}' 스케줄 없음.")
                return
            for s in target:
                try:
                    self.scheduler.remove_job(s["id"])
                except:
                    pass
            schedules = [s for s in schedules if s["label"] != label]
            save_schedules(schedules)
            await update.message.reply_text(f"✅ 스케줄 삭제: {label}")
        else:
            await update.message.reply_text(
                "사용법:\n"
                "/schedule list\n"
                "/schedule add HH:MM 라벨 메시지\n"
                "/schedule del 라벨"
            )

    # ── 인박스 유틸 ────────────────────────────────────────────────────────────
    def _get_inbox_files(self) -> list[str]:
        if not os.path.isdir(INBOX_DIR):
            return []
        return sorted(f for f in os.listdir(INBOX_DIR) if f.endswith(".md"))

    def _add_to_embed_queue(self, fpath: str):
        try:
            queue = []
            if os.path.exists(EMBED_QUEUE):
                with open(EMBED_QUEUE, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            if fpath not in queue:
                queue.append(fpath)
            with open(EMBED_QUEUE, "w", encoding="utf-8") as f:
                json.dump(queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning("embed_queue 추가 실패: %s", e)

    async def _handle_inbox_command(self, update, context):
        """/inbox — 승인 대기 파일 인라인 버튼으로 전송"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        files = self._get_inbox_files()
        if not files:
            await update.message.reply_text("📭 승인 대기 중인 항목이 없습니다.")
            return
        await update.message.reply_text(
            f"🧠 주니어 연구원 학습 리포트\n\n승인 대기 {len(files)}건. 결재해 주세요."
        )
        for filename in files[:10]:
            fpath = os.path.join(INBOX_DIR, filename)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            score_m = re.search(r"점수:\s*(\d)/5", content)
            topic_m = re.search(r"주제:\s*(.+)", content)
            score = score_m.group(1) if score_m else "?"
            topic = (topic_m.group(1).strip() if topic_m else "")[:30]
            preview = content[:400] + ("...[중략]" if len(content) > 400 else "")
            keyboard = [[
                InlineKeyboardButton("✅ Vault 저장", callback_data=f"approve|{filename}"),
                InlineKeyboardButton("🗑 삭제",       callback_data=f"reject|{filename}"),
            ]]
            header = f"📄 {filename[:50]}"
            if topic:
                header += f"\n주제: {topic} | 점수: {score}/5"
            await update.message.reply_text(
                f"{header}\n\n{preview}",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    async def _handle_approval_callback(self, update, context):
        """인라인 버튼 클릭 → 승인(이동) / 반려(삭제)"""
        query = update.callback_query
        await query.answer()
        try:
            action, filename = query.data.split("|", 1)
        except ValueError:
            await query.edit_message_text("잘못된 버튼 데이터입니다.")
            return
        source_path = os.path.join(INBOX_DIR, filename)
        if not os.path.exists(source_path):
            await query.edit_message_text("이미 처리되었거나 파일이 없습니다.")
            return
        if action == "approve":
            month_dir = os.path.join(APPROVED_DIR, datetime.now().strftime("%Y-%m"))
            os.makedirs(month_dir, exist_ok=True)
            dest = os.path.join(month_dir, filename)
            os.rename(source_path, dest)
            self._add_to_embed_queue(dest)
            await query.edit_message_text(f"✅ Vault 저장 완료\n클리핑/승인됨/{datetime.now().strftime('%Y-%m')}/{filename}")
        elif action == "reject":
            os.remove(source_path)
            await query.edit_message_text(f"🗑 삭제 완료\n{filename}")

    async def run(self):
        """텔레그램 봇 + 스케줄러 동시 실행 (PTB v20 async context manager 방식)."""
        from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters

        if not BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN 환경변수가 없습니다.")

        app = Application.builder().token(BOT_TOKEN).build()
        self.bot = app.bot

        # 허용 ID 로드
        allowed_ids_file = os.path.join(SYSTEM_DIR, "telegram_allowed_ids.json")
        allowed_ids = []
        if os.path.exists(allowed_ids_file):
            try:
                with open(allowed_ids_file) as f:
                    allowed_ids = json.load(f)
            except:
                pass

        async def _msg_handler(update, context):
            if allowed_ids and update.message.from_user.id not in allowed_ids:
                return
            if self.chat_id is None:
                self.chat_id = update.message.chat_id
                self._register_schedules()
            await self._handle_telegram_message(update, context)

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _msg_handler))
        app.add_handler(CommandHandler("schedule", _msg_handler))
        app.add_handler(CommandHandler("inbox", self._handle_inbox_command))
        app.add_handler(CallbackQueryHandler(self._handle_approval_callback))

        # 코드 플래너 태스크 실행 (30초마다 대기 중인 태스크 1개 처리)
        async def _planner_tick():
            try:
                import onew_code_planner as _ocp
                from google import genai as _genai
                _client = _genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

                before = {p["id"]: p["status"] for p in _ocp._load_queue().get("plans", [])}
                _ocp.execute_next(client=_client)

                for p in _ocp._load_queue().get("plans", []):
                    if before.get(p["id"]) not in ("pending", "running"):
                        continue
                    if p["status"] not in ("done", "aborted"):
                        continue

                    touched = [t["target"] for t in p["tasks"]
                               if t["status"] == "done" and t["type"] in ("create", "modify")]
                    icon = "✅" if p["status"] == "done" else "🔴"
                    msg  = (f"{icon} [코드플래너] 작업 {'완료' if p['status'] == 'done' else '중단'}\n"
                            f"목표: {p['goal'][:60]}\n"
                            f"생성/수정 파일: {', '.join(touched) if touched else '없음'}")
                    if self.bot and self.chat_id:
                        await send_telegram(self.bot, self.chat_id, msg)

                    # 실패한 경우 → 온유에게 원인 분석 + 자가 학습 요청
                    if p["status"] == "aborted":
                        failed_tasks = [t for t in p["tasks"] if t["status"] == "failed"]
                        if not failed_tasks:
                            continue
                        ft = failed_tasks[0]
                        analysis_prompt = (
                            f"[코드 플래너 실패 분석 요청]\n"
                            f"목표: {p['goal']}\n"
                            f"실패 태스크: [{ft['type']}] {ft['desc']}\n"
                            f"대상 파일: {ft['target']}\n"
                            f"오류 내용: {ft['result'][:300]}\n\n"
                            f"위 실패 원인을 분석하고, 수정 가능하면 create_code_plan 도구로 "
                            f"수정 계획을 바로 생성하세요. 수정 불가능한 경우 원인만 설명하세요."
                        )
                        try:
                            reply = self.agent.run(analysis_prompt)
                            if self.bot and self.chat_id:
                                await send_telegram(self.bot, self.chat_id,
                                                    f"🧠 [자가 학습]\n{str(reply)[:400]}")
                        except Exception:
                            pass
            except Exception:
                pass
        from apscheduler.triggers.interval import IntervalTrigger
        self.scheduler.add_job(_planner_tick, IntervalTrigger(seconds=30), id="code_planner_tick", replace_existing=True)

        self.scheduler.start()
        print(f"[오케스트레이터] 시작 — {datetime.now().strftime('%H:%M:%S')}")
        print("텔레그램으로 메시지를 보내면 온유가 응답합니다.")
        print("/schedule list|add|del 로 일정 관리")

        # PTB v20: run_polling()은 동기 메서드 → async 환경에서는 직접 updater 사용
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            # 무한 대기 (Ctrl+C로 종료)
            try:
                await asyncio.get_event_loop().create_future()
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                await app.updater.stop()
                await app.stop()
        self.scheduler.shutdown()


# ── 진입점 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    asyncio.run(OnewOrchestrator().run())
