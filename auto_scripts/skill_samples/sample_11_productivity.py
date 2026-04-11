"""스킬: productivity_planning — ICE 스코어링 + 작업 분해 + 포모도로 타이머"""
from dataclasses import dataclass, field
from typing import Literal

# ── 1. ICE 스코어링 ───────────────────────────────────────────────────────────
@dataclass
class Task:
    name: str
    impact: int       # 1-10
    confidence: int   # 1-10
    ease: int         # 1-10
    status: Literal["todo", "in_progress", "done"] = "todo"

    def ice_score(self) -> int:
        return self.impact * self.confidence * self.ease

    def validate(self) -> None:
        for field_name, val in [("impact", self.impact), ("confidence", self.confidence), ("ease", self.ease)]:
            if not (1 <= val <= 10):
                raise ValueError(f"{field_name}은 1-10 범위여야 합니다. (현재: {val})")

def prioritize(tasks: list[Task]) -> list[Task]:
    for t in tasks:
        t.validate()
    return sorted(tasks, key=lambda t: t.ice_score(), reverse=True)

# ── 2. 작업 분해 (Task Decomposition) ────────────────────────────────────────
@dataclass
class SubTask:
    name: str
    done: bool = False

@dataclass
class Project:
    title: str
    subtasks: list[SubTask] = field(default_factory=list)

    def add(self, name: str) -> None:
        self.subtasks.append(SubTask(name))

    def complete(self, name: str) -> None:
        for st in self.subtasks:
            if st.name == name:
                st.done = True
                return
        raise KeyError(f"'{name}' 서브태스크 없음")

    def progress(self) -> float:
        if not self.subtasks:
            return 0.0
        done = sum(1 for st in self.subtasks if st.done)
        return round(done / len(self.subtasks) * 100, 1)

# ── 3. 포모도로 시뮬레이터 ────────────────────────────────────────────────────
class PomodoroSession:
    WORK_MIN = 25
    BREAK_MIN = 5

    def __init__(self):
        self.cycles: list[dict] = []

    def add_cycle(self, task_name: str, completed: bool = True) -> None:
        self.cycles.append({"task": task_name, "completed": completed})

    def total_focus_min(self) -> int:
        return sum(self.WORK_MIN for c in self.cycles if c["completed"])

    def summary(self) -> str:
        done = sum(1 for c in self.cycles if c["completed"])
        return f"완료 {done}/{len(self.cycles)} 사이클 ({self.total_focus_min()}분 집중)"

# ── 검증 ─────────────────────────────────────────────────────────────────────
tasks = [
    Task("스킬 캐시 최적화",   impact=7, confidence=9, ease=8),
    Task("LanceDB 마이그레이션", impact=9, confidence=5, ease=3),
    Task("작업일지 자동화",     impact=6, confidence=8, ease=9),
]
ranked = prioritize(tasks)
assert ranked[0].name == "스킬 캐시 최적화", f"1위: {ranked[0].name}"   # 504
assert ranked[1].name == "작업일지 자동화"                                  # 432
print("  [1] ICE 스코어링:")
for i, t in enumerate(ranked, 1):
    print(f"      {i}위 {t.name}: {t.ice_score()} (I={t.impact} C={t.confidence} E={t.ease})")

# 범위 검증
bad_task = Task("오류", impact=11, confidence=5, ease=5)
try:
    bad_task.validate()
    assert False
except ValueError as e:
    print(f"  [2] 범위 오류 차단: {e}")

# 작업 분해
proj = Project("온유 스킬 시스템")
for name in ["skills_server.py 구현", "optional 스킬 추가", "테스트 작성", "작업일지"]:
    proj.add(name)
proj.complete("skills_server.py 구현")
proj.complete("optional 스킬 추가")
assert proj.progress() == 50.0
print(f"  [3] 프로젝트 진행률: {proj.progress()}%")

# 포모도로
pomo = PomodoroSession()
for task in ["스킬 서버 구현", "테스트 작성", "문서화"]:
    pomo.add_cycle(task)
pomo.add_cycle("방해됨", completed=False)
assert pomo.total_focus_min() == 75
print(f"  [4] 포모도로: {pomo.summary()}")

print("PASS")
