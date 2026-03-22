"""
onew_study_engine.py — 학습 설계 엔진
────────────────────────────────────────
설계 계획 기반 학습 조율:
- onew_study_plan.json 커리큘럼 기반 목표/토픽 선택
- Vault 파일 우선 → AI 생성 fallback
- 마스터리 추적 (0.0~1.0) per 토픽
- 오답 → 약점트래커 자동 연동
- 진도 요약 / 계획 확인 출력

사용:
    engine = StudyEngine(generate_fn, weakness_tracker=wt, review_scheduler=rs)
    q = engine.pick_next_question()       # 다음 문제 선택
    engine.record_result(q, correct=True) # 결과 기록
    print(engine.get_progress_summary())  # 진도 출력
"""
import os
import json
import random
import hashlib
import glob as glob_mod
import re
from datetime import date, timedelta
from pathlib import Path

SYSTEM_DIR    = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH    = Path(r"C:\Users\User\Documents\Obsidian Vault")
PLAN_FILE     = os.path.join(SYSTEM_DIR, "onew_study_plan.json")
PROGRESS_FILE = os.path.join(SYSTEM_DIR, "onew_study_progress.json")

# 마스터리 점수 상수
MASTERY_CORRECT  = 0.10   # 정답 시 +
MASTERY_WRONG    = 0.08   # 오답 시 −
MASTERY_MASTERED = 0.80   # 이 이상 = '잘함'
MAX_FILES_PER_GOAL = 50   # 파싱 파일 상한


# ==============================================================================
# DB 관리
# ==============================================================================
def _load_plan() -> dict:
    if os.path.exists(PLAN_FILE):
        try:
            with open(PLAN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"goals": []}


def _load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"topics": {}, "recent_hashes": []}


def _save_progress(p: dict):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)


def _q_hash(q: str) -> str:
    return hashlib.md5(q.strip().encode("utf-8")).hexdigest()[:12]


# ==============================================================================
# Vault 문제 파서 (독립 — obsidian_agent에 의존하지 않음)
# ==============================================================================
# 다양한 문제 포맷 지원:
#   "문제: ...", "**문제:** ...", "1. **문제:** ...", "N. ..." (번호형)
_STRIP_MD = re.compile(r"\*+")   # ** 제거용
_Q_PAT = re.compile(r"^\*{0,2}문제\*{0,2}[:\s]\s*\*{0,2}\s*(.{5,})", re.IGNORECASE)
_Q_NUM = re.compile(r"^\s*\d+[\.)\s]\s+(.{10,}[?？])")       # "1. 압축기란?"
_A_PAT = re.compile(r"^\*{0,2}정답\*{0,2}[:\s]\s*\*{0,2}\s*(.+)", re.IGNORECASE)
_E_PAT = re.compile(r"^\*{0,2}해설\*{0,2}[:\s]\s*\*{0,2}\s*(.+)", re.IGNORECASE)


