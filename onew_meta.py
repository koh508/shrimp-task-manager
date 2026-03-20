"""
onew_meta.py  — 온유 자기 인식 엔진 (Level 2 자율형)
────────────────────────────────────────────────────
기능:
  1. 대화 토픽 추적 → 반복/공백/장기미접속 패턴 감지
  2. 답변 만족도 추정 (재질문 패턴 분석)
  3. Vault 공백 감지 → 노트 부재 경고
  4. 능동적 제안 생성 (터미널 출력 + 텔레그램)
  5. 자기개선 제안 → onew_to_claude.md 자동 작성
"""
import os, json, re, glob, threading, time, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import Counter

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
META_DB      = os.path.join(SYSTEM_DIR, 'meta_db.json')
CLAUDE_MEMO  = os.path.join(SYSTEM_DIR, 'onew_to_claude.md')

# 분석 임계값
REPEAT_THRESHOLD    = 3    # 이 횟수 이상 같은 토픽 → 노트 생성 제안
STALE_DAYS          = 14   # 이 일수 이상 미접속 → 복습 제안
POOR_ANSWER_LIMIT   = 2    # 같은 세션 내 재질문 이 횟수 → 품질 경고
IDLE_CHECK_SEC      = 600  # 10분마다 패턴 분석


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
    if os.path.exists(META_DB):
        try:
            with open(META_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'topics': {}, 'sessions': [], 'proposals_sent': []}

def _save_db(db: dict):
    with open(META_DB, 'w', encoding='utf-8') as f:
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

def _vault_has_note(topic: str) -> bool:
    """Vault 전체에서 토픽 관련 파일 존재 여부"""
    pattern = os.path.join(OBSIDIAN_VAULT_PATH, '**', '*.md')
    for fpath in glob.glob(pattern, recursive=True):
        if 'SYSTEM' in fpath or 'code_backup' in fpath:
            continue
        if topic.lower() in Path(fpath).stem.lower():
            return True
    return False

def _vault_note_count(folder: str) -> int:
    path = os.path.join(OBSIDIAN_VAULT_PATH, folder)
    if not os.path.exists(path):
        return 0
    return len(glob.glob(os.path.join(path, '**', '*.md'), recursive=True))


# ==============================================================================
# 토픽 추출 (Gemini)
# ==============================================================================
def _extract_topic(q: str, generate_fn) -> str | None:
    prompt = (
        "다음 질문에서 핵심 학습 토픽을 1~4단어로 추출하라. "
        "학습/공부/업무와 무관하면 '없음'을 출력. "
        "설명 없이 토픽만.\n\n"
        f"질문: {q}"
    )
    try:
        result = generate_fn(prompt).strip().split('\n')[0].strip()
        if result == '없음' or len(result) > 20:
            return None
        return result
    except:
        return None


# ==============================================================================
# 만족도 신호 분류
# ==============================================================================
SATISFIED_KW  = ['알겠어', '이해했어', '고마워', '맞아', '오케이', 'ok', '완벽', '덕분']
UNSATISFIED_KW = ['다시', '좀 더', '왜', '이해 안', '헷갈', '다르게', '다른 방법', '아닌데', '틀렸']

def _satisfaction_signal(q: str) -> str:
    """'good' | 'bad' | 'neutral'"""
    ql = q.lower()
    if any(k in ql for k in SATISFIED_KW):
        return 'good'
    if any(k in ql for k in UNSATISFIED_KW):
        return 'bad'
    return 'neutral'


