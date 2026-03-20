"""
onew_field_linker.py
텔레그램 현장 채팅 → Vault 이론 노트 자동 연결
- telegram_collector.py 가 저장한 텔레그램/그룹명/YYYY-MM-DD.md 를 감시
- 새 메시지에서 현장 용어 추출 → Vault 이론 노트 검색
- 연관 이론 링크 + 설명을 텔레그램으로 알림
"""
import os, json, re, time, threading, glob, urllib.request, urllib.parse
from datetime import datetime, date
from pathlib import Path

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
STATE_FILE   = os.path.join(SYSTEM_DIR, 'field_linker_state.json')
TELEGRAM_DIR = os.path.join(OBSIDIAN_VAULT_PATH, '텔레그램')

CHECK_INTERVAL_SEC = 120   # 2분마다 새 메시지 확인
MIN_TEXT_LEN       = 10    # 이 글자 수 미만 메시지는 스킵

# 현장/기술 용어 감지 키워드 (이게 포함된 메시지만 분석)
FIELD_KEYWORDS = [
    '압력', '온도', '냉매', '압축기', '응축기', '증발기', '팽창', '냉동',
    '배관', '밸브', '펌프', '모터', '전류', '전압', '인버터', '센서',
    '누설', '누수', '과열', '과냉', '결로', '착상', '제상',
    '소화', '스프링클러', '감지기', '방화', '배연', '제연',
    '오류', '에러', '알람', '트립', '과부하', '단락', '접지',
    '시공', '설치', '점검', '보수', '교체', '불량',
]


# ==============================================================================
# 유틸
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

def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_state(s: dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def _send_telegram(msg: str):
    try:
        token = _get_env('TELEGRAM_BOT_TOKEN')
        if not token:
            return
        ids_file = os.path.join(SYSTEM_DIR, 'telegram_allowed_ids.json')
        with open(ids_file, 'r') as f:
            ids = json.load(f)
        if not ids:
            return
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': ids[0], 'text': msg, 'parse_mode': 'Markdown'
        }).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except:
        pass


# ==============================================================================
# 텔레그램 MD 파싱 — 오늘 파일에서 새 메시지 추출
# ==============================================================================
def _get_today_telegram_files() -> list[str]:
    today = date.today().isoformat()
    return glob.glob(os.path.join(TELEGRAM_DIR, '**', f'{today}.md'), recursive=True)

def _extract_messages_from_md(fpath: str, processed_pos: int) -> tuple[list[str], int]:
    """마지막으로 읽은 위치(processed_pos) 이후의 새 메시지 텍스트만 추출"""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return [], processed_pos

    new_content = content[processed_pos:]
    if not new_content.strip():
        return [], processed_pos

    # --- 구분자로 메시지 블록 분리 ---
    blocks = re.split(r'\n\n---\n\n', new_content)
    messages = []
    for block in blocks:
        # 헤더 줄 제거 (**HH:MM 이름** 형식)
        lines = block.strip().split('\n')
        text_lines = []
        for line in lines:
            if re.match(r'^\*\*\d{2}:\d{2}', line):
                continue  # 발신자/시간 헤더
            if line.startswith('![[') or line.startswith('📎'):
                continue  # 미디어
            if line.strip():
                text_lines.append(line.strip())
        text = ' '.join(text_lines)
        if len(text) >= MIN_TEXT_LEN:
            messages.append(text)

    return messages, len(content)


# ==============================================================================
# 이론 노트 검색 (간단한 키워드 매칭)
# ==============================================================================
def _find_theory_notes(keywords: list[str]) -> list[tuple[str, str]]:
    """키워드와 매칭되는 Vault 노트 탐색 (파일명 + 내용 검색)"""
    THEORY_FOLDERS = ['OCU', '약점노트', '대화요약', '변환문서']
    results = []
    seen = set()

    for folder in THEORY_FOLDERS:
        folder_path = os.path.join(OBSIDIAN_VAULT_PATH, folder)
        if not os.path.exists(folder_path):
            continue
        for md_file in glob.glob(os.path.join(folder_path, '**', '*.md'), recursive=True):
            if md_file in seen:
                continue
            try:
                fname = Path(md_file).stem
                # 파일명 매칭 우선
                name_match = any(kw in fname for kw in keywords)
                if name_match:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        snippet = f.read(500)
                    results.append((fname, snippet))
                    seen.add(md_file)
                    if len(results) >= 3:
                        return results
            except:
                pass

    # 파일명 매칭 부족 시 내용 검색
    if len(results) < 2:
        for folder in THEORY_FOLDERS:
            folder_path = os.path.join(OBSIDIAN_VAULT_PATH, folder)
            if not os.path.exists(folder_path):
                continue
            for md_file in glob.glob(os.path.join(folder_path, '**', '*.md'), recursive=True):
                if md_file in seen:
                    continue
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read(1000)
                    if any(kw in content for kw in keywords):
                        fname = Path(md_file).stem
                        results.append((fname, content[:300]))
                        seen.add(md_file)
                        if len(results) >= 3:
                            return results
                except:
                    pass

    return results


