"""
onew_night_study.py
PC 유휴/야간 시간 감지 → 자율 학습 실행
- 새 노트 분석 → 연관 개념 링크 자동 추가
- 예상 시험 문제 생성 → Vault 저장
- 오전 6시 텔레그램으로 학습 결과 브리핑
사용법: 온유_실행.bat 에서 백그라운드 실행
"""
import os, json, re, time, threading, ctypes, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
STATE_FILE   = os.path.join(SYSTEM_DIR, 'night_study_state.json')
NIGHT_DIR    = os.path.join(OBSIDIAN_VAULT_PATH, '야간학습')
EMBED_QUEUE_FILE = os.path.join(SYSTEM_DIR, 'embed_queue.json')  # C: 임베딩 대기열

IDLE_THRESHOLD_MIN = 30     # PC 유휴 인식 기준 (분)
CONV_IDLE_MIN      = 30     # 대화 없는 시간 기준 (분) — 낮 시간 학습 트리거
STUDY_START_HOUR   = 0      # 야간 학습 시작 시각
STUDY_END_HOUR     = 6      # 야간 학습 종료 시각
MORNING_HOUR       = 6      # 아침 브리핑 시각
CHECK_INTERVAL_SEC = 300    # 5분마다 상태 체크
MAX_NOTES_PER_RUN  = 5      # 1회 실행당 최대 처리 노트 수

# 학습 대상 폴더 (우선순위 순)
STUDY_FOLDERS = [
    # 기존
    'OCU', '약점노트', '대화요약', '클리핑', '현장학습',
    # 신규: 온유 AI/코딩 성장 학습
    '작업일지',               # Claude Code가 기록한 개발 이력 → 코드 변경 맥락 학습
    '온유_성장기록',          # 실패사례 + 코드교훈 → 자기 오류 패턴 학습
    'SYSTEM/코드리뷰',        # Claude 코드 리뷰 결과 → 코드 품질 기준 학습
    '클리핑/Anthropic',       # Anthropic 공홈에서 가져온 문서·연구·릴리즈노트
    '클리핑/Google',          # Google Developers Blog에서 가져온 AI/개발 뉴스
    '야간학습/사용자요청',    # 대화 중 발화 → 학습 목표 포착 → 자율처리
]

# Anthropic 공홈 정기 수집 URL 목록
ANTHROPIC_URLS = [
    ("https://www.anthropic.com/news",                         "Anthropic 뉴스"),
    ("https://www.anthropic.com/research",                     "Anthropic 연구"),
    ("https://docs.anthropic.com/en/release-notes/overview",   "Claude API 릴리즈노트"),
    ("https://docs.anthropic.com/en/docs/about-claude/models/overview", "Claude 모델 목록"),
]
ANTHROPIC_FETCH_INTERVAL_DAYS = 3   # 최소 3일에 한 번 재수집

# Google Developers Blog 정기 수집 URL 목록
GOOGLE_DEVBLOG_URLS = [
    ("https://developers.googleblog.com/", "Google Developers Blog"),
]
GOOGLE_DEVBLOG_FETCH_INTERVAL_DAYS = 3
SKIP_FOLDERS  = ['SYSTEM', 'Processed', 'Clippings', '텔레그램', '야간학습',
                 'code_backup', '변환문서', '업무자료', '대화기록']

