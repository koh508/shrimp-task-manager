"""
onew_task_manager.py — 온유 장기 태스크 관리
- 여러 세션에 걸친 멀티스텝 작업 추적
- onew_tasks.json에 영속 저장
- obsidian_agent.py의 tool로 연결됨
"""
import os, json
from datetime import datetime
from pathlib import Path

SYSTEM_DIR  = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE  = os.path.join(SYSTEM_DIR, 'onew_tasks.json')

STATUS_PENDING   = "대기"
STATUS_RUNNING   = "진행중"
STATUS_DONE      = "완료"
STATUS_FAILED    = "실패"
STATUS_CANCELLED = "취소"


# ── 영속 저장 ──────────────────────────────────────────────────────────────────
def _load() -> list:
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return []

def _save(tasks: list):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def _new_id() -> str:
    tasks = _load()
    return f"T{len(tasks)+1:03d}"


# ── 공개 인터페이스 ────────────────────────────────────────────────────────────
def task_create(title: str, steps: list[str], priority: str = "보통") -> str:
    """새 멀티스텝 태스크를 생성합니다.
    title: 태스크 제목
    steps: 순서대로 실행할 단계 목록 (예: ["파일 읽기", "내용 수정", "검증"])
    priority: '높음' / '보통' / '낮음'
    """
    tasks = _load()
    tid = _new_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    task = {
        "id": tid,
        "title": title,
        "priority": priority,
        "status": STATUS_PENDING,
        "steps": [{"desc": s, "status": STATUS_PENDING, "note": ""} for s in steps],
        "created": now,
        "updated": now,
        "log": [f"{now} 생성됨"]
    }
    tasks.append(task)
    _save(tasks)
    step_lines = '\n'.join(f"  {i+1}. {s}" for i, s in enumerate(steps))
    return f"✅ 태스크 생성: [{tid}] {title}\n단계:\n{step_lines}"


def task_list(status_filter: str = "") -> str:
    """현재 태스크 목록을 반환합니다.
    status_filter: '' (전체) / '대기' / '진행중' / '완료' / '실패'
    """
    tasks = _load()
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    if not tasks:
        return "태스크 없음."

    lines = []
    for t in tasks:
        done  = sum(1 for s in t["steps"] if s["status"] == STATUS_DONE)
        total = len(t["steps"])
        bar   = f"{done}/{total}"
        lines.append(f"[{t['id']}] {t['title']} — {t['status']} ({bar}) [{t['priority']}]")
        for i, s in enumerate(t["steps"]):
            icon = {"완료":"✅","진행중":"🔄","실패":"❌","취소":"⛔"}.get(s["status"], "⬜")
            note = f" ← {s['note']}" if s['note'] else ""
            lines.append(f"   {icon} {i+1}. {s['desc']}{note}")
    return '\n'.join(lines)


def task_update(task_id: str, step_index: int, status: str, note: str = "") -> str:
    """태스크의 특정 단계 상태를 업데이트합니다.
    task_id: 태스크 ID (예: 'T001')
    step_index: 단계 번호 (1부터 시작)
    status: '진행중' / '완료' / '실패'
    note: 메모 (선택)
    """
    tasks = _load()
    for task in tasks:
        if task["id"] != task_id:
            continue
        idx = step_index - 1
        if not (0 <= idx < len(task["steps"])):
            return f"Error: 단계 번호 {step_index}가 범위를 벗어남 (총 {len(task['steps'])}단계)"

        task["steps"][idx]["status"] = status
        task["steps"][idx]["note"]   = note
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        task["log"].append(f"{now} 단계{step_index} → {status}" + (f" ({note})" if note else ""))
        task["updated"] = now

        # 전체 태스크 상태 자동 갱신
        statuses = [s["status"] for s in task["steps"]]
        if all(s == STATUS_DONE for s in statuses):
            task["status"] = STATUS_DONE
        elif STATUS_FAILED in statuses:
            task["status"] = STATUS_FAILED
        elif STATUS_RUNNING in statuses:
            task["status"] = STATUS_RUNNING
        else:
            task["status"] = STATUS_PENDING

        _save(tasks)
        return f"✅ [{task_id}] 단계{step_index} '{task['steps'][idx]['desc']}' → {status}"

    return f"Error: 태스크 '{task_id}'를 찾을 수 없습니다."


def task_next(task_id: str = "") -> str:
    """다음 실행할 단계를 반환합니다. task_id 생략 시 진행중/대기 중 가장 우선순위 높은 태스크."""
    tasks = _load()
    active = [t for t in tasks if t["status"] in (STATUS_PENDING, STATUS_RUNNING)]
    if not active:
        return "현재 진행할 태스크 없음."

    if task_id:
        active = [t for t in active if t["id"] == task_id]
        if not active:
            return f"'{task_id}' 태스크를 찾을 수 없습니다."

    # 우선순위 정렬
    prio_order = {"높음": 0, "보통": 1, "낮음": 2}
    active.sort(key=lambda t: prio_order.get(t["priority"], 1))
    task = active[0]

    for i, step in enumerate(task["steps"]):
        if step["status"] == STATUS_PENDING:
            return (
                f"📋 [{task['id']}] {task['title']}\n"
                f"다음 단계 {i+1}/{len(task['steps'])}: {step['desc']}\n"
                f"완료 후: task_update('{task['id']}', {i+1}, '완료')"
            )
    return f"[{task['id']}] 모든 단계 완료 또는 실패 상태."


def task_cancel(task_id: str) -> str:
    """태스크를 취소합니다."""
    tasks = _load()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = STATUS_CANCELLED
            task["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save(tasks)
            return f"⛔ [{task_id}] '{task['title']}' 취소됨"
    return f"Error: '{task_id}' 없음"


def get_pending_summary() -> str:
    """시작 시 온유에게 보여줄 미완료 태스크 요약."""
    tasks = _load()
    active = [t for t in tasks if t["status"] in (STATUS_PENDING, STATUS_RUNNING)]
    if not active:
        return ""
    lines = [f"📋 미완료 태스크 {len(active)}개:"]
    for t in active:
        done = sum(1 for s in t["steps"] if s["status"] == STATUS_DONE)
        lines.append(f"  [{t['id']}] {t['title']} ({done}/{len(t['steps'])}단계)")
    return '\n'.join(lines)
