"""
onew_weakness_tracker.py
대화에서 약점 개념 자동 감지 → 반복 시 약점노트 자동 생성
"""
import os, json, re
from datetime import datetime
from pathlib import Path

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_DIR   = os.path.dirname(os.path.abspath(__file__))
WEAKNESS_DB  = os.path.join(SYSTEM_DIR, 'weakness_db.json')
NOTE_DIR     = os.path.join(OBSIDIAN_VAULT_PATH, '약점노트')
THRESHOLD    = 2   # 몇 번 이상이면 노트 생성

# 약점 감지 키워드
WEAK_KEYWORDS = [
    '모르겠', '모르는데', '헷갈', '이해가 안', '이해 안',
    '뭐야', '뭔데', '뭐지', '뭐예요', '뭔가요',
    '맞아?', '맞나?', '맞지?', '맞는거야', '맞는건가',
    '틀렸어', '틀린거야', '틀린건가',
    '다시 설명', '다시 알려', '다시 말해',
    '어떻게 되는거야', '어떻게 되는건가', '어떻게 돼',
    '왜 그래', '왜 그런거야', '왜 그런건가',
    '차이가 뭐야', '차이가 뭔데', '차이 알려',
]

os.makedirs(NOTE_DIR, exist_ok=True)


def _load_db() -> dict:
    if os.path.exists(WEAKNESS_DB):
        try:
            with open(WEAKNESS_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def _save_db(db: dict):
    with open(WEAKNESS_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _is_weak_question(q: str) -> bool:
    q_lower = q.lower()
    return any(kw in q_lower for kw in WEAK_KEYWORDS)


def _extract_concept(q: str, answer: str, generate_fn) -> str | None:
    """Gemini로 핵심 개념어 추출 (1~5단어)"""
    prompt = (
        f"다음 질문에서 핵심 개념어를 1~5단어로만 추출하라. "
        f"예: '응축기', '냉매 순환 원리', 'PID 제어'. "
        f"설명 없이 개념어만 출력.\n\n질문: {q}"
    )
    try:
        result = generate_fn(prompt)
        concept = result.strip().split('\n')[0].strip()
        # 너무 길거나 이상한 경우 필터링
        if 1 <= len(concept) <= 30:
            return concept
    except:
        pass
    return None


def _safe_filename(concept: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', concept)


def _generate_note(concept: str, q: str, answer: str, history: list, generate_fn):
    """약점노트 MD 파일 생성/업데이트"""
    fname    = _safe_filename(concept) + '.md'
    fpath    = os.path.join(NOTE_DIR, fname)
    today    = datetime.now().strftime('%Y-%m-%d')
    now_str  = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 심화 설명 생성
    context = '\n'.join([f"Q: {r['q']}\nA: {r['a']}" for r in history[-3:]])
    prompt = (
        f"'{concept}'에 대해 헷갈려하는 학습자를 위한 핵심 정리 노트를 작성하라.\n"
        f"포함 내용:\n"
        f"1. 핵심 개념 한 줄 정의\n"
        f"2. 원리/이유 설명 (3~5줄)\n"
        f"3. 쉬운 비유 또는 예시\n"
        f"4. 혼동하기 쉬운 포인트\n"
        f"5. 핵심 공식 또는 체크포인트 (해당 시)\n\n"
        f"과거 질문 맥락:\n{context}"
    )
    try:
        note_body = generate_fn(prompt)
    except:
        note_body = answer

    # 기존 파일이 있으면 이력 추가, 없으면 신규 생성
    if os.path.exists(fpath):
        with open(fpath, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n\n## 📅 {now_str} 재질문\n\n**Q:** {q}\n\n{note_body}")
    else:
        content = (
            f"---\n"
            f"tags: [약점노트, 자율학습]\n"
            f"개념: {concept}\n"
            f"날짜: {today}\n"
            f"상태: 복습필요\n"
            f"---\n\n"
            f"# ⚠️ 약점: {concept}\n\n"
            f"> 이 노트는 온유가 반복 질문을 감지해 자동 생성했습니다.\n\n"
            f"---\n\n"
            f"## 📅 {now_str} 최초 기록\n\n"
            f"**Q:** {q}\n\n"
            f"{note_body}"
        )
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

    return fname


class WeaknessTracker:
    def __init__(self, generate_fn, review_scheduler=None):
        """generate_fn: Gemini 텍스트 생성 함수 (prompt → str)"""
        self.generate_fn = generate_fn
        self.review_scheduler = review_scheduler
        self.db = _load_db()

    def detect_and_log(self, q: str, answer: str) -> str | None:
        """
        약점 감지 → DB 기록 → 임계값 초과 시 노트 생성
        반환: 생성된 노트 파일명 (없으면 None)
        """
        if not _is_weak_question(q):
            return None

        concept = _extract_concept(q, answer, self.generate_fn)
        if not concept:
            return None

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        # DB 업데이트
        entry = self.db.get(concept, {'count': 0, 'history': []})
        entry['count'] += 1
        entry['last_seen'] = now_str
        entry['history'].append({'q': q, 'a': answer[:300], 'time': now_str})
        entry['history'] = entry['history'][-10:]  # 최근 10개만 유지
        self.db[concept] = entry
        _save_db(self.db)

        print(f"  📌 [약점감지] '{concept}' ({entry['count']}회)")

        # 임계값 초과 → 노트 생성
        if entry['count'] >= THRESHOLD:
            fname     = _generate_note(concept, q, answer, entry['history'], self.generate_fn)
            note_path = os.path.join(NOTE_DIR, fname)
            print(f"  📝 [약점노트] 생성/업데이트: 약점노트/{fname}")
            # 복습 스케줄 자동 등록
            if self.review_scheduler:
                self.review_scheduler.register(concept, note_path)
            return fname

        return None

    def get_summary(self) -> str:
        """약점 현황 요약 문자열"""
        if not self.db:
            return "아직 약점이 감지되지 않았습니다."
        lines = ["## ⚠️ 약점 현황\n"]
        for concept, entry in sorted(self.db.items(), key=lambda x: -x[1]['count']):
            lines.append(f"- **{concept}** ({entry['count']}회) — 마지막: {entry.get('last_seen', '?')}")
        return '\n'.join(lines)