def _parse_vault_questions(vault_path_str: str) -> list:
    """
    Vault 경로에서 Q&A 쌍을 추출한다.
    단일 파일 또는 디렉토리 모두 지원.
    반환: [{"question": str, "answer": str, "explanation": str, "source": str}]
    """
    if not vault_path_str:
        return []

    # 경로 해석: 절대경로 vs Vault 기준 상대경로
    p = Path(vault_path_str)
    if not p.is_absolute():
        p = VAULT_PATH / vault_path_str

    if not p.exists():
        return []

    files = sorted(p.glob("*.md")) if p.is_dir() else ([p] if p.is_file() else [])
    files = files[:MAX_FILES_PER_GOAL]

    questions = []
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # ── 포맷 A: 야간학습 스타일 (번호 블록 내 **문제:** / **정답:**) ────
        # "1.  **문제:** 질문\n    **정답:** 정답"
        num_blocks = re.split(r"\n\s*\d+\.\s+", content)
        for block in num_blocks[1:]:
            qm = _Q_PAT.match(block.strip())
            if qm:
                q_text = _STRIP_MD.sub("", qm.group(1)).strip()
                am = _A_PAT.search(block)
                a_text = _STRIP_MD.sub("", am.group(1)).strip() if am else ""
                em = _E_PAT.search(block)
                e_text = _STRIP_MD.sub("", em.group(1)).strip() if em else ""
                is_latex = (q_text.startswith("=") or q_text.startswith("\\")
                            or q_text.count("\\") > 2 or q_text.count("$") > 1)
                if q_text and a_text and len(q_text) > 5 and not is_latex:
                    questions.append({
                        "question":    q_text[:300],
                        "answer":      a_text[:300],
                        "explanation": e_text[:200],
                        "source":      fp.name,
                    })

        # ── 포맷 B: 라인별 파싱 (문제:/정답: 형식, 번호 없는 경우) ──────────
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            qm2 = _Q_PAT.match(stripped) or _Q_NUM.match(stripped)
            if qm2:
                q_text = _STRIP_MD.sub("", qm2.group(1)).strip()
                a_text = e_text = ""
                for j in range(i + 1, min(i + 6, len(lines))):
                    l = lines[j].strip()
                    if not l:
                        break
                    am2 = _A_PAT.match(l)
                    if am2 and not a_text:
                        a_text = _STRIP_MD.sub("", am2.group(1)).strip()
                    em2 = _E_PAT.match(l)
                    if em2 and not e_text:
                        e_text = _STRIP_MD.sub("", em2.group(1)).strip()
                is_latex = (q_text.startswith("=") or q_text.startswith("\\")
                            or q_text.count("\\") > 2 or q_text.count("$") > 1)
                if q_text and a_text and len(q_text) > 5 and not is_latex:
                    questions.append({
                        "question":    q_text[:300],
                        "answer":      a_text[:300],
                        "explanation": e_text[:200],
                        "source":      fp.name,
                    })
            i += 1

    # 접두어 정리 + 중복 제거 (question 기준)
    _PREFIX = re.compile(r"^(?:문제|Q)[:\s.]\s*", re.IGNORECASE)
    seen = set()
    unique = []
    for q in questions:
        q["question"] = _PREFIX.sub("", q["question"]).strip()
        h = _q_hash(q["question"])
        if h not in seen:
            seen.add(h)
            unique.append(q)
    return unique


