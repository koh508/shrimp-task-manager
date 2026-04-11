"""
onew_code_planner.py — 온유 자율 코딩 계획 실행 레이어

v2 개선:
  1. Abort        : 선행 태스크 실패 → 후행 태스크 즉시 skipped + 플랜 중단
  2. Context Chain: 완료 태스크 결과를 다음 태스크 프롬프트에 주입
  3. Rollback     : 플랜 시작 전 스냅샷 → 최종 실패 시 전체 원상복구
  4. Vision       : interface_summary.json 으로 LLM에 실제 코드 구조 제공

v3 개선:
  5. TDD 강제     : modify/create 직후 verify 태스크 자동 삽입
  6. HITL Gate    : 코어 파일 수정 시 텔레그램 승인 대기
  7. 오답 노트    : 롤백 시 실패 경험 → onew_reasoning_log.json 기록 + 다음 프롬프트 주입
  8. 설계 원칙    : 프롬프트에 코딩 가이드라인 주입 (전역변수 금지 등)
"""
import ast
import difflib
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

SYSTEM_DIR        = os.path.dirname(os.path.abspath(__file__))
PLAN_QUEUE        = os.path.join(SYSTEM_DIR, "onew_code_plan_queue.json")
CHANGE_LOG_DIR    = os.path.join(SYSTEM_DIR, "코드변경이력")
INTERFACE_SUMMARY = os.path.join(SYSTEM_DIR, "interface_summary.json")
REASONING_LOG     = os.path.join(SYSTEM_DIR, "onew_reasoning_log.json")
PLANNER_CONTEXT   = os.path.join(SYSTEM_DIR, "onew_planner_context.json")  # 온유 대화 주입용
MAX_TASKS         = 10
PLAN_HISTORY      = 20

# [v3-6] 핵심 코어 파일 — 수정 시 인간 승인 필요
CORE_FILES = {
    "obsidian_agent.py",
    "onew_code_planner.py",
    "onew_self_improve.py",
    "onew_locks.py",
    "onew_tools.py",
}

# [v3-8] 설계 원칙 — 모든 코드 생성/수정 프롬프트에 주입
DESIGN_PRINCIPLES = """=== 설계 원칙 (반드시 준수) ===
- 전역 변수 사용 금지 (모듈 상수는 대문자, 런타임 상태는 파일에 영속화)
- 순환 참조(Circular Import) 절대 금지 (의존 방향: tools → locks → core)
- 순수 함수(Pure Function) 우선 — 외부 상태 의존 없이 인수/반환값으로만 동작
- 함수 1개 = 책임 1개 (단일 책임 원칙)
- 예외는 로깅 후 상위로 전파하거나 명시적 실패값 반환
- API 키 하드코딩 금지 — 환경변수 사용"""


# ==============================================================================
# [데이터 모델]
# ==============================================================================
def _new_task(desc, task_type, target, issue="", depends_on=None):
    return {
        "id":         str(uuid.uuid4())[:8],
        "desc":       desc,
        "type":       task_type,   # modify | create | verify
        "target":     target,
        "issue":      issue,
        "depends_on": depends_on or [],
        "status":     "pending",   # pending|running|done|failed|skipped
        "result":     "",
        "created_at": datetime.now().isoformat(),
    }


def _new_plan(goal, tasks):
    return {
        "id":         str(uuid.uuid4())[:8],
        "goal":       goal,
        "status":     "pending",   # pending|running|done|failed|aborted|waiting_approval
        "tasks":      tasks,
        "snapshot":   {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


# ==============================================================================
# [저장/로드]
# ==============================================================================
def _load_queue():
    if not os.path.exists(PLAN_QUEUE):
        return {"plans": []}
    try:
        with open(PLAN_QUEUE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"plans": []}


def _save_queue(data):
    plans    = data.get("plans", [])
    active   = [p for p in plans if p["status"] in ("pending", "running", "waiting_approval")]
    finished = [p for p in plans if p["status"] not in ("pending", "running", "waiting_approval")]
    data["plans"] = active + finished[-PLAN_HISTORY:]
    tmp = PLAN_QUEUE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PLAN_QUEUE)


# ==============================================================================
# [알림]
# ==============================================================================
def _notify(msg):
    try:
        token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, timeout=5
        )
    except Exception:
        pass


