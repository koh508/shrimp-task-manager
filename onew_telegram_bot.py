"""
온유 텔레그램 봇 (onew_telegram_bot.py)
- 텔레그램으로 온유에게 질문/이미지 분석 가능
- 실행: python onew_telegram_bot.py
"""
import sys
import os
import re
import json
import asyncio
import logging
import tempfile
import time
from datetime import datetime, time as dtime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)

from onew_core import bg_task_manager as _bg
from onew_core import claude_bridge as _cb

MAX_BG_TASKS = 3   # 동시 최대 백그라운드 작업 수

# "클로드:" prefix 감지 패턴
_CLAUDE_PREFIXES = ("클로드:", "클로드야", "claude:", "!claude")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# ==============================================================================
# 설정
# ==============================================================================
def _get_env(name: str) -> str:
    """환경변수를 읽되, 없으면 Windows 사용자 레지스트리에서 직접 읽음."""
    val = os.environ.get(name, '')
    if not val:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment')
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
        except:
            pass
    return val or ''

BOT_TOKEN = _get_env('TELEGRAM_BOT_TOKEN')

# 허용된 텔레그램 user_id 목록 (빈 리스트면 첫 메시지에서 자동 등록)
# 처음 실행 시 비워두면 봇이 user_id를 알려줌
ALLOWED_USER_IDS: list[int] = []

ALLOWED_IDS_FILE = os.path.join(SYSTEM_DIR, 'telegram_allowed_ids.json')

# ==============================================================================
# 인박스 승인 시스템 경로
# ==============================================================================
VAULT_PATH    = os.path.dirname(SYSTEM_DIR)
INBOX_DIR     = os.path.join(VAULT_PATH, "inbox_filtered")
APPROVED_DIR  = os.path.join(VAULT_PATH, "클리핑", "승인됨")
EMBED_QUEUE   = os.path.join(SYSTEM_DIR, "embed_queue.json")

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(APPROVED_DIR, exist_ok=True)