# ==============================================================================
# 자기개선 제안 → onew_to_claude.md
# ==============================================================================
def _write_improvement_proposal(topic: str, questions: list[str], generate_fn):
    """반복 불만족 패턴 감지 → Claude에게 개선 제안 자동 작성"""
    q_list = '\n'.join(f"- {q}" for q in questions[-5:])
    prompt = (
        f"온유(Gemini RAG 에이전트)가 '{topic}' 관련 질문에 반복적으로 불충분한 답변을 했다.\n"
        f"반복된 질문들:\n{q_list}\n\n"
        f"Claude Code에게 보낼 개선 요청 프롬프트를 작성하라. "
        f"포함 내용: 문제 원인 추정 / 구체적 개선 방향 / 수정이 필요한 파일 추정.\n"
        f"한국어로 간결하게."
    )
    try:
        proposal = generate_fn(prompt)
    except:
        proposal = f"'{topic}' 관련 반복 질문 발생. 노트 또는 RAG 응답 개선 필요."

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    block = (
        f"\n\n---\n\n"
        f"## {now} — '{topic}' 개선 제안\n\n"
        f"{proposal}\n\n"
        f"> 자동 생성됨 by onew_meta.py"
    )

    if not os.path.exists(CLAUDE_MEMO):
        with open(CLAUDE_MEMO, 'w', encoding='utf-8') as f:
            f.write(
                "---\ntags: [온유, 자기개선, Claude협업]\n---\n\n"
                "# 🤝 온유 → Claude 개선 제안\n"
                "_온유가 스스로 한계를 감지하고 Claude에게 보내는 개선 요청 모음_\n"
            )
    with open(CLAUDE_MEMO, 'a', encoding='utf-8') as f:
        f.write(block)

    print(f"\n  🤝 [자기개선] '{topic}' 개선 제안 → onew_to_claude.md 작성됨")
    _send_telegram(
        f"🤝 *온유 자기개선 감지*\n\n"
        f"*토픽:* {topic}\n"
        f"반복 불만족 패턴을 감지해 Claude에게 개선 요청을 작성했습니다.\n"
        f"`SYSTEM/onew_to_claude.md` 확인 후 Claude Code에 붙여넣기 해주세요."
    )