# ==============================================================================
# [Fix 4] 코드 구조 컨텍스트 로드 (interface_summary.json)
# ==============================================================================
def _load_interface_summary(max_chars=3000):
    """interface_summary.json → LLM 프롬프트용 요약 문자열."""
    if not os.path.exists(INTERFACE_SUMMARY):
        return "(interface_summary.json 없음 — onew_contract.py 실행 필요)"
    try:
        with open(INTERFACE_SUMMARY, encoding="utf-8") as f:
            summary = json.load(f)
        lines = []
        for fname, info in summary.items():
            if not fname.endswith(".py"):
                continue
            desc    = info.get("description", "")
            funcs   = info.get("functions", [])
            fn_list = ", ".join(funcs[:8])
            lines.append(f"  {fname}: {desc} | 함수: {fn_list}")
        text = "\n".join(lines)
        return text[:max_chars]
    except Exception as e:
        return f"(요약 로드 실패: {e})"


# ==============================================================================
# [Fix 3] 트랜잭션 스냅샷 / 롤백
# ==============================================================================
def _take_snapshot(plan):
    """플랜 실행 전 modify 대상 파일 전체 스냅샷."""
    snapshot = {}
    for task in plan["tasks"]:
        if task["type"] == "modify":
            path = _resolve_target(task["target"])
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        snapshot[task["target"]] = f.read()
                except Exception:
                    pass
    plan["snapshot"] = snapshot


def _rollback_plan(plan):
    """플랜 중단 시 스냅샷으로 전체 복구."""
    snapshot = plan.get("snapshot", {})
    rolled   = []

    for filename, content in snapshot.items():
        path = os.path.join(SYSTEM_DIR, filename)
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp, path)
            rolled.append(f"복원: {filename}")
        except Exception as e:
            rolled.append(f"복원실패: {filename} ({e})")

    for task in plan["tasks"]:
        if task["type"] == "create" and task["status"] == "done":
            path = _resolve_target(task["target"])
            if os.path.exists(path) and task["target"] not in snapshot:
                try:
                    os.remove(path)
                    rolled.append(f"삭제: {task['target']}")
                except Exception:
                    pass

    return rolled


# ==============================================================================
# [Fix 1] Abort — 실패 전파
# ==============================================================================
def _propagate_failure(failed_id, all_tasks):
    """실패 태스크에 의존하는 모든 후행 태스크를 skipped 처리 (전이적)."""
    failed_ids = {failed_id}
    changed    = True
    while changed:
        changed = False
        for t in all_tasks:
            if t["status"] == "pending" and any(dep in failed_ids for dep in t["depends_on"]):
                t["status"] = "skipped"
                t["result"] = f"선행 태스크({[d for d in t['depends_on'] if d in failed_ids]}) 실패로 건너뜀"
                failed_ids.add(t["id"])
                changed = True
    return failed_ids


# ==============================================================================
# [Fix 2] Context Chain — 선행 결과 주입
# ==============================================================================
def _build_context(task, all_tasks):
    """의존 태스크의 결과를 컨텍스트 문자열로 조합."""
    if not task["depends_on"]:
        return ""
    done_map = {t["id"]: t for t in all_tasks if t["status"] == "done"}
    parts    = []
    for dep_id in task["depends_on"]:
        if dep_id in done_map:
            dep = done_map[dep_id]
            parts.append(f"[선행완료] {dep['desc']}\n결과: {dep['result'][:300]}")
    return "\n\n".join(parts)


# ==============================================================================
# [v3-5] TDD 강제 — modify/create 직후 verify 자동 삽입
# ==============================================================================
def _ensure_tdd_order(tasks_raw):
    """modify 직후 테스트 파일이 존재하면 verify 자동 삽입.
    .py 파일에만 적용. .md/.json 등 비-Python 파일은 절대 verify 삽입 안 함."""
    result = []
    for i, task in enumerate(tasks_raw):
        result.append(task)
        t_type = task.get("type", "modify")
        target = task.get("target", "")

        # 확장자가 .py가 아니면 무조건 건너뜀 — 절대 verify 삽입 안 함
        if not os.path.basename(target).endswith(".py"):
            continue

        # create는 자동 삽입 안 함 (테스트 파일 미존재)
        if t_type != "modify":
            continue

        base          = os.path.basename(target)
        expected_test = f"test_{base}" if not base.startswith("test_") else base

        # 테스트 파일이 실제로 존재할 때만 삽입
        test_path = _resolve_target(expected_test)
        if not os.path.exists(test_path):
            continue

        # 다음 태스크가 이미 이 파일의 verify면 건너뜀
        next_t = tasks_raw[i + 1] if i + 1 < len(tasks_raw) else None
        if (next_t
                and next_t.get("type") == "verify"
                and next_t.get("target") == expected_test):
            continue

        result.append({
            "desc":       f"[TDD] {target} 변경 검증",
            "type":       "verify",
            "target":     expected_test,
            "issue":      f"{target} 수정 완료 후 pytest 실행",
            "depends_on": [],
        })
    return result[:MAX_TASKS]


