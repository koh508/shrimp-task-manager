"""
telegram_export_to_md.py
Telegram Desktop 내보내기 JSON → 옵시디언 마크다운 변환
사용법: python telegram_export_to_md.py
"""
import os, sys, json, shutil, re
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
OUTPUT_BASE = os.path.join(OBSIDIAN_VAULT_PATH, "텔레그램")

SKIP_TYPES = {'service'}  # 입장/퇴장 등 시스템 메시지 제외

# ==============================================================================
# 텍스트 추출 (문자열 또는 리스트 형태 모두 처리)
# ==============================================================================
def _extract_text(text_field):
    if isinstance(text_field, str):
        return text_field.strip()
    if isinstance(text_field, list):
        parts = []
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get('text', ''))
        return ''.join(parts).strip()
    return ''

# ==============================================================================
# 미디어 파일 복사 → Vault
# ==============================================================================
def _copy_media(src_path, export_dir, save_dir, msg_id, ts_str):
    """미디어 파일을 Vault로 복사, 저장 파일명 반환"""
    full_src = os.path.join(export_dir, src_path)
    if not os.path.exists(full_src):
        return None
    ext = Path(full_src).suffix.lower() or '.jpg'
    fname = f"telegram_{ts_str}_{msg_id}{ext}"
    dst = os.path.join(save_dir, fname)
    shutil.copy2(full_src, dst)
    return fname

# ==============================================================================
# 메시지 → 마크다운 블록
# ==============================================================================
def _msg_to_md(msg, export_dir, save_dir):
    lines = []
    ts = msg.get('date', '')
    try:
        dt = datetime.fromisoformat(ts)
        time_str = dt.strftime('%H:%M')
        ts_fs = dt.strftime('%Y%m%d_%H%M%S')
    except:
        time_str = ts
        ts_fs = ts.replace(':', '').replace('-', '').replace('T', '_')

    sender = msg.get('from', msg.get('actor', '알 수 없음'))
    msg_id = msg.get('id', 0)
    forwarded = msg.get('forwarded_from', '')

    # 헤더
    header = f"**{time_str} {sender}**"
    if forwarded:
        header += f"  _(전달: {forwarded})_"
    lines.append(header)

    # 미디어 처리 (사진/파일/영상)
    media_path = None
    media_type = msg.get('media_type', '')
    photo = msg.get('photo', '')
    file_ = msg.get('file', '')

    if photo:
        fname = _copy_media(photo, export_dir, save_dir, msg_id, ts_fs)
        if fname:
            lines.append(f"![[{fname}]]")
    elif file_:
        ext = Path(file_).suffix.lower()
        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        fname = _copy_media(file_, export_dir, save_dir, msg_id, ts_fs)
        if fname:
            if ext in img_exts:
                lines.append(f"![[{fname}]]")
            else:
                lines.append(f"📎 [[{fname}]]")

    # 텍스트
    text = _extract_text(msg.get('text', ''))
    if text:
        lines.append(text)

    # 스티커/기타
    if not text and not photo and not file_:
        sticker = msg.get('sticker_emoji', '')
        if sticker:
            lines.append(sticker)

    return '\n'.join(lines) if len(lines) > 1 else '\n'.join(lines)

# ==============================================================================
# 날짜별 그룹핑 → MD 파일 생성
# ==============================================================================
def _write_day_md(day_str, messages_md, group_name, save_dir):
    try:
        dt = datetime.strptime(day_str, '%Y-%m-%d')
        weekday = ['월', '화', '수', '목', '금', '토', '일'][dt.weekday()]
        title = f"{day_str} ({weekday})"
    except:
        title = day_str

    frontmatter = (
        f"---\n"
        f"tags: [텔레그램, 회사채팅, {day_str}]\n"
        f"날짜: {day_str}\n"
        f"채팅방: {group_name}\n"
        f"상태: 완료\n"
        f"---\n\n"
        f"# 📱 {title} — {group_name}\n\n"
    )

    content = frontmatter + "\n\n---\n\n".join(messages_md)
    # 파일명: YYYY-MM-DD_채팅방명.md (날짜만으로 생성 시 DAILY 노트와 충돌 방지)
    safe_group = re.sub(r'[\\/:*?"<>|!\s]+', '_', group_name).strip('_') or 'unknown'
    fname = f"{day_str}_{safe_group}.md"
    fpath = os.path.join(save_dir, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    return fname

# ==============================================================================
# 메인
# ==============================================================================
def main():
    print("=" * 54)
    print("  텔레그램 내보내기 → 옵시디언 마크다운 변환")
    print("=" * 54)
    print("\nTelegram Desktop 내보내기 폴더 경로:")
    print("(우클릭 → 경로 복사 후 붙여넣기)")
    export_dir = input("> ").strip().strip('"')

    # result.json 파일 경로를 직접 붙여넣은 경우 자동 처리
    if export_dir.lower().endswith('result.json'):
        result_json = export_dir
        export_dir  = os.path.dirname(export_dir)
    else:
        result_json = os.path.join(export_dir, 'result.json')

    if not os.path.exists(result_json):
        print(f"\n❌ result.json 없음: {result_json}")
        print("Telegram Desktop에서 JSON 형식으로 내보내기 하세요.")
        return

    with open(result_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    group_name = data.get('name', '알수없는채팅방')
    safe_name  = re.sub(r'[\\/:*?"<>|]', '_', group_name)
    messages   = data.get('messages', [])

    print(f"\n채팅방: {group_name}")
    print(f"전체 메시지: {len(messages)}개")

    # 메시지 타입 현황 출력 (디버그)
    type_counts = {}
    for msg in messages:
        t = msg.get('type', '없음')
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"타입별: {type_counts}")

    # 저장 폴더
    save_dir = os.path.join(OUTPUT_BASE, safe_name)
    os.makedirs(save_dir, exist_ok=True)

    # 날짜별 그룹핑 (service 타입 제외)
    by_day = {}
    for msg in messages:
        if msg.get('type') in SKIP_TYPES:
            continue
        ts = msg.get('date', '')
        day = ts[:10] if ts else '날짜없음'
        by_day.setdefault(day, []).append(msg)

    if not by_day:
        print("\n❌ 변환할 메시지가 없습니다.")
        print("모든 메시지가 service 타입이거나 날짜 정보가 없습니다.")
        return

    print(f"날짜 범위: {min(by_day)} ~ {max(by_day)}")
    print(f"변환 중...\n")

    saved = []
    for day_str in sorted(by_day.keys()):
        day_msgs = by_day[day_str]
        messages_md = []
        for msg in day_msgs:
            block = _msg_to_md(msg, export_dir, save_dir)
            if block.strip():
                messages_md.append(block)

        if messages_md:
            fname = _write_day_md(day_str, messages_md, group_name, save_dir)
            saved.append(fname)
            print(f"  {fname}  ({len(day_msgs)}건)")

    print(f"\n{'='*54}")
    print(f"✅ 완료: {len(saved)}일치 → 텔레그램/{safe_name}/")
    print(f"{'='*54}")

if __name__ == '__main__':
    main()