# ==============================================================================
# 핵심: 메시지 분석 → 이론 연결
# ==============================================================================
def _has_field_keyword(text: str) -> bool:
    return any(kw in text for kw in FIELD_KEYWORDS)

def _analyze_and_link(messages: list[str], generate_fn) -> str | None:
    """현장 메시지 배치 분석 → 연관 이론 찾아서 알림 메시지 생성"""
    field_msgs = [m for m in messages if _has_field_keyword(m)]
    if not field_msgs:
        return None

    # Gemini로 핵심 기술 용어 추출
    combined = '\n'.join(field_msgs[:5])
    prompt = (
        "다음 현장 대화에서 이론적 배경이 필요한 핵심 기술 용어를 최대 5개 추출하라.\n"
        "쉼표로 구분, 단어만, 설명 없이.\n"
        "예: 응축기, 냉매 누설, 과열도, 팽창밸브\n\n"
        f"현장 대화:\n{combined}"
    )
    try:
        result = generate_fn(prompt)
        keywords = [k.strip() for k in result.split(',') if k.strip()][:5]
    except:
        return None

    if not keywords:
        return None

    # 관련 이론 노트 검색
    theory_notes = _find_theory_notes(keywords)

    # 연결 설명 생성
    explain_prompt = (
        f"현장에서 다음 내용이 언급되었다:\n{combined}\n\n"
        f"핵심 키워드: {', '.join(keywords)}\n\n"
        f"이 현장 상황과 관련된 이론 원리를 2~3줄로 간결하게 설명하라. "
        f"공조냉동/소방/전기 이론 중심."
    )
    try:
        explanation = generate_fn(explain_prompt)[:400]
    except:
        explanation = ''

    # 알림 메시지 구성
    lines = [
        f"🔗 *현장 → 이론 연결 알림*\n",
        f"*키워드:* {', '.join(keywords)}\n",
    ]
    if explanation:
        lines.append(f"*이론 요약:*\n{explanation}\n")
    if theory_notes:
        links = ' · '.join(f"[[{name}]]" for name, _ in theory_notes)
        lines.append(f"*관련 노트:* {links}")

    return '\n'.join(lines)


# ==============================================================================
# 백그라운드 루프
# ==============================================================================
def _run_loop(generate_fn):
    state = _load_state()

    while True:
        try:
            import onew_shared
            if onew_shared.is_quiet_period():
                time.sleep(CHECK_INTERVAL_SEC)
                continue
        except ImportError:
            pass
        try:
            today_files = _get_today_telegram_files()
            for fpath in today_files:
                pos = state.get(fpath, 0)
                messages, new_pos = _extract_messages_from_md(fpath, pos)

                if messages:
                    notify = _analyze_and_link(messages, generate_fn)
                    if notify:
                        _send_telegram(notify)
                        print(f"  🔗 [현장연결] 알림 전송: {Path(fpath).parent.name}")

                if new_pos != pos:
                    state[fpath] = new_pos
                    _save_state(state)

        except Exception as e:
            print(f"  ⚠️ [현장연결] 오류: {e}")
            try:
                import onew_shared
                onew_shared.report_error("현장연결", e)
            except:
                pass

        time.sleep(CHECK_INTERVAL_SEC)


def start_background(generate_fn):
    t = threading.Thread(target=_run_loop, args=(generate_fn,), daemon=True)
    t.start()
    print("🔗 [현장연결] 백그라운드 시작 (2분마다 현장 채팅 분석)")
    return t