os.makedirs(NIGHT_DIR, exist_ok=True)


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
# PC 유휴 감지 (Windows)
# ==============================================================================
class _LastInputInfo(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_seconds() -> float:
    try:
        info = _LastInputInfo()
        info.cbSize = ctypes.sizeof(info)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
        millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
        return millis / 1000.0
    except:
        return 0.0

def is_idle() -> bool:
    return get_idle_seconds() >= IDLE_THRESHOLD_MIN * 60

def is_night_hours() -> bool:
    h = datetime.now().hour
    return h >= STUDY_START_HOUR or h < STUDY_END_HOUR  # 0시~6시

def is_conversation_idle() -> bool:
    """마지막 온유 대화로부터 CONV_IDLE_MIN분 이상 경과 → 낮 시간 자율학습 트리거"""
    try:
        import onew_shared
        last = onew_shared._last_activity
        if last == 0.0:
            return False  # 아직 대화 없음 → 트리거 안 함
        return (time.time() - last) >= CONV_IDLE_MIN * 60
    except:
        return False

def is_morning_briefing_time() -> bool:
    now = datetime.now()
    return now.hour == MORNING_HOUR and now.minute < 10


# ==============================================================================
# 새 노트 탐색
# ==============================================================================
def _find_new_notes(state: dict) -> list[str]:
    """24시간 이내 수정된 미처리 노트 탐색"""
    processed = set(state.get('processed_files', []))
    cutoff     = datetime.now().timestamp() - 86400  # 24시간 전
    candidates = []

    for folder in STUDY_FOLDERS:
        folder_path = os.path.join(OBSIDIAN_VAULT_PATH, folder)
        if not os.path.exists(folder_path):
            continue
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS and not d.startswith('code_backup')]
            for fname in files:
                if not fname.endswith('.md'):
                    continue
                fpath = os.path.join(root, fname)
                if fpath in processed:
                    continue
                # 충돌1 방지: 자동생성 노트(개념정리/약점노트 AI 생성분)는 재처리 건너뜀
                try:
                    with open(fpath, 'r', encoding='utf-8') as _f:
                        _head = _f.read(300)
                    if 'auto_generated: true' in _head:
                        continue
                except:
                    pass
                try:
                    if os.path.getmtime(fpath) >= cutoff:
                        candidates.append(fpath)
                except:
                    pass

    return candidates[:MAX_NOTES_PER_RUN]


# ==============================================================================
# 핵심 학습 작업
# ==============================================================================
def _read_note(fpath: str) -> str:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return f.read()[:3000]
    except:
        return ''

def _find_related_links(content: str, note_title: str, generate_fn) -> list[str]:
    """노트 내용에서 Vault 연관 개념 추출 → [[링크]] 형태로 반환"""
    prompt = (
        f"다음 학습 노트에서 옵시디언 [[위키링크]]로 연결할 만한 핵심 개념어 5개를 추출하라.\n"
        f"규칙: 단어만, 쉼표 구분, 설명 없이.\n"
        f"예: 응축기, 냉매 순환, PID 제어, 에너지 보존 법칙, 열역학 2법칙\n\n"
        f"노트 제목: {note_title}\n"
        f"내용:\n{content[:1500]}"
    )
    try:
        result = generate_fn(prompt)
        concepts = [c.strip() for c in result.split(',') if c.strip()]
        return [f"[[{c}]]" for c in concepts[:5]]
    except:
        return []

# 공조냉동 과년도 참조 파일 목록 (우선순위 순)
_PAST_EXAM_FILES = [
    os.path.join(OBSIDIAN_VAULT_PATH, '공조냉동기계기사', '공조냉동기계기사 실기 과년도 출제문제 (2025년) 클로드.md'),
    os.path.join(OBSIDIAN_VAULT_PATH, 'OCU', '공조냉동기계기사', '실기기출_25년1-3회.md'),
    os.path.join(OBSIDIAN_VAULT_PATH, 'OCU', '공조냉동기계기사 2024 실기', '실기 합본_part1.md'),
    os.path.join(OBSIDIAN_VAULT_PATH, 'OCU', '공조냉동기계기사 2024 실기', '실기 합본_part2.md'),
    os.path.join(OBSIDIAN_VAULT_PATH, 'OCU', '공조냉동기계기사 2024 실기', '실기 합본_part3.md'),
]