# ==============================================================================
# [v3-6] HITL — 코어 파일 수정 감지
# ==============================================================================
def _has_core_file(tasks):
    """코어 파일을 건드리는 태스크가 있으면 True."""
    return any(
        t.get("target") in CORE_FILES and t.get("type") in ("modify", "create")
        for t in tasks
    )


def approve_plan(plan_id=None):
    """'승인' 명령 처리 — waiting_approval 플랜을 pending으로 전환."""
    data    = _load_queue()
    waiting = [p for p in data.get("plans", []) if p["status"] == "waiting_approval"]
    if not waiting:
        return "승인 대기 중인 계획 없음"
    target = next((p for p in waiting if p["id"] == plan_id), waiting[-1])
    target["status"]     = "pending"
    target["updated_at"] = datetime.now().isoformat()
    _save_queue(data)
    _notify(f"✅ [코드플래너] 계획 승인됨\n목표: {target['goal'][:50]}")
    return f"✅ 계획 승인됨 — 실행 시작: {target['goal'][:60]}"


def reject_plan(plan_id=None):
    """'거부' 명령 처리 — waiting_approval 플랜을 cancelled로 전환."""
    data    = _load_queue()
    waiting = [p for p in data.get("plans", []) if p["status"] == "waiting_approval"]
    if not waiting:
        return "승인 대기 중인 계획 없음"
    target = next((p for p in waiting if p["id"] == plan_id), waiting[-1])
    target["status"]     = "cancelled"
    target["updated_at"] = datetime.now().isoformat()
    _save_queue(data)
    _notify(f"🚫 [코드플래너] 계획 거부됨\n목표: {target['goal'][:50]}")
    return f"🚫 계획 거부됨: {target['goal'][:60]}"


# ==============================================================================
# [v3-7] 오답 노트 — 실패 기록 / 로드
# ==============================================================================
def _save_code_change(target: str, old_content: str, goal: str):
    """수정된 파일의 diff를 SYSTEM/코드변경이력/ 에 .md로 저장하고 터미널에 요약 출력."""
    try:
        path = _resolve_target(target)
        if not os.path.exists(path):
            return
        new_content = Path(path).read_text(encoding="utf-8")

        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"{target} (이전)",
            tofile=f"{target} (이후)",
            lineterm=""
        ))

        if not diff:
            return  # 변경 없음

        added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

        now = datetime.now()
        ts  = now.strftime("%Y-%m-%d_%H%M")
        safe_name = target.replace("/", "_").replace("\\", "_")

        # diff 내용이 너무 길면 앞부분만 (최대 100줄)
        diff_text = "\n".join(diff[:100])
        if len(diff) > 100:
            diff_text += f"\n... (생략: {len(diff)-100}줄 더 있음)"

        md = (
            f"---\n"
            f"tags: [코드변경이력]\n"
            f"날짜: {now.strftime('%Y-%m-%d')}\n"
            f"파일: {target}\n"
            f"목표: {goal[:80]}\n"
            f"---\n\n"
            f"# 코드 변경 이력: {target}\n\n"
            f"**변경 시각:** {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"**목표:** {goal[:120]}\n"
            f"**변경:** +{added}줄 추가 / -{removed}줄 삭제\n\n"
            f"```diff\n{diff_text}\n```\n"
        )

        os.makedirs(CHANGE_LOG_DIR, exist_ok=True)
        log_path = os.path.join(CHANGE_LOG_DIR, f"{ts}_{safe_name}.md")
        tmp = log_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(md)
        os.replace(tmp, log_path)

        # 터미널 요약 출력
        summary = f"[변경이력] {target}: +{added}줄 / -{removed}줄 -> {os.path.basename(log_path)}"
        try:
            print(summary)
        except UnicodeEncodeError:
            pass

    except Exception:
        pass


def _log_failure(plan, failed_task):
    """롤백 발생 시 실패 경험을 onew_reasoning_log.json에 기록."""
    entry = {
        "timestamp":        datetime.now().isoformat(),
        "goal":             plan["goal"],
        "failed_task_desc": failed_task["desc"],
        "failed_task_type": failed_task["type"],
        "failed_target":    failed_task.get("target", ""),
        "error":            failed_task.get("result", "")[:400],
    }
    try:
        log = []
        if os.path.exists(REASONING_LOG):
            with open(REASONING_LOG, encoding="utf-8") as f:
                log = json.load(f)
        log.append(entry)
        log = log[-50:]  # 최대 50개 유지
        tmp = REASONING_LOG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        os.replace(tmp, REASONING_LOG)
    except Exception:
        pass