# ==============================================================================
# 허용 ID 관리
# ==============================================================================
def _load_allowed_ids() -> list[int]:
    import json
    if os.path.exists(ALLOWED_IDS_FILE):
        try:
            with open(ALLOWED_IDS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return ALLOWED_USER_IDS[:]

def _save_allowed_ids(ids: list[int]):
    import json
    with open(ALLOWED_IDS_FILE, 'w') as f:
        json.dump(ids, f)

# ==============================================================================
# 온유 에이전트 초기화
# ==============================================================================
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        print("온유 에이전트 초기화 중...")
        import obsidian_agent as _oa
        _agent = _oa.OnewAgent(location_mode="home")  # 텔레그램은 항상 home 모드
        _oa.onew = _agent
        print("온유 에이전트 준비 완료 (시크릿 OFF)")
    return _agent

# ==============================================================================
# 보안: 허용된 사용자만 접근
# ==============================================================================
def is_allowed(user_id: int) -> bool:
    ids = _load_allowed_ids()
    return not ids or user_id in ids  # 등록된 ID 없으면 누구나 (초기 설정용)

# ==============================================================================
# 이미지 Vault 저장
# ==============================================================================
def save_to_vault(img_bytes: bytes, ext: str, reply: str, question: str) -> str:
    import obsidian_agent as _oa
    now = datetime.now()
    month_str = now.strftime('%Y-%m')
    ts = now.strftime('%Y-%m-%d_%H-%M-%S')

    save_dir = os.path.join(_oa.OBSIDIAN_VAULT_PATH, '현장사진', month_str)
    os.makedirs(save_dir, exist_ok=True)

    img_filename = f'{ts}_현장.{ext}'
    img_path = os.path.join(save_dir, img_filename)
    with open(img_path, 'wb') as f:
        f.write(img_bytes)

    question_line = question or '(질문 없음)'
    md_content = (
        f'---\ntags: [현장, 이미지분석, 텔레그램, 작업기록]\n'
        f'날짜: {now.strftime("%Y-%m-%d")}\n'
        f'시간: {now.strftime("%H:%M")}\n'
        f'작성일시: {now.strftime("%Y-%m-%d %H:%M:%S")}\n'
        f'상태: 검토필요\n'
        f'작업장소: (미기입)\n'
        f'작업자: (미기입)\n'
        f'---\n\n'
        f'# 📋 현장 작업기록지\n\n'
        f'| 항목 | 내용 |\n|------|------|\n'
        f'| 작성일시 | {now.strftime("%Y-%m-%d %H:%M")} |\n'
        f'| 질문/작업내용 | {question_line} |\n'
        f'| 작업장소 | _(미기입 — 직접 기입)_ |\n'
        f'| 작업자 | _(미기입 — 직접 기입)_ |\n'
        f'| 감독자 확인 | _(서명란)_ |\n\n'
        f'---\n\n'
        f'{reply}\n\n'
        f'## 원본 이미지\n![[{img_filename}]]\n'
    )
    md_filename = f'{ts}_현장분석.md'
    md_path = os.path.join(save_dir, md_filename)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return f'현장사진/{month_str}/{md_filename}'

# ==============================================================================
# 핸들러
# ==============================================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    ids = _load_allowed_ids()

    if not ids:
        # 최초 실행: 이 user_id를 자동 등록
        _save_allowed_ids([uid])
        await update.message.reply_text(
            f"온유 텔레그램 봇 시작!\n\n"
            f"당신의 ID({uid})가 자동 등록되었습니다.\n"
            f"이제 자유롭게 질문하세요."
        )
    elif uid in ids:
        await update.message.reply_text("온유입니다. 질문하세요.")
    else:
        await update.message.reply_text(f"접근 권한이 없습니다. (ID: {uid})")


async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """내 텔레그램 user_id 확인"""
    uid = update.effective_user.id
    await update.message.reply_text(f"당신의 Telegram ID: `{uid}`", parse_mode='Markdown')


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """온유 상태 확인"""
    if not is_allowed(update.effective_user.id):
        return
    import json
    from datetime import datetime

    agent = get_agent()
    mode = "🔒 시크릿" if agent.location_mode == "work" else "🔓 일반"

    # 예산 현황
    try:
        import onew_budget
        budget_line = onew_budget.get_status().split('\n')[2]  # 배경 호출: N / M회
    except:
        budget_line = "예산 정보 없음"

    # 마지막 학습 세션
    try:
        state_file = os.path.join(SYSTEM_DIR, 'night_study_state.json')
        with open(state_file, 'r', encoding='utf-8') as f:
            ns = json.load(f)
        last = ns.get('last_session', '없음')
    except:
        last = '없음'

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = (
        f"🟢 *온유 가동 중* — {now}\n\n"
        f"모드: {mode}\n"
        f"API {budget_line}\n"
        f"마지막 야간학습: {last}\n\n"
        f"명령어: /stop /budget /plan /review /clip"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """온유 메인 에이전트 안전 종료"""
    if not is_allowed(update.effective_user.id):
        return
    flag = os.path.join(SYSTEM_DIR, 'stop.flag')
    with open(flag, 'w') as f:
        f.write('stop')
    await update.message.reply_text(
        "🔴 온유 종료 신호 전송 완료.\n"
        "메인 에이전트가 현재 작업 후 종료됩니다.\n"
        "재시작: 바탕화면 `온유_실행.bat` 실행"
    )


async def cmd_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """API 예산 현황"""
    if not is_allowed(update.effective_user.id):
        return
    try:
        import onew_budget
        await update.message.reply_text(onew_budget.get_status(), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"예산 정보 조회 실패: {e}")


async def cmd_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """오늘 학습 계획 조회"""
    if not is_allowed(update.effective_user.id):
        return
    from datetime import date
    today = date.today().isoformat()
    plan_dir = os.path.join(SYSTEM_DIR, '..', '학습계획')
    plan_file = os.path.join(plan_dir, f"{today}.md")
    if os.path.exists(plan_file):
        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()[:2000]
        await update.message.reply_text(content)
    else:
        await update.message.reply_text(
            f"📋 오늘({today}) 학습 계획이 아직 없습니다.\n"
            f"온유에게 '오늘 계획' 또는 '계획 세워줘'라고 말해보세요."
        )


async def cmd_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """복습 현황 조회"""
    if not is_allowed(update.effective_user.id):
        return
    import json
    from datetime import date
    db_file = os.path.join(SYSTEM_DIR, 'review_db.json')
    if not os.path.exists(db_file):
        await update.message.reply_text("복습 데이터가 없습니다.")
        return
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            db = json.load(f)
        today = date.today().isoformat()
        due = [c for c, e in db.items() if e.get('next_review', '9999') <= today]
        upcoming = sorted(
            [(c, e.get('next_review', '?')) for c, e in db.items() if e.get('next_review', '9999') > today],
            key=lambda x: x[1]
        )[:5]
        lines = [f"📚 *복습 현황*\n"]
        if due:
            lines.append(f"*오늘 복습 대상 ({len(due)}개):*")
            lines.extend(f"• {c}" for c in due[:10])
        else:
            lines.append("오늘 복습 대상 없음 ✅")
        if upcoming:
            lines.append(f"\n*예정 복습:*")
            lines.extend(f"• {c} — {d}" for c, d in upcoming)
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"복습 정보 조회 실패: {e}")


async def cmd_clipping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """오늘 클리핑 현황"""
    if not is_allowed(update.effective_user.id):
        return
    import json
    from datetime import date
    today = date.today().isoformat()
    index_file = os.path.join(SYSTEM_DIR, '..', '클리핑', f'클리핑_인덱스.json')
    # 클리핑 폴더 파일 수로 대체
    clip_dir = os.path.join(SYSTEM_DIR, '..', '클리핑')
    try:
        files = [f for f in os.listdir(clip_dir) if f.startswith(today) and f.endswith('.md')]
        await update.message.reply_text(
            f"📎 *오늘 클리핑 현황* ({today})\n\n"
            f"완료: {len(files)}개\n" +
            ('\n'.join(f"• {f[11:-3]}" for f in files[:10]) if files else "아직 없음"),
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"클리핑 정보 조회 실패: {e}")


async def cmd_rollback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/rollback 파일명 — 파일을 최근 백업본으로 복원"""
    if not is_allowed(update.effective_user.id):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "사용법: `/rollback 파일명`\n예: `/rollback onew_night_study.py`",
            parse_mode='Markdown'
        )
        return
    filename = args[0]
    import obsidian_agent as _oa
    result = _oa.rollback_file(filename)
    await update.message.reply_text(result)


# ==============================================================================
# 백그라운드 작업 명령어
# ==============================================================================

async def cmd_sync(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/sync — 백그라운드 임베딩 동기화. 완료 시 알림."""
    if not is_allowed(update.effective_user.id):
        return

    if _bg.count_running() >= MAX_BG_TASKS:
        await update.message.reply_text(
            f"⚠️ 백그라운드 작업이 이미 {MAX_BG_TASKS}개 실행 중입니다.\n/tasks 로 확인하세요."
        )
        return

    chat_id = update.effective_chat.id

    def _do_sync():
        import io, contextlib
        agent = get_agent()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agent.mem.sync(silent=False)
        output = buf.getvalue()
        # 핵심 줄만 추출 (최대 5줄)
        keywords = ('완료', '처리', '스킵', '한도', '청크', '파일', '학습')
        lines = [l.strip() for l in output.splitlines() if any(k in l for k in keywords)]
        return '\n'.join(lines[-5:]) if lines else "(로그 없음)"

    task_id = _bg.submit("임베딩 sync", _do_sync, chat_id, ctx.application)
    await update.message.reply_text(
        f"⚙️ *임베딩 sync* 시작 (`{task_id}`)\n완료되면 알림을 보내드립니다.",
        parse_mode="Markdown"
    )


async def cmd_bg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/bg <질문> — 백그라운드 질의. 완료 시 알림."""
    if not is_allowed(update.effective_user.id):
        return

    query = ' '.join(ctx.args) if ctx.args else ''
    if not query:
        await update.message.reply_text(
            "사용법: `/bg 질문내용`\n예: `/bg 냉동사이클 4단계 설명해줘`",
            parse_mode="Markdown"
        )
        return

    if _bg.count_running() >= MAX_BG_TASKS:
        await update.message.reply_text(
            f"⚠️ 백그라운드 작업이 이미 {MAX_BG_TASKS}개 실행 중입니다.\n/tasks 로 확인하세요."
        )
        return

    chat_id = update.effective_chat.id
    _query = query  # 클로저 캡처

    def _do_ask():
        agent = get_agent()
        prev_len = len(agent.history_records)
        agent.ask(_query, silent_search=True)
        if len(agent.history_records) > prev_len:
            return agent.history_records[-1].get('text', '응답 없음')
        return '응답 없음'

    label = query[:20] + ("..." if len(query) > 20 else "")
    task_id = _bg.submit(f"질의: {label}", _do_ask, chat_id, ctx.application)
    await update.message.reply_text(
        f"⚙️ *백그라운드 질의* 시작 (`{task_id}`)\n\"{label}\"\n완료되면 알림을 보내드립니다.",
        parse_mode="Markdown"
    )


async def cmd_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/tasks — 백그라운드 작업 목록 조회"""
    if not is_allowed(update.effective_user.id):
        return

    tasks = _bg.list_tasks()
    if not tasks:
        await update.message.reply_text("실행 중인 백그라운드 작업이 없습니다.")
        return

    icon = {"실행중": "⚙️", "완료": "✅", "실패": "❌"}
    lines = ["*백그라운드 작업 현황*\n"]
    for tid, t in tasks.items():
        i = icon.get(t["status"], "•")
        lines.append(f"{i} `{tid}` {t['name']} — {t['started']} ({t['status']})")

    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')


# ==============================================================================
# Claude Code 릴레이
# ==============================================================================

async def _handle_claude_relay(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    raw_request: str,
    tool_preset: str = "standard",
):
    """공통 처리: 프롬프트 래핑 → subprocess → 스트리밍 업데이트 → 완료 알림."""
    if _cb.is_running():
        await update.message.reply_text(
            "⚠️ Claude Code가 이미 작업 중입니다.\n`/claude_cancel` 로 취소하세요.",
            parse_mode="Markdown",
        )
        return

    # prefix 제거
    request = raw_request.strip()
    for p in _CLAUDE_PREFIXES:
        if request.lower().startswith(p.lower()):
            request = request[len(p):].strip()
            break

    prompt = _cb.build_prompt(request)

    # 시작 메시지 (즉시 응답)
    status_msg = await update.message.reply_text(
        f"⚙️ *Claude Code 실행 중...*\n\n"
        f"요청: {request[:60]}{'...' if len(request) > 60 else ''}\n\n"
        f"취소: `/claude_cancel`",
        parse_mode="Markdown",
    )

    # 스트리밍 버퍼 + 4초 throttle
    buf: list[str] = []
    loop = asyncio.get_running_loop()
    last_edit = [loop.time()]

    async def on_chunk(text: str):
        buf.append(text)
        if loop.time() - last_edit[0] >= 4.0:
            last_edit[0] = loop.time()
            preview = "".join(buf)[-500:]
            try:
                await status_msg.edit_text(
                    f"⚙️ *Claude Code 실행 중...*\n```\n{preview}\n```\n취소: `/claude_cancel`",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    chat_id = update.effective_chat.id

    async def _run():
        ok, result = await _cb.run_async(
            prompt,
            workdir=SYSTEM_DIR,
            tool_preset=tool_preset,
            on_chunk=on_chunk,
        )
        icon = "✅" if ok else "❌"
        label = "완료" if ok else "오류"
        header = f"{icon} *Claude Code {label}*\n\n"

        full_reply = header + (result or "(응답 없음)")
        try:
            await status_msg.edit_text(full_reply[:4096], parse_mode="Markdown")
        except Exception:
            await ctx.bot.send_message(chat_id, full_reply[:4096], parse_mode="Markdown")

        # 4096자 초과 분할 전송
        if len(result) > 4096 - len(header):
            for i in range(4096 - len(header), len(result), 4096):
                await ctx.bot.send_message(chat_id, result[i:i+4096])

    asyncio.create_task(_run())


async def cmd_claude(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/claude <요청> — Claude Code에 작업 지시 (또는 대화에서 '클로드: 요청')"""
    if not is_allowed(update.effective_user.id):
        return
    request = " ".join(ctx.args) if ctx.args else ""
    if not request:
        await update.message.reply_text(
            "*Claude Code 릴레이 사용법*\n\n"
            "1️⃣ 명령어: `/claude 요청내용`\n"
            "2️⃣ 대화: `클로드: 요청내용`\n"
            "3️⃣ 읽기전용: `/claude_ro 요청내용`\n\n"
            "취소: `/claude_cancel`\n"
            "상태: `/claude_status`",
            parse_mode="Markdown",
        )
        return
    await _handle_claude_relay(update, ctx, request, tool_preset="standard")


async def cmd_claude_ro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/claude_ro <요청> — 읽기 전용 모드 (파일 수정 없음)"""
    if not is_allowed(update.effective_user.id):
        return
    request = " ".join(ctx.args) if ctx.args else ""
    if not request:
        await update.message.reply_text("사용법: `/claude_ro 질문내용`", parse_mode="Markdown")
        return
    await _handle_claude_relay(update, ctx, request, tool_preset="readonly")


async def cmd_claude_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/claude_cancel — 실행 중인 Claude Code 작업 취소"""
    if not is_allowed(update.effective_user.id):
        return
    cancelled = await _cb.cancel()
    if cancelled:
        await update.message.reply_text("🛑 Claude Code 작업을 취소했습니다.")
    else:
        await update.message.reply_text("실행 중인 Claude Code 작업이 없습니다.")


async def cmd_claude_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/claude_status — Claude Code 실행 상태 확인"""
    if not is_allowed(update.effective_user.id):
        return
    if _cb.is_running():
        await update.message.reply_text(
            "⚙️ Claude Code 작업 *실행 중*\n취소: `/claude_cancel`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("✅ 대기 중 (실행 중인 작업 없음)")


# ==============================================================================
# 인박스 승인 시스템
# ==============================================================================

def _get_inbox_files() -> list[str]:
    """inbox_filtered/ 의 대기 중인 .md 파일 목록"""
    if not os.path.isdir(INBOX_DIR):
        return []
    return sorted(f for f in os.listdir(INBOX_DIR) if f.endswith(".md"))


def _add_to_embed_queue(fpath: str):
    """승인된 파일을 embed_queue.json에 추가 → LanceDB 자동 인덱싱"""
    try:
        import json
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


async def cmd_inbox(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/inbox — 승인 대기 파일 목록 전송 (인라인 버튼)"""
    if not is_allowed(update.effective_user.id):
        return

    files = _get_inbox_files()
    if not files:
        await update.message.reply_text("📭 승인 대기 중인 항목이 없습니다.")
        return

    await update.message.reply_text(
        f"🧠 *주니어 연구원 학습 리포트*\n\n"
        f"승인 대기 {len(files)}건. 결재를 진행해 주세요.",
        parse_mode="Markdown",
    )

    for filename in files[:10]:  # 한 번에 최대 10건
        fpath = os.path.join(INBOX_DIR, filename)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # YAML 프론트매터에서 점수·주제 추출
        score_m = re.search(r"점수:\s*(\d)/5", content)
        topic_m = re.search(r"주제:\s*(.+)", content)
        score = score_m.group(1) if score_m else "?"
        topic = topic_m.group(1).strip() if topic_m else ""

        preview = content[:500] + ("\n...[중략]" if len(content) > 500 else "")

        keyboard = [[
            InlineKeyboardButton("✅ Vault 저장", callback_data=f"approve|{filename}"),
            InlineKeyboardButton("🗑 삭제",       callback_data=f"reject|{filename}"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        header = f"📄 *{filename[:50]}*"
        if topic:
            header += f"\n주제: {topic} | 점수: {score}/5"

        await update.message.reply_text(
            f"{header}\n\n{preview}",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def handle_approval_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """인라인 버튼 클릭 → 승인(이동+RAG 인덱싱) / 반려(삭제)"""
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.edit_message_text("접근 권한이 없습니다.")
        return

    try:
        action, filename = query.data.split("|", 1)
    except ValueError:
        await query.edit_message_text("⚠️ 잘못된 버튼 데이터입니다.")
        return

    source_path = os.path.join(INBOX_DIR, filename)
    if not os.path.exists(source_path):
        await query.edit_message_text("⚠️ 이미 처리되었거나 파일이 없습니다.")
        return

    if action == "approve":
        # 승인: 클리핑/승인됨/ 으로 이동 + embed_queue 등록
        today_month = datetime.now().strftime("%Y-%m")
        dest_dir = os.path.join(APPROVED_DIR, today_month)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        os.rename(source_path, dest_path)
        _add_to_embed_queue(dest_path)
        logging.info("[APPROVED] %s → 클리핑/승인됨/%s/", filename, today_month)
        await query.edit_message_text(
            f"✅ *Vault 저장 완료*\n"
            f"`클리핑/승인됨/{today_month}/{filename}`\n"
            f"RAG 인덱싱 대기열에 등록됨.",
            parse_mode="Markdown",
        )

    elif action == "reject":
        os.remove(source_path)
        logging.info("[REJECTED] %s 삭제됨", filename)
        await query.edit_message_text(
            f"🗑 *삭제 완료*\n`{filename}`",
            parse_mode="Markdown",
        )


# ==============================================================================
# 대화 Vault 저장 (5턴마다)
# ==============================================================================
_conv_buffer: list = []   # [{"time": "HH:MM", "q": str, "a": str}, ...]
_turn_count: int = 0
SAVE_EVERY_N_TURNS = 1    # 매 턴마다 저장 (5→1: 봇 강제 종료 시 유실 방지)

def _save_conv_to_vault():
    """버퍼의 대화를 오늘 날짜 파일에 추가 저장 후 버퍼 초기화."""
    global _conv_buffer
    if not _conv_buffer:
        return
    import obsidian_agent as _oa
    today = datetime.now().strftime('%Y-%m-%d')
    save_dir = os.path.join(_oa.OBSIDIAN_VAULT_PATH, '텔레그램대화')
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f'{today}_텔레그램대화.md')

    # 파일이 없으면 헤더 생성
    if not os.path.exists(file_path):
        header = (
            f'---\ntags: [텔레그램대화, 대화기록]\n'
            f'날짜: {today}\n---\n\n'
            f'# 텔레그램 대화 — {today}\n\n'
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)

    # 버퍼 내용 추가
    lines = []
    for turn in _conv_buffer:
        lines.append(f"## {turn['time']}")
        lines.append(f"**용준:** {turn['q']}\n")
        lines.append(f"**온유:** {turn['a']}\n")
    block = '\n'.join(lines) + '\n'

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(block)

    print(f"💾 [대화저장] {len(_conv_buffer)}턴 → 텔레그램대화/{today}_텔레그램대화.md")
    _conv_buffer = []


# ADHD 코치 인스턴스 (봇 시작 시 초기화)
_coach = None

def get_coach():
    global _coach
    if _coach is None:
        try:
            from onew_adhd_coach import ADHDCoach
            import obsidian_agent as _oa
            gen_fn = lambda p: _oa.client.models.generate_content(
                model='gemini-2.5-flash', contents=p,
                config=_oa.types.GenerateContentConfig(
                    thinking_config=_oa.types.ThinkingConfig(thinking_budget=0))
            ).text
            _coach = ADHDCoach(gen_fn)
        except Exception as e:
            print(f"  ⚠️ ADHD코치 초기화 실패: {e}")
    return _coach


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """텍스트 메시지 → ADHD 코치 우선 → 온유 질의응답"""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("접근 권한이 없습니다.")
        return

    query = update.message.text.strip()
    if not query:
        return

    # Claude Code 릴레이 (최우선 처리)
    if any(query.lower().startswith(p.lower()) for p in _CLAUDE_PREFIXES):
        await _handle_claude_relay(update, ctx, query)
        return

    # 오답 추적: 직전 시험 문제 풀이 결과에 대한 정답/오답 응답 감지
    chat_id = update.effective_chat.id
    _exam_action = None
    async with _last_exam_lock:
        if chat_id in _last_exam:
            q_lower = query.lower()
            if any(kw in q_lower for kw in _WRONG_KW):
                _save_wrong_answer(chat_id, correct=False)
                _exam_action = "wrong"
            elif any(kw in q_lower for kw in _CORRECT_KW):
                _save_wrong_answer(chat_id, correct=True)
                _exam_action = "correct"
    if _exam_action == "wrong":
        await update.message.reply_text("오답 기록했습니다. 아침 브리핑에서 복습 알림을 드릴게요.")
        return
    if _exam_action == "correct":
        await update.message.reply_text("정답 확인했습니다.")
        return

    # 코드 플래너 명령 처리 (ADHD 코치보다 먼저)
    if query.startswith('계획:') or query.startswith('계획 '):
        goal = query.split(':', 1)[-1].strip() if ':' in query else query[3:].strip()
        try:
            import onew_code_planner as _ocp
            result = _ocp.receive_direction(goal, client=get_agent()._client if hasattr(get_agent(), '_client') else None)
            await update.message.reply_text(f"📋 {result}")
        except Exception as _e:
            await update.message.reply_text(f"⚠️ 계획 생성 실패: {_e}")
        return
    elif query in ('계획상태', '계획 상태', 'plan status'):
        try:
            import onew_code_planner as _ocp
            await update.message.reply_text(_ocp.get_status())
        except Exception as _e:
            await update.message.reply_text(f"⚠️ {_e}")
        return
    elif query.lower() in (
        '승인', '플래너승인', 'plan approve',
        '실행', '실행해', '실행해줘', '실행할게',
        '진행', '진행해', '진행해줘',
        '시작', '시작해', '시작해줘',
    ):
        try:
            import onew_code_planner as _ocp
            await update.message.reply_text(_ocp.approve_plan())
        except Exception as _e:
            await update.message.reply_text(f"⚠️ {_e}")
        return
    elif query.lower() in ('거부', '취소', '거부해', '취소해', 'plan reject', 'plan cancel'):
        try:
            import onew_code_planner as _ocp
            await update.message.reply_text(_ocp.reject_plan())
        except Exception as _e:
            await update.message.reply_text(f"⚠️ {_e}")
        return

    # ADHD 코치가 먼저 처리
    coach = get_coach()
    if coach:
        loop = asyncio.get_event_loop()
        handled = await loop.run_in_executor(None, lambda: coach.handle_message(query))
        if handled:
            return

    await update.message.chat.send_action('typing')

    agent = get_agent()
    loop = asyncio.get_event_loop()

    def _ask():
        prev_len = len(agent.history_records)
        agent.ask(query, silent_search=True)
        if len(agent.history_records) > prev_len:
            return agent.history_records[-1].get('text', '응답 없음')
        return '이 주제는 집에서 이야기해요. (시크릿 모드)'

    reply = await loop.run_in_executor(None, _ask)

    # 텔레그램 메시지 최대 4096자
    if len(reply) > 4096:
        for i in range(0, len(reply), 4096):
            await update.message.reply_text(reply[i:i+4096])
    else:
        await update.message.reply_text(reply)

    # 대화 버퍼에 추가 → 5턴마다 Vault 저장
    global _conv_buffer, _turn_count
    _conv_buffer.append({
        'time': datetime.now().strftime('%H:%M'),
        'q': query,
        'a': reply[:2000],   # 지나치게 긴 답변은 앞 2000자만
    })
    _turn_count += 1
    if _turn_count % SAVE_EVERY_N_TURNS == 0:
        await loop.run_in_executor(None, _save_conv_to_vault)


# 앨범(미디어그룹) 버퍼: {media_group_id: {'files': [], 'caption': '', 'time': float, 'chat_id': int}}
_album_buffer: dict = defaultdict(lambda: {'files': [], 'caption': '', 'time': 0, 'msg': None})
_album_tasks: dict = {}  # {media_group_id: asyncio.Task}

ALBUM_WAIT_SEC = 2.0  # 앨범 수집 대기 시간


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """사진 수신 - 단일 또는 앨범 자동 감지"""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("접근 권한이 없습니다.")
        return

    photo = update.message.photo[-1]
    caption = update.message.caption or ''
    media_group_id = update.message.media_group_id

    if media_group_id:
        # 앨범 모드: 버퍼에 수집 후 대기
        buf = _album_buffer[media_group_id]
        if len(buf['files']) >= 20:  # 최대 20장 제한
            return
        buf['files'].append(photo.file_id)
        buf['time'] = time.time()
        buf['msg'] = update.message
        if caption:
            buf['caption'] = caption

        # 기존 대기 태스크 취소 후 재시작 (마지막 사진 기준 대기)
        if media_group_id in _album_tasks:
            _album_tasks[media_group_id].cancel()

        task = asyncio.create_task(
            _process_album_after_delay(media_group_id, ctx)
        )
        _album_tasks[media_group_id] = task
    else:
        # 단일 사진 모드
        await _process_single_photo(update.message, photo.file_id, caption, ctx)


async def _process_album_after_delay(media_group_id: str, ctx):
    """앨범 수집 완료 후 다중 분석 실행"""
    await asyncio.sleep(ALBUM_WAIT_SEC)
    buf = _album_buffer.pop(media_group_id, {})
    _album_tasks.pop(media_group_id, None)
    if not buf:
        return

    msg = buf['msg']
    file_ids = buf['files']
    caption = buf['caption']
    n = len(file_ids)

    await msg.reply_text(
        f"📸 {n}장 앨범 감지 → 4단계 다중 분석 시작\n"
        f"(개별분석 → 종합 → 재분석 → 최종보고서)\n"
        f"시간이 걸립니다. 잠시 기다려주세요..."
    )

    # 모든 사진 다운로드
    tmp_paths = []
    img_bytes_list = []
    try:
        for fid in file_ids:
            file = await ctx.bot.get_file(fid)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_paths.append(tmp.name)  # 파일 생성 직후 등록 → 예외 시도 정리 보장
            await file.download_to_drive(tmp_paths[-1])
            with open(tmp_paths[-1], 'rb') as f:
                img_bytes_list.append(f.read())

        from onew_field_analyzer import analyze_multiple_field_images
        loop = asyncio.get_event_loop()

        def _multi_analyze():
            return analyze_multiple_field_images(tmp_paths, caption, get_agent())

        report = await loop.run_in_executor(None, _multi_analyze)

        # Vault 저장 (종합 보고서)
        saved_path = save_to_vault(img_bytes_list[0], 'jpg', report, caption)
        report += f"\n\n💾 저장됨: `{saved_path}` (대표 사진 1장 + 보고서)"

        for i in range(0, len(report), 4096):
            await msg.reply_text(report[i:i+4096])

    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except:
                pass


async def _process_single_photo(message, file_id: str, caption: str, ctx):
    """단일 사진 처리 — 시험 문제(exam) / 현장 안전 분석(field) 자동 분기"""
    from onew_field_analyzer import is_exam_photo, analyze_exam_image, analyze_field_image

    file = await ctx.bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_event_loop()

        if is_exam_photo(caption):
            # ── 시험 문제 풀이 모드 ──────────────────────────────────────
            await message.reply_text("📚 문제 분석 중...")

            def _exam():
                return analyze_exam_image(tmp_path, caption, get_agent())

            result = await loop.run_in_executor(None, _exam)
            report = result['answer']

            # 오답 추적: 마지막 시험 응답 저장
            chat_id = message.chat.id
            async with _last_exam_lock:
                _last_exam[chat_id] = {
                    "question": (caption or result.get("vision", ""))[:120],
                    "answer":   report[:200],
                    "date":     datetime.now(KST).strftime("%Y-%m-%d"),
                }
            report += "\n\n맞았나요? (맞아 / 틀렸어)"

        else:
            # ── 현장 안전 분석 모드 (기존) ───────────────────────────────
            await message.reply_text("📡 3중 분석 시작 (사진·Vault·웹)... 잠시 기다려주세요.")

            def _field():
                return analyze_field_image(tmp_path, caption, get_agent())

            result = await loop.run_in_executor(None, _field)
            report = result['report']

        with open(tmp_path, 'rb') as f:
            img_bytes = f.read()
        saved_path = save_to_vault(img_bytes, 'jpg', report, caption)
        report += f"\n\n💾 저장됨: `{saved_path}`"

        for i in range(0, len(report), 4096):
            await message.reply_text(report[i:i+4096])

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """파일로 전송된 이미지 처리"""
    if not is_allowed(update.effective_user.id):
        return
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith('image/'):
        await update.message.reply_text("이미지 파일만 분석 가능합니다.")
        return
    ext = doc.mime_type.split('/')[-1].replace('jpeg', 'jpg')

    await update.message.chat.send_action('typing')
    file = await ctx.bot.get_file(doc.file_id)
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    caption = update.message.caption or ''
    try:
        import obsidian_agent as _oa
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, lambda: _oa.analyze_image(tmp_path, caption))

        with open(tmp_path, 'rb') as f:
            img_bytes = f.read()
        saved_path = save_to_vault(img_bytes, ext, reply, caption)
        await update.message.reply_text(f"{reply}\n\n💾 저장됨: `{saved_path}`")
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


# ==============================================================================
# 아침 브리핑 + 오답 추적
# ==============================================================================

KST = timezone(timedelta(hours=9))

# 공조냉동기계기사 실기 시험일 (변경 필요 시 여기만 수정)
EXAM_DATE = datetime(2026, 4, 18).date()

WRONG_ANSWERS_FILE = Path(SYSTEM_DIR) / "exam_wrong_answers.json"

# 마지막 시험 문제 응답 버퍼 {chat_id: {"question": str, "answer": str, "date": str}}
_last_exam: dict = {}
_last_exam_lock = asyncio.Lock()

# 오답 확인 키워드
_WRONG_KW  = ("틀렸어", "틀렸다", "오답", "틀림", "아니야", "아니에요", "다시", "잘못됐", "wrong")
_CORRECT_KW = ("맞아", "맞다", "정답", "정확해", "맞았어", "ㅇㅇ", "correct")


def _load_wrong_answers() -> list:
    if WRONG_ANSWERS_FILE.exists():
        try:
            return json.load(WRONG_ANSWERS_FILE.open(encoding="utf-8")).get("wrong_answers", [])
        except Exception:
            pass
    return []


def _save_wrong_answer(chat_id: int, correct: bool):
    """마지막 시험 응답 결과를 오답 파일에 기록."""
    entry = _last_exam.get(chat_id)
    if not entry:
        return
    data = {"wrong_answers": _load_wrong_answers()}
    record = {
        "date":             entry["date"],
        "question_summary": entry["question"][:120],
        "answer_given":     entry["answer"][:200],
        "correct":          correct,
        "reviewed":         False,
    }
    data["wrong_answers"].append(record)
    WRONG_ANSWERS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _last_exam.pop(chat_id, None)


def _build_morning_briefing() -> str:
    """아침 브리핑 텍스트 생성 (API 0원, 파일 읽기만)."""
    today    = datetime.now(KST).date()
    d_day    = (EXAM_DATE - today).days
    lines    = [f"[아침 브리핑 — {today}]"]

    # D-day
    if d_day > 0:
        lines.append(f"공조냉동기계기사 실기 D-{d_day}")
    elif d_day == 0:
        lines.append("공조냉동기계기사 실기 — 오늘 시험입니다!")
    else:
        lines.append("공조냉동기계기사 실기 시험 종료.")

    # 취약 파트 (vault_analyzer 결과)
    patterns_path = Path(SYSTEM_DIR) / "patterns" / "diary_patterns.json"
    if patterns_path.exists():
        try:
            import json as _j
            pat = _j.loads(patterns_path.read_text(encoding="utf-8"))
            weak = pat.get("weak_parts", [])
            if weak:
                lines.append("취약 파트: " + ", ".join(weak[:3]))
        except Exception:
            pass

    # 오답 복습
    wrongs = [w for w in _load_wrong_answers() if not w.get("reviewed")]
    if wrongs:
        lines.append(f"오답 복습 {len(wrongs)}개 남음 — /review_wrong 으로 확인")

    # 어제 일기 여부
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    vault_root = Path(SYSTEM_DIR).parent
    daily_path = vault_root / "DAILY" / f"{yesterday}.md"
    if not daily_path.exists():
        lines.append(f"어제({yesterday}) 일기가 없습니다. 기록해두세요.")

    return "\n".join(lines)


async def _morning_briefing_job(context) -> None:
    """PTB JobQueue 콜백 — 매일 08:00 KST 발송."""
    if not ALLOWED_USER_IDS:
        return
    text = _build_morning_briefing()
    for uid in ALLOWED_USER_IDS:
        try:
            await context.bot.send_message(uid, text)
        except Exception as e:
            logger.warning("[브리핑] 발송 실패 uid=%s: %s", uid, e)


async def cmd_review_wrong(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/review_wrong — 오답 목록 출력."""
    wrongs = [w for w in _load_wrong_answers() if not w.get("reviewed")]
    if not wrongs:
        await update.message.reply_text("복습할 오답이 없습니다.")
        return
    lines = [f"오답 복습 ({len(wrongs)}개)\n"]
    for i, w in enumerate(wrongs[-5:], 1):  # 최근 5개만
        lines.append(f"{i}. [{w['date']}] {w['question_summary'][:60]}")
    await update.message.reply_text("\n".join(lines))


async def _post_init(app) -> None:
    """봇 초기화 후 스케줄 등록."""
    if app.job_queue and ALLOWED_USER_IDS:
        app.job_queue.run_daily(
            _morning_briefing_job,
            time=dtime(8, 0, 0, tzinfo=KST),
            name="morning_briefing",
        )
        logger.info("[브리핑] 매일 08:00 KST 스케줄 등록 완료")


# ==============================================================================
# 메인
# ==============================================================================
def main():
    if not BOT_TOKEN:
        print("오류: TELEGRAM_BOT_TOKEN 환경변수가 없습니다.")
        print("PowerShell에서 설정:")
        print('  [System.Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "your_token", "User")')
        sys.exit(1)

    # 온유 에이전트 미리 로딩
    get_agent()

    print("텔레그램 봇 시작 중...")
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler('start',    cmd_start))
    app.add_handler(CommandHandler('id',       cmd_id))
    app.add_handler(CommandHandler('status',   cmd_status))
    app.add_handler(CommandHandler('stop',     cmd_stop))
    app.add_handler(CommandHandler('budget',   cmd_budget))
    app.add_handler(CommandHandler('plan',     cmd_plan))
    app.add_handler(CommandHandler('review',   cmd_review))
    app.add_handler(CommandHandler('clip',     cmd_clipping))
    app.add_handler(CommandHandler('rollback', cmd_rollback))
    app.add_handler(CommandHandler('inbox',    cmd_inbox))
    app.add_handler(CommandHandler('sync',          cmd_sync))
    app.add_handler(CommandHandler('bg',            cmd_bg))
    app.add_handler(CommandHandler('tasks',         cmd_tasks))
    app.add_handler(CommandHandler('claude',        cmd_claude))
    app.add_handler(CommandHandler('claude_ro',     cmd_claude_ro))
    app.add_handler(CommandHandler('claude_cancel', cmd_claude_cancel))
    app.add_handler(CommandHandler('claude_status',  cmd_claude_status))
    app.add_handler(CommandHandler('review_wrong',   cmd_review_wrong))
    app.add_handler(CallbackQueryHandler(handle_approval_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    print("원격 제어: /status /stop /budget /plan /review /clip /rollback /inbox")
    print("백그라운드: /sync (임베딩) | /bg <질문> (비동기 질의) | /tasks (작업 현황)")
    print("Claude 릴레이: /claude <요청> | /claude_ro <읽기전용> | /claude_cancel | /claude_status")
    print("사용법: 사진 한 장 → 3중 분석 / 앨범(여러 장) → 4단계 다중 분석")

    print("온유 텔레그램 봇 가동 완료. Ctrl+C로 종료.")
    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        # 봇 종료 시 미저장 대화 버퍼 강제 flush
        if _conv_buffer:
            print(f"💾 [종료] 미저장 대화 {len(_conv_buffer)}턴 저장 중...")
            _save_conv_to_vault()


if __name__ == '__main__':
    main()
