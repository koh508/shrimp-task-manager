"""
onew_review_scheduler.py
에빙하우스 망각 곡선 기반 복습 스케줄러
- 개념 학습 기록 → 1/3/7/21일 후 텔레그램 퀴즈 전송
- 약점노트와 연동 (WeaknessTracker에서 자동 등록)
"""
import os, json, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
REVIEW_DB    = os.path.join(SYSTEM_DIR, 'review_db.json')
NOTE_DIR     = os.path.join(OBSIDIAN_VAULT_PATH, '약점노트')

# 에빙하우스 복습 간격 (일)
INTERVALS = [1, 3, 7, 21]


# ==============================================================================
# DB 관리
# ==============================================================================
def _load_db() -> dict:
    if os.path.exists(REVIEW_DB):
        try:
            with open(REVIEW_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_db(db: dict):
    with open(REVIEW_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ==============================================================================
# 텔레그램 전송
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
        if not os.path.exists(ids_file):
            return
        with open(ids_file, 'r') as f:
            ids = json.load(f)
        if not ids:
            return
        chat_id = ids[0]
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown'
        }).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except Exception as e:
        print(f"  [복습알림] 전송 실패: {e}")


# ==============================================================================
# 퀴즈 생성
# ==============================================================================
def _build_quiz(concept: str, note_path: str | None, generate_fn) -> str:
    """개념 또는 노트 내용 기반 퀴즈 3문제 생성"""
    note_content = ""
    if note_path and os.path.exists(note_path):
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                note_content = f.read()[:2000]
        except:
            pass

    if note_content:
        prompt = (
            f"다음 학습 노트를 바탕으로 핵심 개념 퀴즈 3문제를 만들어라.\n"
            f"형식: 번호. 질문\n정답: 답\n\n"
            f"노트 내용:\n{note_content}"
        )
    else:
        prompt = (
            f"'{concept}'에 대한 핵심 퀴즈 3문제를 만들어라.\n"
            f"공조냉동기계기사/소방방재/현장 실무 맥락 우선.\n"
            f"형식: 번호. 질문\n정답: 답"
        )
    try:
        return generate_fn(prompt)
    except:
        return f"'{concept}' 개념을 다시 복습하세요."


# ==============================================================================
# 핵심 클래스
# ==============================================================================
class ReviewScheduler:
    def __init__(self, generate_fn):
        self.generate_fn = generate_fn
        self.db = _load_db()

    def register(self, concept: str, note_path: str | None = None):
        """개념 복습 스케줄 등록 (최초 1회만)"""
        if concept in self.db:
            return  # 이미 등록됨
        today = date.today().isoformat()
        next_review = (date.today() + timedelta(days=INTERVALS[0])).isoformat()
        self.db[concept] = {
            'first_studied': today,
            'reviews_done': 0,
            'next_review': next_review,
            'note_path': note_path,
        }
        _save_db(self.db)
        print(f"  📅 [복습등록] '{concept}' → {next_review} 첫 복습 예정")

    def get_due_today(self) -> list[dict]:
        """오늘 복습해야 할 개념 목록"""
        today = date.today().isoformat()
        due = []
        for concept, entry in self.db.items():
            if entry.get('reviews_done', 0) >= len(INTERVALS):
                continue  # 완료
            if entry.get('next_review', '9999') <= today:
                due.append({'concept': concept, **entry})
        return due

    def mark_reviewed(self, concept: str):
        """복습 완료 처리 → 다음 간격 계산"""
        if concept not in self.db:
            return
        entry = self.db[concept]
        done  = entry.get('reviews_done', 0) + 1
        entry['reviews_done'] = done
        if done < len(INTERVALS):
            next_date = (date.today() + timedelta(days=INTERVALS[done])).isoformat()
            entry['next_review'] = next_date
            print(f"  ✅ [복습완료] '{concept}' → 다음 복습: {next_date} ({INTERVALS[done]}일 후)")
        else:
            entry['next_review'] = 'mastered'
            print(f"  🏆 [완전학습] '{concept}' 망각곡선 완료!")
        _save_db(self.db)

    def run_daily_check(self):
        """시작 시 오늘 복습 항목 확인 → 텔레그램 전송"""
        due = self.get_due_today()
        if not due:
            return

        print(f"\n📅 [복습알림] 오늘 복습할 항목 {len(due)}개")
        for item in due:
            concept   = item['concept']
            note_path = item.get('note_path')
            done      = item.get('reviews_done', 0)
            interval  = INTERVALS[done] if done < len(INTERVALS) else INTERVALS[-1]

            print(f"  → '{concept}' (학습 후 {interval}일차 복습)")
            quiz = _build_quiz(concept, note_path, self.generate_fn)

            msg = (
                f"📚 *복습 알림* — {interval}일차\n"
                f"*개념:* {concept}\n\n"
                f"{quiz}\n\n"
                f"_온유에게 '복습완료: {concept}' 라고 말하면 다음 일정으로 넘어갑니다._"
            )
            _send_telegram(msg)
            # ⚠️ 버그수정: 텔레그램 전송 직후 자동 완료 처리하지 않음
            # 사용자가 '복습완료: {concept}' 입력 시에만 mark_reviewed() 호출

    def get_summary(self) -> str:
        """복습 현황 요약"""
        if not self.db:
            return "등록된 복습 일정이 없습니다."
        today = date.today().isoformat()
        lines = ["## 📅 복습 일정\n"]
        for concept, entry in sorted(self.db.items(), key=lambda x: x[1].get('next_review', '')):
            done  = entry.get('reviews_done', 0)
            nxt   = entry.get('next_review', '?')
            total = len(INTERVALS)
            if nxt == 'mastered':
                status = '🏆 완료'
            elif nxt <= today:
                status = '🔴 오늘 복습!'
            else:
                status = f'⏳ {nxt}'
            lines.append(f"- **{concept}** ({done}/{total}회) {status}")
        return '\n'.join(lines)