# ==============================================================================
# 핵심 클래스
# ==============================================================================
class MetaEngine:
    def __init__(self, generate_fn):
        self.generate_fn  = generate_fn
        self.db           = _load_db()
        self._session_topics: list[str] = []   # 현재 세션 토픽 목록
        self._session_bad:  Counter     = Counter()  # 세션 내 불만족 카운트

    # ── 매 질문마다 호출 ──────────────────────────────────────────────────────
    def observe(self, q: str, answer: str) -> str | None:
        """
        질문/답변 관찰 → DB 기록 → 즉시 제안이 있으면 반환 (없으면 None)
        """
        today   = date.today().isoformat()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        signal  = _satisfaction_signal(q)

        # 토픽 추출 (비동기 느낌으로 결과 무시 가능)
        topic = _extract_topic(q, self.generate_fn)
        if not topic:
            return None

        # DB 업데이트
        entry = self.db['topics'].get(topic, {
            'count': 0, 'bad_count': 0, 'last_seen': '',
            'questions': [], 'has_note': False
        })
        entry['count']    += 1
        entry['last_seen'] = now_str
        entry['questions'].append(q)
        entry['questions'] = entry['questions'][-10:]

        if signal == 'bad':
            entry['bad_count'] = entry.get('bad_count', 0) + 1
            self._session_bad[topic] += 1

        entry['has_note'] = _vault_has_note(topic)
        self.db['topics'][topic] = entry
        self._session_topics.append(topic)
        _save_db(self.db)

        # ── 즉시 제안 판단 ──
        suggestion = self._check_immediate(topic, entry, signal)
        return suggestion

    def _check_immediate(self, topic: str, entry: dict, signal: str) -> str | None:
        """즉각 반환할 제안 생성"""
        proposals_sent = set(self.db.get('proposals_sent', []))

        # 1. 같은 세션에서 같은 토픽 불만족 2회 이상
        if self._session_bad[topic] >= POOR_ANSWER_LIMIT:
            key = f"improve:{topic}"
            if key not in proposals_sent:
                _write_improvement_proposal(
                    topic, entry['questions'], self.generate_fn
                )
                proposals_sent.add(key)
                self.db['proposals_sent'] = list(proposals_sent)
                _save_db(self.db)
            return None

        # 2. 반복 질문인데 Vault 노트 없음
        if entry['count'] >= REPEAT_THRESHOLD and not entry['has_note']:
            key = f"nonote:{topic}"
            if key not in proposals_sent:
                proposals_sent.add(key)
                self.db['proposals_sent'] = list(proposals_sent)
                _save_db(self.db)
                return (
                    f"\n  💡 [온유 제안] '{topic}'을 {entry['count']}번 물어보셨는데 "
                    f"관련 노트가 없어요. 약점노트로 만들어드릴까요? ('약점노트 만들어줘: {topic}')"
                )

        return None

    # ── 주기적 분석 (백그라운드) ──────────────────────────────────────────────
    def run_periodic_analysis(self):
        """10분마다 전체 패턴 분석 → 능동적 제안"""
        today = date.today().isoformat()
        now   = datetime.now()
        suggestions = []

        for topic, entry in self.db['topics'].items():
            last = entry.get('last_seen', '')
            if not last:
                continue
            try:
                last_dt = datetime.strptime(last[:10], '%Y-%m-%d')
                days_ago = (now - last_dt).days
            except:
                continue

            # 장기 미접속 토픽
            if days_ago >= STALE_DAYS and entry.get('count', 0) >= 2:
                key = f"stale:{topic}:{today}"
                if key not in self.db.get('proposals_sent', []):
                    suggestions.append(
                        f"• *{topic}* — {days_ago}일째 복습 안 함 ({entry['count']}번 학습)"
                    )
                    self.db.setdefault('proposals_sent', []).append(key)

        # Vault 공백 감지
        thin_folders = []
        for folder in ['OCU', '약점노트', '대화요약']:
            cnt = _vault_note_count(folder)
            if cnt < 3:
                thin_folders.append(f"{folder}/ ({cnt}개)")

        if suggestions or thin_folders:
            msg_lines = ["🧠 *온유 자율 분석 보고*\n"]
            if suggestions:
                msg_lines.append("*장기 미복습 토픽:*\n" + '\n'.join(suggestions))
            if thin_folders:
                msg_lines.append("\n*Vault 공백 감지:*\n" + '\n'.join(f"• {f}" for f in thin_folders))
            msg_lines.append("\n_온유에게 '오늘 공부할 것 추천해줘'라고 해보세요._")
            _send_telegram('\n'.join(msg_lines))
            _save_db(self.db)

    def get_summary(self) -> str:
        """현황 요약"""
        topics = self.db.get('topics', {})
        if not topics:
            return "아직 수집된 패턴이 없습니다."
        lines = ["## 🧠 학습 패턴 현황\n"]
        for topic, entry in sorted(topics.items(), key=lambda x: -x[1]['count'])[:10]:
            note = "📝" if entry.get('has_note') else "❌노트없음"
            bad  = f" ⚠️불만족{entry['bad_count']}회" if entry.get('bad_count', 0) > 0 else ""
            lines.append(f"- **{topic}** {entry['count']}회 {note}{bad} — {entry.get('last_seen','?')[:10]}")
        return '\n'.join(lines)

    def recommend_today(self) -> str:
        """오늘 공부할 것 추천"""
        topics = self.db.get('topics', {})
        if not topics:
            return "아직 학습 데이터가 없어요. 조금 더 대화해봐요!"

        now = datetime.now()
        scored = []
        for topic, entry in topics.items():
            score = 0
            # 자주 물어봤지만 노트 없음 → 높은 우선순위
            if not entry.get('has_note'):
                score += entry['count'] * 2
            # 오래 안 봤을수록 우선순위 up
            try:
                last_dt = datetime.strptime(entry['last_seen'][:10], '%Y-%m-%d')
                score += (now - last_dt).days
            except:
                pass
            # 불만족 기록 있으면 추가 우선순위
            score += entry.get('bad_count', 0) * 3
            scored.append((topic, score))

        scored.sort(key=lambda x: -x[1])
        top = scored[:3]

        lines = ["## 📚 오늘 추천 학습\n"]
        for i, (topic, score) in enumerate(top, 1):
            entry  = topics[topic]
            reason = []
            if not entry.get('has_note'):
                reason.append("노트 없음")
            if entry.get('bad_count', 0) > 0:
                reason.append(f"불만족 {entry['bad_count']}회")
            try:
                days = (now - datetime.strptime(entry['last_seen'][:10], '%Y-%m-%d')).days
                if days > 7:
                    reason.append(f"{days}일 미복습")
            except:
                pass
            reason_str = ' · '.join(reason) if reason else '자주 질문'
            lines.append(f"{i}. **{topic}** ({reason_str})")

        return '\n'.join(lines)


# ==============================================================================
# 백그라운드 루프
# ==============================================================================
def _bg_loop(engine: MetaEngine):
    while True:
        time.sleep(IDLE_CHECK_SEC)
        try:
            import onew_shared
            if onew_shared.is_quiet_period():
                continue
        except ImportError:
            pass
        try:
            engine.run_periodic_analysis()
        except Exception as e:
            print(f"  ⚠️ [메타엔진] 분석 오류: {e}")
            try:
                import onew_shared
                onew_shared.report_error("메타엔진", e)
            except:
                pass

def start_background(engine: MetaEngine):
    t = threading.Thread(target=_bg_loop, args=(engine,), daemon=True)
    t.start()
    print("🧠 [메타엔진] 백그라운드 시작 (10분마다 패턴 분석)")
    return t