def _save_planner_context(plan, touched_files, status):
    """플랜 완료/중단 결과를 onew_planner_context.json에 저장 (온유 대화 주입용)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "status":    status,
        "goal":      plan["goal"],
        "files":     touched_files,
    }
    try:
        records = []
        if os.path.exists(PLANNER_CONTEXT):
            with open(PLANNER_CONTEXT, encoding="utf-8") as f:
                records = json.load(f)
        records.append(entry)
        records = records[-10:]  # 최근 10개만 유지
        tmp = PLANNER_CONTEXT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        os.replace(tmp, PLANNER_CONTEXT)
    except Exception:
        pass


def get_recent_context(max_entries=3):
    """최근 플래너 실행 결과 + 현재 진행 중인 플랜 → 온유 대화 주입용 문자열."""
    lines = []

    # 1) 현재 대기/실행 중인 플랜 (큐에서 직접 읽기)
    try:
        data   = _load_queue()
        active = [p for p in data.get("plans", [])
                  if p["status"] in ("pending", "running", "waiting_approval")]
        has_waiting = any(p["status"] == "waiting_approval" for p in active)
        if active:
            lines.append("[현재 진행 중인 플래너 작업]")
            for p in active:
                done_files = [t["target"] for t in p["tasks"]
                              if t["status"] == "done" and t["type"] in ("create", "modify")]
                pending_files = [t["target"] for t in p["tasks"]
                                 if t["status"] in ("pending", "running") and t["type"] in ("create", "modify")]
                lines.append(f"⏳ [{p['status']}] {p['goal'][:60]}")
                if done_files:
                    lines.append(f"   완료된 파일: {', '.join(done_files)}")
                if pending_files:
                    lines.append(f"   예정된 파일: {', '.join(pending_files)}")
            if has_waiting:
                lines.append(
                    "⛔ [Agent 지시] waiting_approval 플랜이 있습니다. "
                    "Agent가 write_file/task_create로 직접 파일을 생성/수정하는 것은 엄격히 금지됩니다. "
                    "사용자에게 '승인 또는 거부를 입력해 주세요' 라고만 안내하십시오."
                )
    except Exception:
        pass

    # 2) 최근 완료/중단된 플랜 이력
    if os.path.exists(PLANNER_CONTEXT):
        try:
            with open(PLANNER_CONTEXT, encoding="utf-8") as f:
                records = json.load(f)
            if records:
                lines.append("[최근 완료된 플래너 작업]")
                for r in records[-max_entries:]:
                    ts    = r["timestamp"][:16].replace("T", " ")
                    icon  = "✅" if r["status"] == "done" else "🔴"
                    files = ", ".join(r["files"]) if r["files"] else "없음"
                    lines.append(f"{icon} {ts} — {r['goal'][:50]}")
                    lines.append(f"   파일: {files}")
        except Exception:
            pass

    return "\n".join(lines) if lines else ""


def _load_failure_lessons(max_entries=5):
    """최근 실패 경험 → 프롬프트 주입용 문자열."""
    if not os.path.exists(REASONING_LOG):
        return ""
    try:
        with open(REASONING_LOG, encoding="utf-8") as f:
            log = json.load(f)
        if not log:
            return ""
        recent = log[-max_entries:]
        lines  = ["=== 과거 실패 기록 (동일한 실수 반복 금지) ==="]
        for e in recent:
            lines.append(
                f"- 목표: {e['goal'][:60]}\n"
                f"  실패: [{e['failed_task_type']}] {e['failed_task_desc'][:60]}\n"
                f"  원인: {e['error'][:150]}"
            )
        return "\n".join(lines)
    except Exception:
        return ""


# ==============================================================================
# [계획 생성]
# ==============================================================================
def create_plan(goal, client=None):
    """목표를 Gemini로 태스크 목록으로 분해하고 큐에 저장."""
    if client is None:
        _notify("⚠️ [코드플래너] Gemini 클라이언트 없음")
        return None

    interface_ctx  = _load_interface_summary()
    failure_ctx    = _load_failure_lessons()
    failure_section = f"\n{failure_ctx}\n" if failure_ctx else ""

    # 실제 존재하는 수정 가능 파일 목록 동적 생성
    from onew_contract import SCAN_FILES as _scan
    existing_files = [f for f in _scan if os.path.exists(os.path.join(SYSTEM_DIR, f))]
    allowed_targets = "\n".join(f"  - {f}" for f in existing_files)

    # 성장 로드맵 로드 (있으면)
    roadmap_path = os.path.join(SYSTEM_DIR, "onew_growth_roadmap.md")
    roadmap_ctx = ""
    if os.path.exists(roadmap_path):
        try:
            with open(roadmap_path, encoding="utf-8") as f:
                roadmap_raw = f.read()
            # "채택하지 않는 것" 섹션만 추출
            if "채택하지 않는 것" in roadmap_raw:
                start = roadmap_raw.index("채택하지 않는 것")
                roadmap_ctx = "\n=== 채택 금지 기술 (절대 사용 금지) ===\n" + roadmap_raw[start:start+600]
        except Exception:
            pass

    prompt = f"""온유 자율 코딩 시스템입니다.
