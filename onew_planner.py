"""
onew_planner.py — 온유 Level 3: 목표지향형 자율 계획 엔진
──────────────────────────────────────────────────────────
- 매일 아침: 시험 D-day + 약점 + 복습 + 패턴 → 오늘 학습 계획 수립
- 계획 실행: 부족 노트 생성, 예상 문제 제작, 복습 스케줄 조정
- 저녁 보고: 달성도 + 내일 미리보기
- 텔레그램 전송 + Vault 저장
"""
import os, json, glob, time, threading, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
PLAN_DB      = os.path.join(SYSTEM_DIR, 'plan_db.json')
PLAN_DIR     = os.path.join(OBSIDIAN_VAULT_PATH, '학습계획')
EXAM_DATE    = date(2026, 4, 18)   # 공조냉동 실기

MORNING_HOUR = 7    # 아침 계획 전송 시각
EVENING_HOUR = 21   # 저녁 보고 시각

os.makedirs(PLAN_DIR, exist_ok=True)


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

def _load_db() -> dict:
    if os.path.exists(PLAN_DB):
        try:
            with open(PLAN_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_db(db: dict):
    with open(PLAN_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

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
# 데이터 수집 — 각 모듈 DB 읽기
# ==============================================================================
def _get_dday() -> int:
    return (EXAM_DATE - date.today()).days

def _get_weak_topics(top_n=3) -> list[dict]:
    """weakness_db에서 우선순위 높은 약점 토픽"""
    path = os.path.join(SYSTEM_DIR, 'weakness_db.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        scored = []
        for topic, entry in db.items():
            score = entry.get('count', 0) * 2 + entry.get('bad_count', 0) * 3
            has_note = os.path.exists(
                os.path.join(OBSIDIAN_VAULT_PATH, '약점노트', f"{topic}.md")
            )
            scored.append({'topic': topic, 'score': score, 'has_note': has_note, **entry})
        scored.sort(key=lambda x: -x['score'])
        return scored[:top_n]
    except:
        return []

def _get_due_reviews() -> list[str]:
    """review_db에서 오늘 복습할 항목"""
    path = os.path.join(SYSTEM_DIR, 'review_db.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        today = date.today().isoformat()
        due = []
        for concept, entry in db.items():
            if entry.get('reviews_done', 0) >= 4:
                continue
            if entry.get('next_review', '9999') <= today:
                due.append(concept)
        return due
    except:
        return []

def _get_meta_pattern() -> dict:
    """meta_db에서 최근 학습 패턴 요약"""
    path = os.path.join(SYSTEM_DIR, 'meta_db.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        topics = db.get('topics', {})
        # 최근 3일 이내 질문한 토픽
        recent = []
        cutoff = (date.today() - timedelta(days=3)).isoformat()
        for topic, entry in topics.items():
            if entry.get('last_seen', '')[:10] >= cutoff:
                recent.append(topic)
        return {'recent_topics': recent, 'total_topics': len(topics)}
    except:
        return {}

def _get_last_night_study() -> list[str]:
    """어젯밤 야간학습에서 처리된 노트 목록"""
    path = os.path.join(SYSTEM_DIR, 'night_study_state.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        today     = date.today().isoformat()
        recent = []
        for fpath in state.get('processed_files', []):
            try:
                mtime = date.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                if mtime in (yesterday, today):
                    recent.append(Path(fpath).stem)
            except:
                pass
        return recent[:5]
    except:
        return []


# ==============================================================================
# 계획 수립
# ==============================================================================
def _dday_phase(dday: int) -> str:
    if dday > 30:   return "준비기"
    if dday > 14:   return "집중기"
    if dday > 7:    return "마무리기"
    if dday > 0:    return "최종점검"
    return "시험당일"

def _dday_strategy(dday: int) -> str:
    if dday > 30:
        return "개념 이해 중심. 약점 발굴과 노트 구축에 집중."
    if dday > 14:
        return "반복 복습 강화. 약점 집중 공략. 문제풀이 병행."
    if dday > 7:
        return "기출 위주. 틀린 문제 재풀이. 핵심 공식 암기."
    return "핵심 공식·법칙만 압축 반복. 컨디션 관리 최우선."

def build_daily_plan(generate_fn) -> dict:
    """오늘의 학습 계획 수립"""
    today   = date.today().isoformat()
    dday    = _get_dday()
    phase   = _dday_phase(dday)
    strategy = _dday_strategy(dday)

    weak    = _get_weak_topics()
    reviews = _get_due_reviews()
    meta    = _get_meta_pattern()
    night   = _get_last_night_study()

    # Gemini로 구체적 계획 생성
    context = (
        f"시험 D-{dday} ({phase})\n"
        f"전략: {strategy}\n\n"
        f"약점 토픽: {[w['topic'] for w in weak]}\n"
        f"오늘 복습 예정: {reviews}\n"
        f"최근 3일 질문 토픽: {meta.get('recent_topics', [])}\n"
        f"어젯밤 야간학습 처리: {night}\n"
    )
    prompt = (
        f"공조냉동기계기사 실기 수험생의 오늘 학습 계획을 수립하라.\n\n"
        f"현황:\n{context}\n"
        f"출력 형식:\n"
        f"1. 오늘의 핵심 목표 (1줄)\n"
        f"2. 학습 순서 (번호 목록, 각 30~60분 단위)\n"
        f"3. 오늘 반드시 확인할 공식/개념 (3개)\n"
        f"4. 내일을 위한 준비 (1줄)\n"
        f"간결하게."
    )
    try:
        plan_text = generate_fn(prompt)
    except:
        plan_text = f"D-{dday} {phase}: 약점 복습 + 기출 풀이"

    plan = {
        'date':     today,
        'dday':     dday,
        'phase':    phase,
        'strategy': strategy,
        'weak':     [w['topic'] for w in weak],
        'reviews':  reviews,
        'plan_text': plan_text,
        'tasks':    _extract_tasks(weak, reviews),
        'completed': [],
        'generated_at': datetime.now().strftime('%H:%M'),
    }
    return plan

def _extract_tasks(weak: list, reviews: list) -> list[dict]:
    """실행 가능한 태스크 목록 생성"""
    tasks = []
    for w in weak:
        if not w.get('has_note'):
            tasks.append({'type': 'create_note', 'topic': w['topic'], 'done': False})
        tasks.append({'type': 'make_quiz', 'topic': w['topic'], 'done': False})
    for r in reviews[:3]:
        tasks.append({'type': 'review', 'topic': r, 'done': False})
    return tasks


# ==============================================================================
# 계획 실행
# ==============================================================================
def execute_tasks(plan: dict, generate_fn) -> list[str]:
    """태스크 자동 실행 → 완료 목록 반환"""
    completed = []
    for task in plan.get('tasks', []):
        if task.get('done'):
            continue
        topic = task['topic']
        try:
            if task['type'] == 'create_note':
                _create_study_note(topic, generate_fn)
                task['done'] = True
                completed.append(f"📝 {topic} 노트 생성")

            elif task['type'] == 'make_quiz':
                _create_quiz(topic, plan['date'], generate_fn)
                task['done'] = True
                completed.append(f"❓ {topic} 예상문제 생성")

            elif task['type'] == 'review':
                # 복습은 텔레그램으로 이미 전송됨 (review_scheduler)
                task['done'] = True
                completed.append(f"🔁 {topic} 복습 완료")

        except Exception as e:
            print(f"  ⚠️ [플래너] 태스크 실패 ({topic}): {e}")

    plan['completed'].extend(completed)
    return completed

def _create_study_note(topic: str, generate_fn):
    """약점 개념 학습 노트 자동 생성"""
    import re
    prompt = (
        f"'{topic}' 개념을 공조냉동기계기사 실기 수준에 맞게 정리하라.\n"
        f"포함: 정의 / 원리 / 핵심 공식 / 시험 출제 포인트 / 예시\n"
        f"마크다운 형식."
    )
    content = generate_fn(prompt)
    safe    = re.sub(r'[\\/:*?"<>|]', '_', topic)
    fpath   = os.path.join(OBSIDIAN_VAULT_PATH, '약점노트', f"{safe}.md")
    if not os.path.exists(fpath):
        today = date.today().isoformat()
        header = (
            f"---\ntags: [약점노트, 자율학습, {today}]\n"
            f"개념: {topic}\n날짜: {today}\n상태: 복습필요\n---\n\n"
            f"# ⚠️ {topic}\n\n> 온유 플래너 자동 생성\n\n"
        )
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(header + content)

def _create_quiz(topic: str, today: str, generate_fn):
    """예상 문제 생성 → 학습계획/ 저장"""
    prompt = (
        f"'{topic}' 공조냉동기계기사 실기 예상문제 3개.\n"
        f"형식: 번호. 문제\n정답: 답\n해설: 짧게"
    )
    content = generate_fn(prompt)
    import re
    safe    = re.sub(r'[\\/:*?"<>|]', '_', topic)
    fpath   = os.path.join(PLAN_DIR, f"{today}_퀴즈_{safe}.md")
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(
            f"---\ntags: [퀴즈, {today}]\n날짜: {today}\n---\n\n"
            f"# ❓ {topic} 예상문제\n\n{content}"
        )


# ==============================================================================
# Vault 저장 + 텔레그램 전송
# ==============================================================================
def save_plan_to_vault(plan: dict):
    today  = plan['date']
    dday   = plan['dday']
    fpath  = os.path.join(PLAN_DIR, f"{today}_학습계획.md")
    content = (
        f"---\ntags: [학습계획, D{dday}, {today}]\n"
        f"날짜: {today}\nD-day: {dday}\n단계: {plan['phase']}\n---\n\n"
        f"# 📅 {today} 학습 계획 — D-{dday}\n\n"
        f"**전략:** {plan['strategy']}\n\n"
        f"---\n\n"
        f"{plan['plan_text']}\n\n"
        f"---\n\n"
        f"## 자동 실행 태스크\n"
    )
    for t in plan.get('tasks', []):
        done = "✅" if t.get('done') else "⬜"
        content += f"- {done} [{t['type']}] {t['topic']}\n"
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

def send_morning_plan(plan: dict):
    dday  = plan['dday']
    phase = plan['phase']
    weak  = plan.get('weak', [])
    rev   = plan.get('reviews', [])

    msg = (
        f"☀️ *오늘의 학습 계획* — D-{dday} ({phase})\n\n"
        f"{plan['plan_text']}\n\n"
    )
    if weak:
        msg += f"*약점 집중:* {' · '.join(weak)}\n"
    if rev:
        msg += f"*오늘 복습:* {' · '.join(rev)}\n"
    msg += f"\n_온유가 노트·퀴즈를 자동 준비합니다._"
    _send_telegram(msg)

def send_evening_report(plan: dict):
    completed = plan.get('completed', [])
    tasks     = plan.get('tasks', [])
    total     = len(tasks)
    done_cnt  = len([t for t in tasks if t.get('done')])
    dday      = plan.get('dday', '?')

    msg = (
        f"🌙 *저녁 학습 보고* — D-{dday}\n\n"
        f"*달성:* {done_cnt}/{total}개\n\n"
    )
    if completed:
        msg += '\n'.join(f"• {c}" for c in completed) + '\n'

    # 내일 미리보기
    tomorrow_dday = dday - 1 if isinstance(dday, int) else '?'
    msg += f"\n*내일 D-{tomorrow_dday}:* {_dday_strategy(tomorrow_dday if isinstance(tomorrow_dday, int) else 99)[:30]}..."
    _send_telegram(msg)


# ==============================================================================
# 핵심 클래스
# ==============================================================================
class DailyPlanner:
    def __init__(self, generate_fn):
        self.generate_fn = generate_fn
        self.db          = _load_db()
        self._today_plan = None

    def run_morning(self):
        """아침 루틴: 계획 수립 → 실행 → 전송"""
        today = date.today().isoformat()
        if self.db.get('last_plan_date') == today:
            # 오늘 이미 실행됨 → 기존 계획 복원
            self._today_plan = self.db.get('today_plan')
            return

        print(f"\n📅 [플래너] 오늘의 학습 계획 수립 중... (D-{_get_dday()})")
        plan = build_daily_plan(self.generate_fn)
        save_plan_to_vault(plan)
        send_morning_plan(plan)

        # 태스크 자동 실행
        completed = execute_tasks(plan, self.generate_fn)
        if completed:
            print(f"  ✅ 자동 완료: {len(completed)}개")

        self._today_plan = plan
        self.db['last_plan_date'] = today
        self.db['today_plan']     = plan
        _save_db(self.db)

    def run_evening(self):
        """저녁 보고"""
        if self._today_plan:
            send_evening_report(self._today_plan)
            self.db['today_plan'] = self._today_plan
            _save_db(self.db)

    def get_today_plan(self) -> str:
        """현재 계획 요약 (터미널 출력용)"""
        plan = self._today_plan or self.db.get('today_plan')
        if not plan:
            return "오늘 계획이 아직 없어요. '계획 세워줘'라고 해보세요."
        dday  = plan.get('dday', '?')
        phase = plan.get('phase', '')
        tasks = plan.get('tasks', [])
        done  = len([t for t in tasks if t.get('done')])
        lines = [
            f"## 📅 오늘 계획 — D-{dday} ({phase})\n",
            plan.get('plan_text', ''),
            f"\n**진행:** {done}/{len(tasks)}개 완료"
        ]
        return '\n'.join(lines)

    def force_plan(self):
        """수동으로 계획 재수립"""
        self.db.pop('last_plan_date', None)
        self.run_morning()


# ==============================================================================
# 백그라운드 루프
# ==============================================================================
def _bg_loop(planner: DailyPlanner):
    last_morning = None
    last_evening = None

    # 시작 시 즉시 아침 루틴 실행
    try:
        planner.run_morning()
    except Exception as e:
        print(f"  ⚠️ [플래너] 아침 루틴 오류: {e}")

    while True:
        time.sleep(60)
        try:
            import onew_shared
            if onew_shared.is_quiet_period():
                continue
        except ImportError:
            pass
        try:
            now   = datetime.now()
            today = date.today().isoformat()

            # 아침 계획 (MORNING_HOUR시)
            if now.hour == MORNING_HOUR and last_morning != today:
                planner.run_morning()
                last_morning = today

            # 저녁 보고 (EVENING_HOUR시)
            if now.hour == EVENING_HOUR and last_evening != today:
                planner.run_evening()
                last_evening = today

        except Exception as e:
            print(f"  ⚠️ [플래너] 루프 오류: {e}")
            try:
                import onew_shared
                onew_shared.report_error("플래너", e)
            except:
                pass

def start_background(planner: DailyPlanner):
    t = threading.Thread(target=_bg_loop, args=(planner,), daemon=True)
    t.start()
    print("📅 [플래너] 백그라운드 시작 (아침 계획 + 저녁 보고)")
    return t
