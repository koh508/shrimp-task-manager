"""
telegram_collector.py
Telethon 기반 텔레그램 그룹 실시간 수집 → 옵시디언 자동 저장
- 메시지 + 사진/파일 시간순 인라인 저장
- 일별 MD 파일 자동 생성
사용법: python telegram_collector.py
"""
import os, sys, re, asyncio, json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
OUTPUT_BASE = os.path.join(OBSIDIAN_VAULT_PATH, "텔레그램")

SYSTEM_DIR  = os.path.dirname(os.path.abspath(__file__))
STATE_FILE  = os.path.join(SYSTEM_DIR, 'telegram_state.json')

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ==============================================================================
# 환경변수 읽기
# ==============================================================================
def _get_env(name):
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

API_ID   = _get_env('TELEGRAM_API_ID')
API_HASH = _get_env('TELEGRAM_API_HASH')

# ==============================================================================
# MD 파일 경로 (일별)
# ==============================================================================
def _safe_fname(name: str) -> str:
    """채팅방 이름을 파일명용 안전 문자열로 변환 (특수문자/공백 제거)"""
    s = re.sub(r'[\\/:*?"<>|!\s]+', '_', name)
    return s.strip('_') or 'unknown'

def _day_md_path(group_name, date_str):
    safe = re.sub(r'[\\/:*?"<>|]', '_', group_name)
    save_dir = os.path.join(OUTPUT_BASE, safe)
    os.makedirs(save_dir, exist_ok=True)
    safe_short = _safe_fname(group_name)
    return save_dir, os.path.join(save_dir, f"{date_str}_{safe_short}.md")

def _ensure_frontmatter(md_path, group_name, date_str):
    """파일이 없으면 frontmatter 생성"""
    if os.path.exists(md_path):
        return
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
        title = f"{date_str} ({weekday})"
    except:
        title = date_str

    content = (
        f"---\n"
        f"tags: [텔레그램, 회사채팅, {date_str}]\n"
        f"날짜: {date_str}\n"
        f"채팅방: {group_name}\n"
        f"상태: 수집중\n"
        f"---\n\n"
        f"# 📱 {title} — {group_name}\n\n"
    )
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

def _append_message(md_path, block):
    """메시지 블록을 MD 파일에 추가"""
    with open(md_path, 'a', encoding='utf-8') as f:
        f.write('\n\n---\n\n' + block)

# ==============================================================================
# 메시지 → 마크다운 블록
# ==============================================================================
def _build_block(sender, time_str, text, media_fname, is_image, forwarded=None):
    lines = []
    header = f"**{time_str} {sender}**"
    if forwarded:
        header += f"  _(전달: {forwarded})_"
    lines.append(header)

    if media_fname:
        if is_image:
            lines.append(f"![[{media_fname}]]")
        else:
            lines.append(f"📎 [[{media_fname}]]")

    if text:
        lines.append(text)

    return '\n'.join(lines)

# ==============================================================================
# 미디어 다운로드
# ==============================================================================
async def _download_media(client, message, save_dir, ts_str):
    IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    try:
        path = await client.download_media(
            message,
            file=os.path.join(save_dir, f"telegram_{ts_str}_{message.id}")
        )
        if path:
            ext = Path(path).suffix.lower()
            is_image = ext in IMG_EXTS
            return Path(path).name, is_image
    except Exception as e:
        print(f"  미디어 다운로드 실패: {e}")
    return None, False

# ==============================================================================
# 과거 메시지 일괄 수집
# ==============================================================================
async def fetch_history(client, group, group_name, limit=None):
    state   = _load_state()
    min_id  = state.get(group_name, {}).get('last_id', 0)
    if min_id:
        print(f"\n과거 메시지 수집 중... (ID {min_id} 이후, 최대 {limit or '전체'}건)")
    else:
        print(f"\n과거 메시지 수집 중... (최대 {limit or '전체'}건)")
    count = 0
    async for message in client.iter_messages(group, limit=limit, min_id=min_id, reverse=True):
        if not message.sender:
            continue
        await _process_message(client, message, group_name)
        count += 1
        if count % 100 == 0:
            print(f"  {count}건 처리...")
    print(f"  완료: {count}건")

# ==============================================================================
# 단일 메시지 처리
# ==============================================================================
async def _process_message(client, message, group_name, save_state=True):
    if not message.date:
        return

    dt       = message.date.astimezone()
    date_str = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H:%M')
    ts_str   = dt.strftime('%Y%m%d_%H%M%S')

    # 발신자
    sender = '알 수 없음'
    if message.sender:
        s = message.sender
        sender = getattr(s, 'first_name', '') or ''
        last = getattr(s, 'last_name', '') or ''
        if last:
            sender += f' {last}'
        if not sender.strip():
            sender = getattr(s, 'username', '알 수 없음') or '알 수 없음'

    # 전달 여부
    forwarded = None
    if message.fwd_from:
        fwd = message.fwd_from
        forwarded = getattr(fwd, 'from_name', None) or '알 수 없음'

    # 텍스트
    text = message.text or ''

    # 미디어
    save_dir, md_path = _day_md_path(group_name, date_str)
    media_fname, is_image = None, False
    if message.media:
        media_fname, is_image = await _download_media(client, message, save_dir, ts_str)

    if not text and not media_fname:
        return  # 스티커 등 무시

    _ensure_frontmatter(md_path, group_name, date_str)
    block = _build_block(sender, time_str, text, media_fname, is_image, forwarded)
    _append_message(md_path, block)

    # 마지막 처리 ID 저장 (중복 방지)
    if save_state and message.id:
        state = _load_state()
        group_state = state.get(group_name, {})
        if message.id > group_state.get('last_id', 0):
            group_state['last_id'] = message.id
            state[group_name] = group_state
            _save_state(state)