# ==============================================================================
# StudyEngine
# ==============================================================================
class StudyEngine:
    def __init__(self, generate_fn, weakness_tracker=None, review_scheduler=None):
        """
        generate_fn      : Gemini 텍스트 생성 함수 (prompt → str)
        weakness_tracker : WeaknessTracker 인스턴스 (선택)
        review_scheduler : ReviewScheduler 인스턴스 (선택)
        """
        self.generate_fn      = generate_fn
        self.weakness_tracker = weakness_tracker
        self.review_scheduler = review_scheduler
        self.plan     = _load_plan()
        self.progress = _load_progress()

    # ── 목표 선택 ──────────────────────────────────────────────────────────────
    def _get_goals(self) -> list:
        return self.plan.get("goals", [])

    def _pick_goal(self, hint: str = None) -> dict | None:
        goals = self._get_goals()
        if not goals:
            return None
        if hint:
            for g in goals:
                if hint in g.get("name", "") or hint == g.get("id", ""):
                    return g

        def urgency(g):
            try:
                days_left = (date.fromisoformat(g.get("deadline", "9999-12-31")) - date.today()).days
            except Exception:
                days_left = 9999
            return (g.get("priority", 99), days_left)

        return sorted(goals, key=urgency)[0]

    # ── 토픽 선택 ──────────────────────────────────────────────────────────────
    def _goal_topics(self, goal: dict) -> list:
        t = goal.get("topics", [])
        if not t:
            t = [s["name"] for s in goal.get("subjects", [])]
        return t

    def _pick_topic(self, goal: dict) -> str:
        today = date.today().isoformat()

        # 1순위: 복습 대상 (review_db)
        rdb_path = os.path.join(SYSTEM_DIR, "review_db.json")
        if os.path.exists(rdb_path):
            try:
                with open(rdb_path, "r", encoding="utf-8") as f:
                    rdb = json.load(f)
                due = [c for c, e in rdb.items()
                       if e.get("reviews_done", 0) < 4  # INTERVALS 길이
                       and e.get("next_review", "9999") <= today]
                if due:
                    return due[0]
            except Exception:
                pass

        # 2순위: 약점 (weakness_db)
        wdb_path = os.path.join(SYSTEM_DIR, "weakness_db.json")
        if os.path.exists(wdb_path):
            try:
                with open(wdb_path, "r", encoding="utf-8") as f:
                    wdb = json.load(f)
                weak = sorted(wdb.items(), key=lambda x: -x[1].get("count", 0))
                if weak and weak[0][1].get("count", 0) >= 2:
                    return weak[0][0]
            except Exception:
                pass

        # 3순위: 마스터리 최저 토픽 (오래 안 한 것 가중)
        topics_data = self.progress.get("topics", {})
        goal_topics = self._goal_topics(goal)

        if goal_topics:
            def score(t):
                td = topics_data.get(t, {})
                mastery = td.get("mastery", 0.0)
                try:
                    days_since = (date.today() - date.fromisoformat(td.get("last_studied", "2000-01-01"))).days
                except Exception:
                    days_since = 999
                # 낮은 마스터리 + 오래됨 → 점수 낮음 → 먼저 선택
                return mastery - min(days_since * 0.01, 0.3)

            return sorted(goal_topics, key=score)[0]

        return goal.get("name", "공조냉동기계기사 실기")

    # ── Vault 경로 조회 ────────────────────────────────────────────────────────
    def _get_vault_path(self, goal: dict | None, topic: str) -> str | None:
        if not goal:
            return None
        if "vault_path" in goal:
            return goal["vault_path"]
        for s in goal.get("subjects", []):
            if s.get("name") == topic:
                return s.get("vault_path")
        return None

    # ── AI 문제 생성 (fallback) ────────────────────────────────────────────────
    def _ai_question(self, topic: str, goal: dict | None) -> dict:
        context = goal.get("name", "공조냉동기계기사 실기") if goal else "공조냉동기계기사 실기"
        prompt = (
            f"다음 주제로 단답형/단문 서술형 문제 1개를 만들어라.\n"
            f"반드시 이 형식 준수:\n"
            f"문제: (내용)\n정답: (짧은 답)\n해설: (1~2줄)\n\n"
            f"과목: {context}\n주제: {topic}"
        )
        try:
            result = self.generate_fn(prompt).strip()
            lines = result.splitlines()
            q = a = e = ""
            for line in lines:
                ls = line.strip()
                if ls.startswith("문제:"):
                    q = ls[3:].strip()
                elif ls.startswith("정답:"):
                    a = ls[3:].strip()
                elif ls.startswith("해설:"):
                    e = ls[3:].strip()
            if q and a:
                return {
                    "question": q, "answer": a, "explanation": e,
                    "topic": topic, "goal_id": goal.get("id", "") if goal else "",
                    "from_vault": False, "source": "AI생성",
                }
        except Exception as err:
            print(f"  ⚠️ [학습엔진] AI 문제 생성 오류: {err}")

        return {
            "question": f"{topic}의 핵심 원리를 한 문장으로 설명하세요.",
            "answer": "(자유 서술)", "explanation": "",
            "topic": topic, "goal_id": "", "from_vault": False, "source": "fallback",
        }

    # ── 핵심: 다음 문제 선택 ───────────────────────────────────────────────────
    def pick_next_question(self, goal_hint: str = None) -> dict:
        """
        다음 학습 문제를 선택해 반환한다.
        우선순위: 복습 대상 → 약점 → 낮은 마스터리 토픽 → Vault → AI 생성
        """
        goal  = self._pick_goal(goal_hint)
        topic = self._pick_topic(goal) if goal else (goal_hint or "공조냉동기계기사 실기")

        vault_path = self._get_vault_path(goal, topic)
        if vault_path:
            vault_qs = _parse_vault_questions(vault_path)
            if vault_qs:
                recent = set(self.progress.get("recent_hashes", []))
                fresh  = [q for q in vault_qs if _q_hash(q["question"]) not in recent]
                pool   = fresh if fresh else vault_qs
                q = random.choice(pool)
                q.setdefault("topic",      topic)
                q.setdefault("goal_id",    goal.get("id", "") if goal else "")
                q.setdefault("from_vault", True)
                return q

        # Vault에서 문제를 못 찾으면 AI 생성
        return self._ai_question(topic, goal)

    # ── 결과 기록 ──────────────────────────────────────────────────────────────
    def record_result(self, q_dict: dict, correct: bool):
        """
        정답/오답 기록 → 마스터리 업데이트 → 오답 시 약점트래커 연동.
        q_dict: pick_next_question() 반환값
        """
        topic    = q_dict.get("topic", "")
        question = q_dict.get("question", "")
        answer   = q_dict.get("answer", "")

        topics_data = self.progress.setdefault("topics", {})
        entry = topics_data.get(topic, {
            "mastery": 0.0, "attempts": 0, "correct": 0, "last_studied": ""
        })
        entry["attempts"] = entry.get("attempts", 0) + 1
        if correct:
            entry["correct"] = entry.get("correct", 0) + 1
            entry["mastery"] = min(1.0, entry.get("mastery", 0.0) + MASTERY_CORRECT)
        else:
            entry["mastery"] = max(0.0, entry.get("mastery", 0.0) - MASTERY_WRONG)
        entry["last_studied"] = date.today().isoformat()
        topics_data[topic] = entry

        # 최근 문제 해시 기록 (중복 방지)
        h = _q_hash(question)
        recent = self.progress.get("recent_hashes", [])
        recent.append(h)
        self.progress["recent_hashes"] = recent[-300:]

        _save_progress(self.progress)

        # 오답 → 약점트래커
        if not correct and self.weakness_tracker and question:
            try:
                self.weakness_tracker.detect_and_log(question, answer)
            except Exception as e:
                print(f"  ⚠️ [학습엔진] 약점 연동 오류: {e}")

        # 마스터리 달성 → 복습 스케줄 등록
        if entry["mastery"] >= MASTERY_MASTERED and self.review_scheduler and topic:
            try:
                note_path = None
                note_dir = os.path.join(str(VAULT_PATH), "약점노트", topic + ".md")
                if os.path.exists(note_dir):
                    note_path = note_dir
                self.review_scheduler.register(topic, note_path)
            except Exception:
                pass

    # ── 진도 요약 ──────────────────────────────────────────────────────────────
    def get_progress_summary(self) -> str:
        goals  = self._get_goals()
        topics = self.progress.get("topics", {})

        if not goals:
            return "학습 목표 없음 — SYSTEM/onew_study_plan.json 확인"

        lines = ["## 학습 진도\n"]
        today = date.today()

        for goal in goals:
            try:
                days_left = (date.fromisoformat(goal.get("deadline", "9999-12-31")) - today).days
                dl_str = f" (D-{days_left})"
            except Exception:
                dl_str = ""

            lines.append(f"### {goal['name']}{dl_str}")
            goal_topics = self._goal_topics(goal)

            if not goal_topics:
                lines.append("  토픽 없음\n")
                continue

            mastered = sum(1 for t in goal_topics
                           if topics.get(t, {}).get("mastery", 0) >= MASTERY_MASTERED)
            lines.append(f"진도: {mastered}/{len(goal_topics)} 완료\n")

            for t in goal_topics:
                td      = topics.get(t, {})
                mastery = td.get("mastery", 0.0)
                att     = td.get("attempts", 0)
                filled  = int(mastery * 10)
                bar     = "#" * filled + "." * (10 - filled)
                icon    = "[완료]" if mastery >= MASTERY_MASTERED else ("[학습중]" if mastery > 0 else "[ ]")
                lines.append(f"  {icon} {t}: [{bar}] {mastery:.0%} ({att}회)")

            lines.append("")

        return "\n".join(lines)

    def get_plan_summary(self) -> str:
        """설계 계획 확인 출력"""
        goals = self._get_goals()
        if not goals:
            return "학습 계획 없음 — SYSTEM/onew_study_plan.json 확인"

        lines = ["## 학습 설계 계획\n"]
        today = date.today()

        for g in goals:
            try:
                days_left = (date.fromisoformat(g.get("deadline", "9999-12-31")) - today).days
                dl_str = f"| 마감 {g['deadline']} (D-{days_left})"
            except Exception:
                dl_str = ""

            lines.append(f"**{g['name']}** {dl_str}")
            lines.append(f"  우선순위: {g.get('priority', '?')}순위")

            goal_topics = self._goal_topics(g)
            if goal_topics:
                preview = ", ".join(goal_topics[:5])
                suffix  = f" 외 {len(goal_topics)-5}개" if len(goal_topics) > 5 else ""
                lines.append(f"  토픽 ({len(goal_topics)}개): {preview}{suffix}")

            vault = g.get("vault_path", "")
            if vault:
                lines.append(f"  Vault: {vault}")
            lines.append("")

        return "\n".join(lines)