다음 목표를 달성하기 위한 코딩 태스크 목록을 JSON으로 작성하세요.

목표: {goal}

=== 수정 가능한 파일 목록 (이 목록 외의 파일은 절대 target으로 지정 금지) ===
{allowed_targets}

=== 새 파일 생성 규칙 ===
- create 태스크: SYSTEM 폴더 직접 하위에만 생성 가능 (src/, tests/ 등 하위 폴더 생성 금지)
- 파일명은 "onew_" 접두어 사용 (예: onew_new_feature.py)
- 테스트 파일은 "test_onew_" 접두어 사용

=== 현재 시스템 파일 구조 (interface_summary) ===
{interface_ctx}
{roadmap_ctx}
{failure_section}
{DESIGN_PRINCIPLES}

규칙:
1. 태스크 최대 {MAX_TASKS}개, 각각 단일 파일 단위로 원자적 실행 가능
2. type: "modify"(기존 파일 수정) / "create"(새 파일 생성) / "verify"(pytest 실행)
3. modify target은 반드시 위 "수정 가능한 파일 목록"에서만 선택할 것 — 목록에 없는 파일은 수정 불가
4. [TDD] .py 파일을 modify할 때만 verify 태스크 배치 (.md 등 비-Python 파일은 verify 불필요)
   - 패턴: modify A.py → verify test_A.py → modify B.py → verify test_B.py
   - .md, .json 등 비-Python 파일 create/modify 후에는 verify 태스크 추가하지 말 것
5. modify의 issue: 위 함수 목록을 참고한 구체적 수정 요구사항 (어떤 함수를 어떻게)
6. create의 issue: 파일 목적 + 포함할 핵심 함수/클래스 명세
7. depends_on: 빈 배열 (순서로 의존성 표현)
8. 실행 가능한 순서로 정렬