# ==============================================================================
# 메인
# ==============================================================================
async def main():
    print("=" * 54)
    print("  텔레그램 실시간 수집기 (Telethon)")
    print("=" * 54)

    if not API_ID or not API_HASH:
        print("\n❌ 환경변수 필요:")
        print("  TELEGRAM_API_ID   — https://my.telegram.org 에서 발급")
        print("  TELEGRAM_API_HASH — 동일")
        print("\nPowerShell에서 등록:")
        print('  [System.Environment]::SetEnvironmentVariable("TELEGRAM_API_ID", "숫자", "User")')
        print('  [System.Environment]::SetEnvironmentVariable("TELEGRAM_API_HASH", "문자열", "User")')
        return

    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat

    session_path = os.path.join(SYSTEM_DIR, 'telegram_session')
    client = TelegramClient(session_path, int(API_ID), API_HASH)

    # 저장된 설정 불러오기
    state       = _load_state()
    cfg         = state.get('_config', {})
    session_exists = os.path.exists(session_path + '.session')

    saved_phone = cfg.get('phone', '')
    saved_group = cfg.get('group_name', '')
    saved_mode  = cfg.get('mode', '')

    # ── 완전 자동 시작 (세션 + 설정 모두 있을 때) ──────────────────────────
    if session_exists and saved_phone and saved_group and saved_mode:
        print(f"\n저장된 설정으로 자동 시작:")
        print(f"  그룹 : {saved_group}")
        print(f"  모드 : {saved_mode}")
        print("취소: Ctrl+C (3초)\n")
        try:
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            return

        await client.start(phone=saved_phone)
        print("✅ 로그인 완료")

        dialogs = await client.get_dialogs()
        groups  = [d for d in dialogs if isinstance(d.entity, (Channel, Chat))]
        matched = next((g for g in groups if g.name == saved_group), None)

        if matched:
            target     = matched
            group_name = saved_group
            mode       = saved_mode
            if mode in ('1', '2'):
                await fetch_history(client, target.entity, group_name)
                if mode == '1':
                    print("\n완료. 종료합니다.")
                    await client.disconnect()
                    return
            print(f"\n📡 실시간 수집 시작 — {group_name}")
            print("종료: Ctrl+C\n")
            @client.on(events.NewMessage(chats=target.entity))
            async def auto_handler(event):
                await _process_message(client, event.message, group_name, save_state=True)
                now = datetime.now().strftime('%H:%M:%S')
                print(f"  [{now}] 새 메시지 저장")
            await client.run_until_disconnected()
            return
        else:
            print(f"  저장된 그룹 '{saved_group}'을 찾을 수 없어 수동 선택합니다.")

    # ── 수동 설정 ────────────────────────────────────────────────────────────
    if saved_phone:
        ans = input(f"전화번호 [{saved_phone}] (엔터=유지): ").strip()
        phone = ans if ans else saved_phone
    else:
        phone = input("전화번호 (+8210 형식, 예: +821090124479): ").strip()

    await client.start(phone=phone)
    print("\n✅ 로그인 완료")

    dialogs = await client.get_dialogs()
    groups  = [d for d in dialogs if isinstance(d.entity, (Channel, Chat))]

    print("\n[참여 중인 그룹/채널]")
    for i, g in enumerate(groups, 1):
        print(f"  {i:2}. {g.name}")

    idx = int(input("\n수집할 그룹 번호: ")) - 1
    target = groups[idx]
    group_name = target.name
    print(f"\n선택: {group_name}")

    print("\n[모드 선택]")
    print("  1. 과거 메시지 전체 수집 후 종료")
    print("  2. 과거 메시지 수집 + 이후 실시간 수집")
    print("  3. 실시간 수집만 (오늘부터)")
    mode = input("번호: ").strip()

    # 설정 저장
    cfg.update({'phone': phone, 'group_name': group_name, 'mode': mode})
    state['_config'] = cfg
    _save_state(state)

    if mode in ('1', '2'):
        limit_inp = input("최대 수집 건수 (엔터=전체): ").strip()
        limit = int(limit_inp) if limit_inp else None
        await fetch_history(client, target.entity, group_name, limit)
        if mode == '1':
            print("\n완료. 종료합니다.")
            await client.disconnect()
            return

    # 실시간 수집
    print(f"\n📡 실시간 수집 시작 — {group_name}")
    print("종료: Ctrl+C\n")

    @client.on(events.NewMessage(chats=target.entity))
    async def handler(event):
        await _process_message(client, event.message, group_name, save_state=True)
        now = datetime.now().strftime('%H:%M:%S')
        print(f"  [{now}] 새 메시지 저장")

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
