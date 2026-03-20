"""
온유 텔레그램 봇 (onew_telegram_bot.py)
- 텔레그램으로 온유에게 질문/이미지 분석 가능
- 실행: python onew_telegram_bot.py
"""
import sys
import os
import asyncio
import logging
import tempfile
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
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
# 대화 Vault 저장 (5턴마다)
# ==============================================================================
_conv_buffer: list = []   # [{"time": "HH:MM", "q": str, "a": str}, ...]
_turn_count: int = 0
SAVE_EVERY_N_TURNS = 5

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
        loop.run_in_executor(None, _save_conv_to_vault)


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
                await file.download_to_drive(tmp.name)
                tmp_paths.append(tmp.name)
                with open(tmp.name, 'rb') as f:
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
    """단일 사진 3중 분석"""
    await message.reply_text("📡 3중 분석 시작 (사진·Vault·웹)... 잠시 기다려주세요.")
    file = await ctx.bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        from onew_field_analyzer import analyze_field_image
        loop = asyncio.get_event_loop()

        def _analyze():
            return analyze_field_image(tmp_path, caption, get_agent())

        result = await loop.run_in_executor(None, _analyze)
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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start',    cmd_start))
    app.add_handler(CommandHandler('id',       cmd_id))
    app.add_handler(CommandHandler('status',   cmd_status))
    app.add_handler(CommandHandler('stop',     cmd_stop))
    app.add_handler(CommandHandler('budget',   cmd_budget))
    app.add_handler(CommandHandler('plan',     cmd_plan))
    app.add_handler(CommandHandler('review',   cmd_review))
    app.add_handler(CommandHandler('clip',     cmd_clipping))
    app.add_handler(CommandHandler('rollback', cmd_rollback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    print("원격 제어: /status /stop /budget /plan /review /clip /rollback")
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