JSON만 반환 (다른 텍스트 없이):
{{"tasks": [{{"desc": "...", "type": "modify|create|verify", "target": "파일명.py", "issue": "...", "depends_on": []}}]}}"""

    try:
        from google.genai import types as _t
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=_t.GenerateContentConfig(
                temperature=0.2,
                thinking_config=_t.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0]
        parsed    = json.loads(raw.strip())
        tasks_raw = parsed.get("tasks", [])[:MAX_TASKS]
    except Exception as e:
        _notify(f"⚠️ [코드플래너] 계획 생성 실패: {e}")
        return None

    if not tasks_raw:
        _notify("⚠️ [코드플래너] 생성된 태스크 없음")
        return None

    # [검증] modify 대상 파일이 실제 존재하는지 계획 생성 시점에 확인
    invalid_modify = [
        t for t in tasks_raw
        if t.get("type") == "modify" and t.get("target") not in existing_files
    ]
    if invalid_modify:
        bad_names = [t["target"] for t in invalid_modify]
        tasks_raw = [t for t in tasks_raw if t not in invalid_modify]
        warn_msg = f"[코드플래너] 존재하지 않는 파일 수정 시도 제거: {bad_names}"
        try:
            print(f"!! {warn_msg}")
        except UnicodeEncodeError:
            pass
        _notify(f"⚠️ {warn_msg}")
        if not tasks_raw:
            _notify("⚠️ [코드플래너] 유효한 태스크가 없어 계획 취소")
            return None

    # 비-Python 파일의 verify 태스크 제거 (LLM이 프롬프트 무시하고 생성하는 경우 방어)
    tasks_raw = [
        t for t in tasks_raw
        if not (t.get("type") == "verify" and not t.get("target", "").endswith(".py"))
    ]

    # [v3-5] TDD 강제: verify 누락 시 자동 삽입 (.py만 해당)
    tasks_raw = _ensure_tdd_order(tasks_raw)

    tasks = [_new_task(
        desc=t.get("desc", ""),
        task_type=t.get("type", "modify"),
        target=t.get("target", ""),
        issue=t.get("issue", ""),
        depends_on=t.get("depends_on", []),
    ) for t in tasks_raw]

    # 순차 depends_on 체인 연결 — verify 실패 시 다음 modify 차단 보장
    # (LLM은 depends_on을 빈 배열로 반환하므로 여기서 직접 연결)
    for i in range(1, len(tasks)):
        if not tasks[i]["depends_on"]:
            tasks[i]["depends_on"] = [tasks[i - 1]["id"]]

    plan = _new_plan(goal, tasks)

    # [v3-6] 모든 계획 → 사용자 확인 대기 (코어 파일 여부 무관)
    plan["status"] = "waiting_approval"
    is_core = _has_core_file(tasks)

    data = _load_queue()
    data["plans"].append(plan)
    _save_queue(data)

    # 터미널 출력 — 계획 상세 내용 표시
    summary_lines = []
    for i, t in enumerate(tasks):
        icon = {"modify": "✏️", "create": "🆕", "verify": "🧪"}.get(t["type"], "•")
        summary_lines.append(f"  {i+1}. {icon} [{t['type']}] {t['target']} — {t['desc']}")
    summary = "\n".join(summary_lines)

    core_warn = ""
    if is_core:
        core_targets = [t["target"] for t in tasks if t.get("target") in CORE_FILES]
        core_warn = f"\n⚠️  코어 파일 포함: {', '.join(core_targets)}"

    plan_preview = (
        f"\n{'='*50}\n"
        f"📋 [코드플래너] 계획 생성 완료 — 실행 전 확인 필요\n"
        f"목표: {goal}{core_warn}\n"
        f"태스크 {len(tasks)}개:\n{summary}\n"
        f"{'='*50}\n"
        f"👉 실행하려면 '승인' 입력 / 취소하려면 '거부' 입력\n"
    )
    try:
        print(plan_preview)
    except UnicodeEncodeError:
        # Windows cp949 터미널 대응 — 이모지 제거 후 출력
        safe = plan_preview.encode('cp949', errors='replace').decode('cp949')
        print(safe)
    _notify(f"📋 [코드플래너] 계획 생성 — 승인 대기\n목표: {goal}\n{summary[:400]}")

    return plan


# ==============================================================================
# [태스크 실행]
# ==============================================================================
def _resolve_target(target: str) -> str:
    """target에서 SYSTEM/ 접두어 제거 후 절대경로 반환."""
    t = target.replace("\\", "/")
    for prefix in ("SYSTEM/", "system/"):
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    return os.path.join(SYSTEM_DIR, t)


def _can_run(task, all_tasks):
    """의존 태스크가 모두 done인지 확인."""
    if not task["depends_on"]:
        return True
    done_ids = {t["id"] for t in all_tasks if t["status"] == "done"}
    return all(dep in done_ids for dep in task["depends_on"])


def _run_modify(task, engine, context=""):
    """기존 파일 수정 — apply_fix() 위임."""
    target = _resolve_target(task["target"])
    if not os.path.exists(target):
        return False, f"파일 없음: {task['target']}"
    issue = task["issue"]
    if context:
        issue = f"{issue}\n\n[선행 태스크 컨텍스트]\n{context}"
    result = engine.apply_fix(target, issue)
    return "✅" in result, result[:300]


def _run_create(task, client, context=""):
    """새 파일 생성 — Gemini가 전체 코드 생성."""
    target_path = _resolve_target(task["target"])
    if os.path.exists(target_path):
        return False, f"⚠️ 파일이 이미 존재합니다: {task['target']}\n→ 새로 만들기(create)가 아닌 수정(modify)으로 계획을 다시 세워주세요."

    ctx_section = f"\n\n선행 태스크 결과 (참고):\n{context}" if context else ""
    prompt = f"""온유 시스템용 Python 모듈을 작성하세요.

파일명: {task['target']}
요구사항: {task['issue']}{ctx_section}

=== 시스템 파일 구조 참고 ===
{_load_interface_summary(max_chars=2000)}

{DESIGN_PRINCIPLES}