def _load_past_exam_sample(char_limit: int = 2000) -> str:
    """과년도 파일 중 하나를 무작위 선택해 랜덤 구간 추출"""
    import random
    candidates = [f for f in _PAST_EXAM_FILES if os.path.exists(f)]
    if not candidates:
        return ''
    fpath = random.choice(candidates)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            text = f.read()
        # 문제 블록(### 문제) 단위로 쪼개서 무작위 2~3개 선택
        import re as _re
        blocks = _re.split(r'(?=###\s*문제)', text)
        blocks = [b.strip() for b in blocks if '문제' in b and len(b) > 100]
        if blocks:
            sample = random.sample(blocks, min(3, len(blocks)))
            result = '\n\n'.join(sample)
            return result[:char_limit]
        return text[len(text)//3 : len(text)//3 + char_limit]  # fallback: 중간 구간
    except:
        return ''

def _generate_questions(content: str, note_title: str, generate_fn) -> str:
    """노트 내용 기반 예상 시험 문제 생성"""
    is_field = any(kw in note_title for kw in ['소각', '배기', '폐열', '집진', '스크러버', '폐기물', '연소'])
    is_hvac  = _get_category(note_title) == '공조냉동'

    if is_field:
        prompt = (
            f"다음 학습 노트를 바탕으로 핵심 문제 5개를 만들어라.\n"
            f"형식:\n1. (문제)\n   정답: (답)\n   해설: (짧게)\n\n"
            f"맥락: 소각장 현장 실무자 관점. 실제 운전·점검·트러블슈팅 중심.\n\n"
            f"노트 제목: {note_title}\n내용:\n{content[:2000]}"
        )
    elif is_hvac:
        past_exam = _load_past_exam_sample()
        past_section = (
            f"\n\n[과년도 실기 문제 예시 — 반드시 이 형식과 유형을 따를 것]\n{past_exam}\n"
            if past_exam else ""
        )
        prompt = (
            f"공조냉동기계기사 실기 예상 문제 5개를 출제하라.\n\n"
            f"[필수 규칙]\n"
            f"1. 반드시 과년도 실기 시험에 실제로 출제된 유형(계산문제, 가/나/다 소문항 구조)만 사용한다.\n"
            f"2. 새로운 유형을 창작하지 않는다. 숫자·조건·단위만 변형한다.\n"
            f"3. 조건값(온도, 압력, 유량 등)은 실제 시험 범위의 수치를 사용한다.\n"
            f"4. 형식: 문제번호. [유형명] (문제 본문)\n   조건: ...\n   가. ...\n   나. ...\n   정답: 가. (값+단위) 나. (값+단위)\n   해설: (계산식 핵심만)\n\n"
            f"[이번 노트에서 다룬 개념]\n노트 제목: {note_title}\n{content[:1500]}"
            f"{past_section}"
        )
    else:
        prompt = (
            f"다음 학습 노트를 바탕으로 핵심 문제 5개를 만들어라.\n"
            f"형식:\n1. (문제)\n   정답: (답)\n   해설: (짧게)\n\n"
            f"맥락: 공조냉동기계기사/소방방재 자격시험 및 현장 실무 맥락.\n\n"
            f"노트 제목: {note_title}\n내용:\n{content[:2000]}"
        )
    try:
        return generate_fn(prompt)
    except:
        return '(문제 생성 실패)'

# ==============================================================================
# A. 자문자답 + 약점 자동 추출
# ==============================================================================
def _self_quiz_and_extract_weakness(content: str, note_title: str, category: str, generate_fn) -> str:
    """노트 내용에서 직접 약점 항목 추출 (문제 생성 없이).
    충돌3 방지: 공조냉동·소방만 실행 (API 절약)"""
    if category not in ('공조냉동', '소방'):
        return ''
    if not content or not content.strip():
        return ''

    prompt = (
        f"다음 학습 노트에서 헷갈리거나 틀리기 쉬운 핵심 개념/공식을 추출하라.\n"
        f"각 항목마다 반드시 아래 형식으로만 출력한다.\n\n"
        f"형식 (정확히 지킬 것):\n"
        f"문제N: (핵심 개념 또는 공식 — 2~3줄)\n"
        f"자신감: 확실 / 불확실 / 모름 중 하나\n\n"
        f"노트 제목: {note_title}\n---\n{content[:2500]}"
    )
    try:
        answer = generate_fn(prompt)
    except:
        return ''

    # 불확실/모름 항목 추출
    weak_items = []
    lines = answer.splitlines()
    current_q = ''
    for line in lines:
        line = line.strip()
        if re.match(r'^문제\d+:', line):
            current_q = line
        elif re.search(r'자신감\s*[:：]\s*(불확실|모름)', line) and current_q:
            weak_items.append(current_q)
            current_q = ''

    if not weak_items:
        return ''

    # 충돌4 방지: 날짜별 카테고리 파일에 append
    today = date.today().isoformat()
    weak_dir = os.path.join(OBSIDIAN_VAULT_PATH, '약점노트')
    os.makedirs(weak_dir, exist_ok=True)
    weak_file = os.path.join(weak_dir, f"{today}_약점_{category}.md")

    block = f"\n\n### 📌 출처: {note_title}\n" + '\n'.join(f"- {q}" for q in weak_items)

    if not os.path.exists(weak_file):
        header = (
            f"---\ntags: [약점노트, {category}, {today}]\n"
            f"auto_generated: true\n"   # 충돌1 방지: 재처리 건너뜀
            f"날짜: {today}\n카테고리: {category}\n---\n\n"
            f"# 🎯 약점 노트 — {category} ({today})\n"
        )
        with open(weak_file, 'w', encoding='utf-8') as f:
            f.write(header + block)
    else:
        with open(weak_file, 'a', encoding='utf-8') as f:
            f.write(block)

    print(f"  🎯 [약점] {len(weak_items)}개 항목 → {os.path.basename(weak_file)}")
    return weak_file


# ==============================================================================
# B. 개념 통합 정리 노트 생성
# ==============================================================================
def _synthesize_concept_note(note_contents: list, category: str, generate_fn) -> str:
    """같은 카테고리 노트 2개 이상 처리 시 종합 정리 노트 생성.
    충돌3 방지: 2개 이상일 때만, 충돌1 방지: auto_generated 태그 부착"""
    if len(note_contents) < 2:
        return ''

    # 대화 중 또는 동기화 중이면 개념정리 생략 (지연)
    try:
        import onew_shared
        if onew_shared.is_quiet_period():
            print(f"  ⏸️ [개념정리] 대화 중 — {category} 개념정리 생략 (다음 사이클로 지연)")
            return ''
        if onew_shared.is_syncing():
            print(f"  ⏸️ [개념정리] 동기화 중 — {category} 개념정리 생략 (다음 사이클로 지연)")
            return ''
    except ImportError:
        pass

    combined = '\n\n'.join(
        f"[{title}]\n{content[:700]}" for title, content in note_contents[:4]
    )
    is_hvac = (category == '공조냉동')
    fmt = (
        "## 핵심 공식\n- ...\n\n## 계산 유형별 풀이법\n- ...\n\n## 자주 나오는 함정\n- ..."
        if is_hvac else
        "## 핵심 개념\n- 개념: 설명\n\n## 공식/계산법\n- ...\n\n## 함정 포인트\n- ..."
    )
    prompt = (
        f"다음 {category} 학습 노트들을 종합해 핵심 개념 정리 노트를 만들어라.\n"
        f"형식:\n{fmt}\n\n"
        f"조건: 중복 제거, 핵심만, 마크다운 형식 유지, 한국어 작성\n\n"
        f"노트들:\n{combined}"
    )
    try:
        result = generate_fn(prompt)
    except:
        return ''

    today = date.today().isoformat()
    save_dir = os.path.join(OBSIDIAN_VAULT_PATH, '온유_성장기록', '개념정리')
    os.makedirs(save_dir, exist_ok=True)
    safe_cat = re.sub(r'[\\/:*?"<>|]', '_', category)
    fpath = os.path.join(save_dir, f"{today}_{safe_cat}_통합정리.md")

    content = (
        f"---\ntags: [개념정리, {category}, 자동생성]\n"
        f"auto_generated: true\n"   # 충돌1 방지: 재처리 건너뜀
        f"날짜: {today}\n카테고리: {category}\n"
        f"출처노트: {', '.join(t for t,_ in note_contents[:4])}\n---\n\n"
        f"# 🧠 {category} 개념 통합 정리 ({today})\n\n"
        f"> [!WARNING] AI 자동 생성 노트 — 내용 검증 필요\n\n"
        f"{result}"
    )
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  🧠 [개념정리] {category} 통합 노트 생성 → {os.path.basename(fpath)}")
    return fpath


# ==============================================================================
# C. 임베딩 대기열 등록
# ==============================================================================
def _queue_for_embedding(fpaths: list) -> None:
    """새로 생성된 파일을 embed_queue.json에 추가.
    충돌2 방지: DB 직접 수정 없이 큐에만 적재 → 온유 sync가 처리"""
    if not fpaths:
        return
    queue = []
    if os.path.exists(EMBED_QUEUE_FILE):
        try:
            with open(EMBED_QUEUE_FILE, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        except:
            queue = []

    existing = set(queue)
    added = [p for p in fpaths if p and os.path.exists(p) and p not in existing]
    if not added:
        return

    queue.extend(added)
    with open(EMBED_QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    print(f"  📥 [임베딩 큐] {len(added)}개 파일 등록 → 온유 재시작 시 자동 반영")


def _append_links_to_note(fpath: str, links: list[str]):
    """노트 하단에 연관 개념 섹션 추가 (기존 내용 보존)"""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if '## 🔗 연관 개념' in content:
            return  # 이미 있음
        section = '\n\n## 🔗 연관 개념\n' + ' · '.join(links)
        with open(fpath, 'a', encoding='utf-8') as f:
            f.write(section)
    except:
        pass

MAX_FILE_BYTES = 50_000  # 50KB 초과 시 새 파일

def _get_category(note_title: str) -> str:
    """노트 제목 → 카테고리 분류"""
    t = note_title.lower()
    if any(k in t for k in ['실기', '합본', '보냉', '공조', '냉동', '냉매', '냉각', '압축', '증발', '응축', '열역학', '몰리에']):
        return "공조냉동"
    if any(k in t for k in ['소방', '연소', '드론', '명사특강', '방화', '소화', '제연', '방재']):
        return "소방"
    if any(k in t for k in ['환경보건', '환경']):
        return "환경보건"
    if any(k in t for k in ['anthropic', 'deepmind', 'gemini', 'hugging', 'llm', 'mcp',
                             '해석가능', 'interpretability', 'constitutional', 'scaling',
                             'ai ', 'ai_', 'claude', '클리핑', 'google_developers', 'google 뉴스']):
        return "AI클리핑"
    if any(k in t for k in ['소각', '배기', '폐열', '집진', '스크러버', '폐기물', '연소', 'psm', '장비이력', 'ojt']):
        return "현장"
    # 온유 성장 기록 카테고리
    if any(k in t for k in ['실패사례', '코드교훈', '온유성장', '오답_패턴']):
        return "온유성장"
    if any(k in t for k in ['작업일지', '온유_대규모', '온유_시스템', '버그수정', '코드리뷰',
                             '개선작업', '안전성강화', '다음단계', '자율에이전트']):
        return "개발이력"
    if '글쓰기' in t:
        return "글쓰기"
    import re
    if re.match(r'^\d{4}-\d{2}-\d{2}', note_title):
        return "대화요약"
    return "기타"

def _get_report_path(cat: str, today_str: str) -> str:
    """카테고리 폴더 내 현재 저장 파일 경로 반환 (50KB 초과 시 새 파일)"""
    cat_dir = os.path.join(NIGHT_DIR, cat)
    os.makedirs(cat_dir, exist_ok=True)
    idx = 1
    while True:
        path = os.path.join(cat_dir, f"{today_str}_{cat}_{idx:02d}.md")
        if not os.path.exists(path):
            return path
        if os.path.getsize(path) < MAX_FILE_BYTES:
            return path
        idx += 1

def _save_questions(note_title: str, questions: str, today_str: str) -> str:
    """예상 문제를 카테고리별 야간학습 파일에 저장 (50KB 분할)"""
    cat = _get_category(note_title)
    report_path = _get_report_path(cat, today_str)
    block = f"\n\n---\n\n## 📝 {note_title}\n\n{questions}"
    if not os.path.exists(report_path):
        header = (
            f"---\n"
            f"tags: [야간학습, {cat}, {today_str}]\n"
            f"날짜: {today_str}\n"
            f"카테고리: {cat}\n"
            f"---\n\n"
            f"# 🌙 야간학습 — {cat} ({today_str})\n"
        )
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(header + block)
    else:
        with open(report_path, 'a', encoding='utf-8') as f:
            f.write(block)
    return report_path


# ==============================================================================
# Anthropic 공홈 수집
# ==============================================================================
def _fetch_anthropic_pages(state: dict) -> list[str]:
    """ANTHROPIC_URLS를 fetch하여 클리핑/Anthropic/ 에 저장. 저장된 제목 목록 반환."""
    from html.parser import HTMLParser
    import re as _re

    class _Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._skip = False
            self._skip_tags = {'script', 'style', 'nav', 'footer', 'head', 'aside'}
            self._depth = {}
            self.parts = []
        def handle_starttag(self, tag, attrs):
            self._depth[tag] = self._depth.get(tag, 0) + 1
            if tag in self._skip_tags:
                self._skip = True
        def handle_endtag(self, tag):
            self._depth[tag] = max(0, self._depth.get(tag, 1) - 1)
            if tag in self._skip_tags and self._depth.get(tag, 0) == 0:
                self._skip = False
        def handle_data(self, data):
            if not self._skip and data.strip():
                self.parts.append(data.strip())

    today = date.today().isoformat()
    last_fetch = state.get('anthropic_last_fetch', '2000-01-01')
    days_since  = (date.today() - date.fromisoformat(last_fetch)).days
    if days_since < ANTHROPIC_FETCH_INTERVAL_DAYS:
        return []

    save_dir = os.path.join(OBSIDIAN_VAULT_PATH, '클리핑', 'Anthropic')
    os.makedirs(save_dir, exist_ok=True)
    saved = []

    for url, label in ANTHROPIC_URLS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible)'})
            with urllib.request.urlopen(req, timeout=15) as r:
                charset = r.headers.get_content_charset('utf-8')
                html_raw = r.read().decode(charset, errors='ignore')

            # 제목
            m = _re.search(r'<title[^>]*>(.*?)</title>', html_raw, _re.IGNORECASE | _re.DOTALL)
            raw_title = _re.sub(r'\s+', ' ', m.group(1).strip()) if m else label
            title = _re.sub(r'\s*[-|]\s*Anthropic.*$', '', raw_title).strip() or label

            # 본문
            ext = _Extractor()
            ext.feed(html_raw)
            text = _re.sub(r'\n{3,}', '\n\n', '\n'.join(ext.parts))[:8000]

            safe = _re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
            fpath = os.path.join(save_dir, f"{today}_{safe}.md")
            md = (
                f"---\ntags: [클리핑, Anthropic, {today}]\n"
                f"날짜: {today}\n원본: {url}\n출처: Anthropic 공홈\n---\n\n"
                f"# {title}\n\n> [!NOTE] 원본\n> {url}\n\n{text}"
            )
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(md)
            saved.append(label)
            print(f"  🌐 [Anthropic] 수집: {label}")
        except Exception as e:
            print(f"  ⚠️ [Anthropic] {label} 실패: {e}")

    if saved:
        state['anthropic_last_fetch'] = today
    return saved


# ==============================================================================
# Google Developers Blog 수집
# ==============================================================================
def _fetch_google_devblog_pages(state: dict) -> list[str]:
    """GOOGLE_DEVBLOG_URLS를 fetch하여 클리핑/Google/ 에 저장. 저장된 제목 목록 반환."""
    from html.parser import HTMLParser
    import re as _re

    class _Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._skip = False
            self._skip_tags = {'script', 'style', 'nav', 'footer', 'head', 'aside'}
            self._depth = {}
            self.parts = []
        def handle_starttag(self, tag, attrs):
            self._depth[tag] = self._depth.get(tag, 0) + 1
            if tag in self._skip_tags:
                self._skip = True
        def handle_endtag(self, tag):
            self._depth[tag] = max(0, self._depth.get(tag, 1) - 1)
            if tag in self._skip_tags and self._depth.get(tag, 0) == 0:
                self._skip = False
        def handle_data(self, data):
            if not self._skip and data.strip():
                self.parts.append(data.strip())

    today = date.today().isoformat()
    last_fetch = state.get('google_devblog_last_fetch', '2000-01-01')
    days_since  = (date.today() - date.fromisoformat(last_fetch)).days
    if days_since < GOOGLE_DEVBLOG_FETCH_INTERVAL_DAYS:
        return []

    save_dir = os.path.join(OBSIDIAN_VAULT_PATH, '클리핑', 'Google')
    os.makedirs(save_dir, exist_ok=True)
    saved = []

    for url, label in GOOGLE_DEVBLOG_URLS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible)'})
            with urllib.request.urlopen(req, timeout=15) as r:
                charset = r.headers.get_content_charset('utf-8')
                html_raw = r.read().decode(charset, errors='ignore')

            m = _re.search(r'<title[^>]*>(.*?)</title>', html_raw, _re.IGNORECASE | _re.DOTALL)
            raw_title = _re.sub(r'\s+', ' ', m.group(1).strip()) if m else label
            title = _re.sub(r'\s*[-|]\s*(Google Developers Blog|Google).*$', '', raw_title, flags=_re.IGNORECASE).strip() or label

            ext = _Extractor()
            ext.feed(html_raw)
            text = _re.sub(r'\n{3,}', '\n\n', '\n'.join(ext.parts))[:8000]

            safe = _re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
            fpath = os.path.join(save_dir, f"{today}_{safe}.md")
            md = (
                f"---\ntags: [클리핑, Google, {today}]\n"
                f"날짜: {today}\n원본: {url}\n출처: Google Developers Blog\n---\n\n"
                f"# {title}\n\n> [!NOTE] 원본\n> {url}\n\n{text}"
            )
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(md)
            saved.append(label)
            print(f"  🌐 [Google] 수집: {label}")
        except Exception as e:
            print(f"  ⚠️ [Google] {label} 실패: {e}")

    if saved:
        state['google_devblog_last_fetch'] = today
    return saved


# ==============================================================================
# 1회 학습 세션
# ==============================================================================
def _track_night_study_usage():
    """야간학습 generate_fn 호출 횟수 추적 (obsidian_agent 과금 로그에 통합)"""
    try:
        import sys
        sys.path.insert(0, SYSTEM_DIR)
        from obsidian_agent import _increment_usage
        _increment_usage("night_study")
    except Exception:
        pass

def run_study_session(generate_fn) -> list[str]:
    """새 노트 처리 → A.자문자답/약점 B.개념정리 C.임베딩큐 포함"""
    _track_night_study_usage()   # 세션 1회 시작 시 추적
    state    = _load_state()
    today    = date.today().isoformat()

    # 외부 사이트 정기 수집 (3일마다)
    anthropic_saved      = _fetch_anthropic_pages(state)
    google_devblog_saved = _fetch_google_devblog_pages(state)
    _save_state(state)

    external_saved = anthropic_saved + google_devblog_saved
    new_notes = _find_new_notes(state)

    if not new_notes and not external_saved:
        return []

    if not new_notes:
        return [f"[외부수집] {', '.join(external_saved)}"]

    print(f"\n🌙 [야간학습] {len(new_notes)}개 노트 처리 시작...")
    processed  = state.get('processed_files', [])
    results    = []
    new_fpaths = []                          # C: 임베딩 큐에 올릴 경로 수집
    # B: 카테고리별 (title, content) 누적 → 세션 끝에 개념정리 생성
    cat_notes: dict = {}

    for fpath in new_notes:
        note_title = Path(fpath).stem
        content    = _read_note(fpath)
        if not content.strip():
            processed.append(fpath)
            continue

        print(f"  → {note_title}")
        category = _get_category(note_title)

        # 1. 연관 링크 추출 및 추가
        links = _find_related_links(content, note_title, generate_fn)
        if links:
            _append_links_to_note(fpath, links)

        # A. 약점 추출 (노트 내용에서 직접 — 공조냉동·소방만)
        weak_path = _self_quiz_and_extract_weakness(content, note_title, category, generate_fn)
        if weak_path and weak_path not in new_fpaths:
            new_fpaths.append(weak_path)

        # B: 카테고리별 노트 누적
        cat_notes.setdefault(category, []).append((note_title, content))

        processed.append(fpath)
        results.append(note_title)

    # B. 개념 통합 정리 노트 생성 (카테고리당 2개 이상일 때만 — 충돌3 방지)
    for cat, notes in cat_notes.items():
        synth_path = _synthesize_concept_note(notes, cat, generate_fn)
        if synth_path:
            new_fpaths.append(synth_path)

    # C. 새로 생성된 파일 임베딩 대기열 등록
    _queue_for_embedding(new_fpaths)

    state['processed_files'] = processed[-500:]
    state['last_session']    = datetime.now().strftime('%Y-%m-%d %H:%M')
    _save_state(state)

    print(f"  ✅ 완료: {len(results)}개 (약점·개념정리·임베딩큐 포함)")
    return results


# ==============================================================================
# 아침 브리핑
# ==============================================================================
def _get_clip_summary() -> str:
    """어제 클리핑 파일 제목 최대 5개 반환."""
    try:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        clip_dir = os.path.join(OBSIDIAN_VAULT_PATH, '클리핑')
        if not os.path.exists(clip_dir):
            return ""
        files = [
            f[len(yesterday)+1:-3]
            for f in os.listdir(clip_dir)
            if f.startswith(yesterday) and f.endswith('.md') and '클리핑목록' not in f
        ]
        if not files:
            return ""
        lines = '\n'.join(f"• {t}" for t in files[:5])
        more = f"\n  외 {len(files)-5}건" if len(files) > 5 else ""
        return f"\n\n📎 *어제 클리핑:*\n{lines}{more}"
    except:
        return ""


def send_morning_briefing(studied_titles: list[str]):
    today = date.today().isoformat()
    clip_summary = _get_clip_summary()

    # 야간학습도 없고 클리핑도 없으면 전송 안 함
    if not studied_titles and not clip_summary:
        return

    lines = []
    if studied_titles:
        lines.append("🌙 *어젯밤 자율 학습:*")
        lines.extend(f"• {t}" for t in studied_titles)
        lines.append(f"\n📝 예상 문제 → `야간학습/{today}.md`")

    msg = (
        f"☀️ *아침 브리핑* — {today}\n\n"
        + '\n'.join(lines)
        + clip_summary
    )
    _send_telegram(msg)


# ==============================================================================
# 백그라운드 루프
# ==============================================================================
def _run_loop(generate_fn):
    studied_tonight = []
    briefing_sent_date = None

    while True:
        try:
            now = datetime.now()
            today_str = date.today().isoformat()

            # 아침 브리핑 (야간학습 여부와 무관하게 클리핑 있으면 전송)
            if is_morning_briefing_time() and briefing_sent_date != today_str:
                send_morning_briefing(studied_tonight)
                print(f"  ☀️ [야간학습] 아침 브리핑 전송 완료")
                studied_tonight    = []
                briefing_sent_date = today_str

            # 대화 중엔 스킵 (sleep 포함 — 미포함 시 CPU 폭주)
            try:
                import onew_shared
                if onew_shared.is_quiet_period():
                    time.sleep(CHECK_INTERVAL_SEC)
                    continue
            except ImportError:
                pass
            # 동기화 중이면 대기
            try:
                import onew_shared
                if onew_shared.is_syncing():
                    time.sleep(30)
                    continue
            except ImportError:
                pass

            # 야간 / PC 유휴 / 대화 유휴 30분 중 하나면 학습 실행
            reason = None
            if is_night_hours():
                reason = "야간"
            elif is_idle():
                reason = f"PC 유휴 {IDLE_THRESHOLD_MIN}분"
            elif is_conversation_idle():
                reason = f"대화 없음 {CONV_IDLE_MIN}분"

            if reason:
                try:
                    import onew_budget
                    if not onew_budget.check_budget():
                        time.sleep(CHECK_INTERVAL_SEC)
                        continue
                except ImportError:
                    pass
                print(f"  📖 [자율학습] 트리거: {reason}")
                results = run_study_session(generate_fn)
                studied_tonight.extend(results)

        except Exception as e:
            print(f"  ⚠️ [야간학습] 오류: {e}")
            try:
                import onew_shared
                onew_shared.report_error("야간학습", e)
            except:
                pass

        time.sleep(CHECK_INTERVAL_SEC)


def start_background(generate_fn):
    """백그라운드 스레드로 시작"""
    t = threading.Thread(target=_run_loop, args=(generate_fn,), daemon=True)
    t.start()
    print("📖 [자율학습] 백그라운드 시작 (야간 / PC유휴 / 대화없음 30분 시 자동 실행)")
    return t


# ==============================================================================
# 단독 실행
# ==============================================================================
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    from google import genai

    api_key = _get_env('GEMINI_API_KEY')
    client  = genai.Client(api_key=api_key)
    gen_fn  = lambda p: client.models.generate_content(model='gemini-2.5-flash', contents=p).text

    print("🌙 야간 자율학습 단독 실행")
    results = run_study_session(gen_fn)
    if results:
        send_morning_briefing(results)
    else:
        print("처리할 새 노트 없음.")
