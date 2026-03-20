"""
onew_adhd_coach.py — ADHD 학습 코치
────────────────────────────────────
- 텔레그램으로 1문제씩 배달 → 답 기다림 → 평가 → 다음 문제
- 아침 공부 약속 받기 → 안 지키면 부드럽게 찌르기
- 어제 멈춘 곳 기억 → 이어서 제안
- 잘 했을 때 짧게 인정 (판단 없이)
"""
import os, json, time, threading, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

SYSTEM_DIR  = os.path.dirname(os.path.abspath(__file__))
STATE_FILE  = os.path.join(SYSTEM_DIR, 'adhd_coach_state.json')
VAULT_PATH  = Path(r"C:\Users\User\Documents\Obsidian Vault")

# 세션 설정
MIN_QUESTIONS_PER_SESSION = 3
MAX_QUESTIONS_PER_SESSION = 7
NUDGE_AFTER_COMMIT_MIN    = 90   # 약속 후 이 시간 지나도 안 하면 찌르기 (분)


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
        data = urllib.parse.urlencode(
            {'chat_id': ids[0], 'text': msg, 'parse_mode': 'Markdown'}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except:
        pass


def _load_state() -> dict:
    today = date.today().isoformat()
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                s = json.load(f)
            # 날짜 바뀌면 일일 카운터 리셋 (streak 유지)
            if s.get('date') != today:
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                streak = s.get('streak_days', 0)
                if s.get('date') == yesterday and s.get('questions_today', 0) >= MIN_QUESTIONS_PER_SESSION:
                    streak += 1
                elif s.get('questions_today', 0) < MIN_QUESTIONS_PER_SESSION:
                    streak = 0
                s.update({
                    'date': today,
                    'questions_today': 0,
                    'correct_today': 0,
                    'committed_minutes': 0,
                    'commitment_kept': False,
                    'nudge_sent': False,
                    'morning_asked': False,
                    'streak_days': streak,
                    'in_session': False,
                    'current_q': None,
                    'current_topic': s.get('last_topic', ''),
                })
                _save_state(s)
            return s
        except:
            pass
    return {
        'date': today,
        'questions_today': 0,
        'correct_today': 0,
        'committed_minutes': 0,
        'commitment_kept': False,
        'nudge_sent': False,
        'morning_asked': False,
        'streak_days': 0,
        'in_session': False,
        'current_q': None,
        'current_topic': '',
        'last_topic': '',
        'last_study_time': '',
        'session_q_count': 0,
    }


def _save_state(s: dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


# ==============================================================================
# 학습 컨텐츠 선택
# ==============================================================================
def _pick_topic(state: dict) -> str:
    """오늘 공부할 토픽 선택 (복습 우선 → 약점 → 시험 과목)"""
    today = date.today().isoformat()

    # 1순위: 복습 대상
    db_file = os.path.join(SYSTEM_DIR, 'review_db.json')
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
            due = [c for c, e in db.items() if e.get('next_review', '9999') <= today]
            if due:
                return due[0]
        except:
            pass

    # 2순위: 약점
    wb_file = os.path.join(SYSTEM_DIR, 'weakness_db.json')
    if os.path.exists(wb_file):
        try:
            with open(wb_file, 'r', encoding='utf-8') as f:
                wb = json.load(f)
            weak = sorted(wb.items(), key=lambda x: -x[1].get('count', 0))
            if weak:
                return weak[0][0]
        except:
            pass

    # 3순위: 어제 했던 토픽
    if state.get('last_topic'):
        return state['last_topic']

    return '공조냉동기계기사 실기'


def _generate_question(topic: str, generate_fn) -> dict:
    """Gemini로 1문제 생성"""
    is_field = any(k in topic for k in ['소각', '배기', '집진', '폐열', '스크러버'])
    context = "소각장 현장 운전 실무, 트러블슈팅 중심" if is_field else \
              "공조냉동기계기사 실기 시험 또는 소방방재 자격시험"

    prompt = (
        f"다음 주제로 단답형 또는 단문 서술형 문제 1개를 만들어라.\n"
        f"형식 (반드시 지킬 것):\n"
        f"문제: (문제 내용)\n"
        f"정답: (짧은 정답)\n"
        f"해설: (1~2줄)\n\n"
        f"맥락: {context}\n"
        f"주제: {topic}"
    )
    try:
        result = generate_fn(prompt)
        lines = result.strip().split('\n')
        q = a = e = ''
        for line in lines:
            if line.startswith('문제:'):
                q = line[3:].strip()
            elif line.startswith('정답:'):
                a = line[3:].strip()
            elif line.startswith('해설:'):
                e = line[3:].strip()
        if q and a:
            return {'question': q, 'answer': a, 'explanation': e, 'topic': topic}
    except:
        pass
    return {'question': f'{topic}의 핵심 원리를 한 문장으로 설명하세요.',
            'answer': '(자유 서술)', 'explanation': '', 'topic': topic}


def _evaluate_answer(user_ans: str, correct_ans: str, question: str, generate_fn) -> tuple[bool, str]:
    """답변 평가 — (맞음 여부, 피드백 메시지)"""
    prompt = (
        f"학습자의 답변이 정답에 가까운지 판단하라.\n"
        f"문제: {question}\n"
        f"정답: {correct_ans}\n"
        f"학습자 답: {user_ans}\n\n"
        f"판단: '맞음' 또는 '틀림' 으로 시작 후 1줄 피드백.\n"
        f"틀렸으면 정답 핵심을 짧게 알려줄 것. 절대 길게 쓰지 말 것."
    )
    try:
        result = generate_fn(prompt).strip()
        correct = result.startswith('맞음')
        return correct, result
    except:
        return False, f"정답: {correct_ans}"


# ==============================================================================
# 코치 클래스
# ==============================================================================
class ADHDCoach:
    def __init__(self, generate_fn):
        self.generate_fn = generate_fn

    def get_session(self) -> dict:
        return _load_state()

    def is_in_session(self) -> bool:
        return _load_state().get('in_session', False)

    # ── 아침 약속 요청 ─────────────────────────────────────────────────────────
    def morning_ask(self):
        state = _load_state()
        if state.get('morning_asked'):
            return
        state['morning_asked'] = True
        _save_state(state)

        streak = state.get('streak_days', 0)
        streak_msg = f"🔥 {streak}일 연속 중!" if streak >= 2 else ""

        _send_telegram(
            f"☀️ *좋은 아침이에요, 용준씨* {streak_msg}\n\n"
            f"오늘 공부 몇 분 할 수 있어요?\n\n"
            f"👉 숫자만 답하거나 '패스'라고 하세요.\n"
            f"예: `10` 또는 `패스`"
        )

    # ── 약속 입력 처리 ─────────────────────────────────────────────────────────
    def handle_commitment(self, text: str) -> bool:
        """'10', '15', '패스' 같은 약속 응답 처리. 처리했으면 True"""
        state = _load_state()
        if state.get('commitment_kept') or state.get('in_session'):
            return False

        text = text.strip()
        if text == '패스':
            _send_telegram("알겠어요. 나중에 할 수 있을 때 '공부 시작'이라고 해주세요.")
            return True

        if text.isdigit():
            minutes = int(text)
            state['committed_minutes'] = minutes
            state['commitment_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            _save_state(state)
            _send_telegram(
                f"좋아요! {minutes}분 약속했어요. 🎯\n"
                f"준비되면 *'공부 시작'* 이라고 말해주세요."
            )
            return True

        return False

    # ── 세션 시작 ──────────────────────────────────────────────────────────────
    def start_session(self, topic: str = '') -> str:
        state = _load_state()
        if state.get('in_session'):
            return "이미 세션 진행 중이에요."

        if not topic:
            topic = _pick_topic(state)

        q_data = _generate_question(topic, self.generate_fn)
        state['in_session']    = True
        state['current_q']     = q_data
        state['current_topic'] = topic
        state['last_topic']    = topic
        state['session_q_count'] = 0
        _save_state(state)

        prev = state.get('last_study_time', '')
        prev_msg = f"_{state.get('last_topic', '')} 이어서 시작합니다._\n\n" if prev else ""

        _send_telegram(
            f"📚 *학습 시작* — {topic}\n\n"
            f"{prev_msg}"
            f"*Q.* {q_data['question']}\n\n"
            f"_답을 입력하세요. 모르면 '모름'이라고 해도 돼요._"
        )
        return ''

    # ── 답변 처리 ──────────────────────────────────────────────────────────────
    def handle_answer(self, text: str):
        state = _load_state()
        if not state.get('in_session') or not state.get('current_q'):
            return

        q_data = state['current_q']

        # 세션 종료 명령
        if text.strip() in ['그만', '종료', '끝', '그만할게', '그만 할게']:
            self._end_session(state)
            return

        # '모름' 처리
        if text.strip() in ['모름', '몰라', '?', 'ㅁ', '모르겠어']:
            state['questions_today'] = state.get('questions_today', 0) + 1
            state['session_q_count'] = state.get('session_q_count', 0) + 1
            feedback = f"괜찮아요. 정답은:\n*{q_data['answer']}*"
            if q_data.get('explanation'):
                feedback += f"\n_{q_data['explanation']}_"
            correct = False
        else:
            correct, feedback = _evaluate_answer(
                text, q_data['answer'], q_data['question'], self.generate_fn
            )
            state['questions_today'] = state.get('questions_today', 0) + 1
            state['session_q_count'] = state.get('session_q_count', 0) + 1
            if correct:
                state['correct_today'] = state.get('correct_today', 0) + 1

        state['last_study_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        q_count = state['session_q_count']

        # 세션 종료 조건
        if q_count >= MAX_QUESTIONS_PER_SESSION:
            _send_telegram(f"{feedback}\n\n")
            _save_state(state)
            self._end_session(state)
            return

        # 다음 문제 생성
        next_q = _generate_question(state['current_topic'], self.generate_fn)
        state['current_q'] = next_q
        _save_state(state)

        # 격려 메시지
        if correct:
            encourage = "✅ 맞아요!"
        elif q_count == 1:
            encourage = "괜찮아요, 다음 문제!"
        else:
            encourage = "다시 한번 도전해봐요!"

        # 중간 쉬어가기 (3문제마다)
        if q_count % 3 == 0 and q_count < MAX_QUESTIONS_PER_SESSION:
            more_msg = (
                f"\n\n{q_count}문제 완료! 👏\n"
                f"계속할까요? *'계속'* 또는 *'그만'* 으로 답해주세요."
            )
            state['in_session'] = False  # 잠깐 대기 모드
            state['waiting_continue'] = True
            _save_state(state)
            _send_telegram(f"{encourage}\n{feedback}{more_msg}")
            return

        _send_telegram(
            f"{encourage}\n{feedback}\n\n"
            f"*Q{q_count + 1}.* {next_q['question']}\n\n"
            f"_모르면 '모름'이라고 해도 돼요._"
        )

    # ── '계속' / '그만' 응답 처리 ─────────────────────────────────────────────
    def handle_continue(self, text: str) -> bool:
        state = _load_state()
        if not state.get('waiting_continue'):
            return False

        text = text.strip()
        if text in ['계속', '응', 'ㅇ', '계속해', '더']:
            state['waiting_continue'] = False
            state['in_session'] = True
            next_q = _generate_question(state['current_topic'], self.generate_fn)
            state['current_q'] = next_q
            _save_state(state)
            _send_telegram(
                f"좋아요! 계속 갑니다 💪\n\n"
                f"*Q.* {next_q['question']}\n\n"
                f"_모르면 '모름'이라고 해도 돼요._"
            )
            return True

        if text in ['그만', '종료', '끝', '그만할게']:
            state['waiting_continue'] = False
            _save_state(state)
            self._end_session(state)
            return True

        return False

    # ── 세션 종료 ──────────────────────────────────────────────────────────────
    def _end_session(self, state: dict):
        state['in_session']      = False
        state['waiting_continue'] = False
        state['current_q']       = None
        state['commitment_kept'] = True
        q = state.get('questions_today', 0)
        c = state.get('correct_today', 0)
        streak = state.get('streak_days', 0)

        # 격려 메시지
        if q >= MIN_QUESTIONS_PER_SESSION:
            state['streak_days'] = streak + 1 if streak == 0 else streak
            msg = (
                f"🎉 *오늘 학습 완료!*\n\n"
                f"문제 {q}개 도전, {c}개 정답\n"
                f"🔥 {state['streak_days']}일 연속 학습\n\n"
                f"_잘 했어요. 짧아도 했다는 게 중요해요._"
            )
        else:
            msg = (
                f"📖 *학습 종료*\n\n"
                f"오늘 {q}문제 풀었어요.\n"
                f"_조금이라도 했다는 거, 정말 잘한 거예요._"
            )

        _save_state(state)
        _send_telegram(msg)

    # ── 약속 안 지키면 넛지 ────────────────────────────────────────────────────
    def nudge_if_needed(self):
        state = _load_state()
        if state.get('commitment_kept') or state.get('nudge_sent'):
            return
        if not state.get('committed_minutes') or not state.get('commitment_time'):
            return

        commit_time = datetime.strptime(state['commitment_time'], '%Y-%m-%d %H:%M')
        elapsed_min = (datetime.now() - commit_time).total_seconds() / 60

        if elapsed_min >= NUDGE_AFTER_COMMIT_MIN:
            state['nudge_sent'] = True
            _save_state(state)
            _send_telegram(
                f"💬 *용준씨, 오늘 {state['committed_minutes']}분 약속했었어요.*\n\n"
                f"지금 딱 3문제만 해볼까요?\n"
                f"*'공부 시작'* 이라고 말해주세요."
            )

    # ── 진입점: 텔레그램 메시지 처리 ──────────────────────────────────────────
    def handle_message(self, text: str) -> bool:
        """
        텔레그램 메시지를 코치가 처리하면 True, 일반 대화로 넘기면 False
        """
        state = _load_state()
        t = text.strip()

        # 약속 대기 중
        if state.get('morning_asked') and not state.get('committed_minutes') \
                and not state.get('commitment_kept'):
            if self.handle_commitment(t):
                return True

        # 계속/그만 대기
        if state.get('waiting_continue'):
            if self.handle_continue(t):
                return True

        # 세션 중 → 답변 처리
        if state.get('in_session'):
            self.handle_answer(t)
            return True

        # 세션 시작 명령
        if t in ['공부 시작', '공부시작', '시작', '문제 줘', '문제줘', '문제', '공부']:
            topic = state.get('last_topic', '')
            self.start_session(topic)
            return True

        return False

    # ── 배경 루프 ──────────────────────────────────────────────────────────────
    def run_background(self):
        while True:
            try:
                try:
                    import onew_shared
                    if onew_shared.is_quiet_period():
                        time.sleep(60)
                        continue
                except ImportError:
                    pass

                now = datetime.now()
                is_weekday = now.weekday() < 5
                if is_weekday and now.hour == 6 and now.minute < 10:
                    self.morning_ask()
                elif not is_weekday and 9 <= now.hour < 10:
                    self.morning_ask()
                self.nudge_if_needed()
            except Exception as e:
                print(f"  ⚠️ [ADHD코치] 오류: {e}")
                try:
                    import onew_shared
                    onew_shared.report_error("ADHD코치", e)
                except:
                    pass
            time.sleep(300)  # 5분마다 체크


def start_background(coach: 'ADHDCoach'):
    t = threading.Thread(target=coach.run_background, daemon=True)
    t.start()
    print("🧠 [ADHD코치] 백그라운드 시작 (아침 약속 + 넛지)")
    return t