규칙:
- 완전하고 실행 가능한 Python 코드만 반환 (``` 없이)
- 한국어 주석, 파일 상단 docstring 필수
- 위 시스템 구조 및 설계 원칙과 일관성 있게 작성"""

    try:
        from google.genai import types as _t
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=_t.GenerateContentConfig(temperature=0.3),
        )
        code = resp.text.strip()
        if "```" in code:
            code = code.split("```")[1]
            if code.startswith("python"):
                code = code[6:]
            code = code.rsplit("```", 1)[0].strip()
    except Exception as e:
        return False, f"코드 생성 실패: {e}"

    # .py 파일만 문법 검사 — .md/.json 등은 완전 건너뜀
    target_name = os.path.basename(task.get("target", ""))
    if target_name.endswith(".py"):
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"문법 오류: {e}"

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    tmp = target_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(code)
    os.replace(tmp, target_path)
    return True, f"생성 완료: {task['target']} ({len(code)}자)"


def _run_verify(task):
    """pytest 실행. 비-Python 파일 대상이면 즉시 성공 반환."""
    target = task.get("target", "")

    # .py 파일이 아닌 verify는 의미 없음 → 성공으로 처리
    if target and not os.path.basename(target).endswith(".py"):
        return True, f"비-Python 파일 verify 건너뜀 (대상: {target})"

    if target:
        path = _resolve_target(target)
        if not os.path.exists(path):
            return False, f"테스트 파일 없음: {target}"
        cmd = [sys.executable, "-m", "pytest", path, "-q", "--tb=short"]
    else:
        cmd = [sys.executable, "-m", "pytest", SYSTEM_DIR, "-q", "--tb=short"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=120, cwd=SYSTEM_DIR)
        out = (r.stdout + r.stderr).strip()[-400:]
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, "타임아웃 (120s)"


# ==============================================================================
# [메인 실행 루프]
# ==============================================================================
def execute_next(engine=None, client=None):
    """대기 계획에서 실행 가능한 태스크 1개 실행. 워처 루프에서 호출."""
    data  = _load_queue()
    plans = data.get("plans", [])

    for plan in plans:
        # [v3-6] 승인 대기 중인 플랜은 건너뜀
        if plan["status"] == "waiting_approval":
            continue
        if plan["status"] not in ("pending", "running"):
            continue

        if plan["status"] == "pending":
            _take_snapshot(plan)

        plan["status"] = "running"
        tasks = plan["tasks"]

        # 실패 전파 — pending이지만 선행이 failed인 태스크 처리
        for t in tasks:
            if t["status"] == "pending":
                failed_deps = [
                    dep for dep in t["depends_on"]
                    if any(x["id"] == dep and x["status"] == "failed" for x in tasks)
                ]
                if failed_deps:
                    _propagate_failure(failed_deps[0], tasks)
                    break

        task = next(
            (t for t in tasks if t["status"] == "pending" and _can_run(t, tasks)),
            None,
        )

        if task is None:
            if all(t["status"] in ("done", "failed", "skipped") for t in tasks):
                done    = sum(1 for t in tasks if t["status"] == "done")
                failed  = sum(1 for t in tasks if t["status"] == "failed")
                skipped = sum(1 for t in tasks if t["status"] == "skipped")

                if failed > 0:
                    plan["status"]     = "aborted"
                    plan["updated_at"] = datetime.now().isoformat()

                    # [v3-7] 오답 노트 기록
                    failed_task = next(t for t in tasks if t["status"] == "failed")
                    _log_failure(plan, failed_task)

                    rolled      = _rollback_plan(plan)
                    done_files  = [t["target"] for t in tasks if t["status"] == "done" and t["type"] in ("create", "modify")]
                    _save_planner_context(plan, done_files, "aborted")
                    _save_queue(data)
                    _notify(
                        f"🔴 [코드플래너] 플랜 중단 + 롤백\n"
                        f"목표: {plan['goal']}\n"
                        f"성공 {done} / 실패 {failed} / 건너뜀 {skipped}\n"
                        f"롤백: {', '.join(rolled[:5])}"
                    )
                else:
                    plan["status"]     = "done"
                    plan["updated_at"] = datetime.now().isoformat()
                    _save_queue(data)
                    # 생성/수정된 파일 목록
                    touched   = [t["target"] for t in tasks if t["status"] == "done" and t["type"] in ("create", "modify")]
                    file_list = "\n".join(f"  • {f}" for f in touched) if touched else "  (없음)"
                    _save_planner_context(plan, touched, "done")
                    _notify(
                        f"✅ [코드플래너] 계획 완료\n"
                        f"목표: {plan['goal']}\n"
                        f"성공 {done}개\n\n"
                        f"생성/수정 파일:\n{file_list}"
                    )
            continue

        context      = _build_context(task, tasks)
        task["status"] = "running"
        _save_queue(data)
        _notify(f"⚙️ [코드플래너] [{task['type']}] {task['desc']}")

        try:
            if task["type"] == "modify" and engine:
                ok, result = _run_modify(task, engine, context)
            elif task["type"] == "create" and client:
                ok, result = _run_create(task, client, context)
            elif task["type"] == "verify":
                ok, result = _run_verify(task)
            else:
                ok, result = False, "실행 불가 (engine/client 미주입)"
        except Exception as e:
            ok, result = False, f"예외: {e}"

        task["status"] = "done" if ok else "failed"
        task["result"] = result[:300]
        plan["updated_at"] = datetime.now().isoformat()

        # 수정 성공 시 diff 저장
        if ok and task["type"] == "modify":
            old = plan.get("snapshot", {}).get(task["target"], "")
            if old:
                _save_code_change(task["target"], old, plan["goal"])

        _save_queue(data)

        if not ok:
            skipped_ids = _propagate_failure(task["id"], tasks)
            _save_queue(data)
            _notify(
                f"❌ [코드플래너] 태스크 실패 → {len(skipped_ids)-1}개 건너뜀\n"
                f"{task['desc']}\n{result[:200]}"
            )
        else:
            _notify(f"✅ {task['desc']}\n{result[:200]}")

        return True

    return False


# ==============================================================================
# [외부 진입점]
# ==============================================================================
def receive_direction(goal, client=None):
    """텔레그램 '계획: [목표]' 명령 처리."""
    goal = goal.strip()
    if len(goal) < 10:
        return "목표가 너무 짧습니다. 구체적으로 설명해 주세요."
    plan = create_plan(goal, client=client)
    if plan is None:
        return "계획 생성 실패"
    if plan["status"] == "waiting_approval":
        return f"⚠️ 코어 파일 수정 계획 ({len(plan['tasks'])}개 태스크) — 승인 후 실행"
    return f"📋 계획 생성 완료 ({len(plan['tasks'])}개 태스크) — 순차 실행 시작"


def get_log(max_plans=3):
    """최근 플랜의 실패 상세 로그 반환 (텔레그램 '플래너로그' 명령용)."""
    data  = _load_queue()
    plans = data.get("plans", [])
    if not plans:
        return "플랜 기록 없음"

    # 최근 플랜 중 실패/중단된 것 우선, 없으면 전체
    targets = [p for p in plans if p["status"] in ("aborted", "failed")][-max_plans:]
    if not targets:
        targets = plans[-max_plans:]

    lines = []
    for p in targets:
        lines.append(f"[{p['status']}] {p['goal'][:50]}")
        for t in p["tasks"]:
            if t["status"] in ("failed", "skipped"):
                icon = "❌" if t["status"] == "failed" else "⏭"
                lines.append(f"  {icon} [{t['type']}] {t['desc'][:40]}")
                if t["result"]:
                    lines.append(f"     → {t['result'][:120]}")
        lines.append("")

    # reasoning_log에서 추가 원인 정보
    if os.path.exists(REASONING_LOG):
        try:
            with open(REASONING_LOG, encoding="utf-8") as f:
                log = json.load(f)
            if log:
                last = log[-1]
                lines.append(f"[마지막 오답 기록]")
                lines.append(f"목표: {last['goal'][:50]}")
                lines.append(f"실패: {last['failed_task_desc'][:50]}")
                lines.append(f"원인: {last['error'][:200]}")
        except Exception:
            pass

    return "\n".join(lines).strip() or "실패 기록 없음"


def get_change_log(max_entries=5):
    """최근 코드 변경 이력 목록 반환."""
    if not os.path.exists(CHANGE_LOG_DIR):
        return "변경 이력 없음 (아직 코드 수정이 실행되지 않았습니다)"
    files = sorted(Path(CHANGE_LOG_DIR).glob("*.md"), reverse=True)[:max_entries]
    if not files:
        return "변경 이력 없음"
    lines = ["[최근 코드 변경 이력]"]
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            # YAML에서 파일/목표/변경 줄 추출
            file_line = next((l for l in content.splitlines() if l.startswith("파일:")), "")
            goal_line = next((l for l in content.splitlines() if l.startswith("목표:")), "")
            change_line = next((l for l in content.splitlines() if l.startswith("**변경:**")), "")
            lines.append(f"\n{f.stem}")
            if file_line: lines.append(f"  {file_line}")
            if goal_line: lines.append(f"  {goal_line}")
            if change_line: lines.append(f"  {change_line.replace('**변경:**','변경:')}")
        except Exception:
            lines.append(f"\n{f.name}")
    return "\n".join(lines)


def get_status():
    """현재 계획 상태 요약."""
    data  = _load_queue()
    plans = data.get("plans", [])
    if not plans:
        return "진행 중인 계획 없음"
    lines = []
    for p in plans[-5:]:
        done    = sum(1 for t in p["tasks"] if t["status"] == "done")
        failed  = sum(1 for t in p["tasks"] if t["status"] == "failed")
        skipped = sum(1 for t in p["tasks"] if t["status"] == "skipped")
        total   = len(p["tasks"])
        status_icon = "⏳" if p["status"] == "waiting_approval" else ""
        lines.append(
            f"{status_icon}[{p['status']}] {p['goal'][:35]} "
            f"✅{done}/❌{failed}/⏭{skipped}/{total}"
        )
    return "\n".join(lines)
