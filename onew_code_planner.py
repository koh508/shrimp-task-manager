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
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

SYSTEM_DIR        = os.path.dirname(os.path.abspath(__file__))
PLAN_QUEUE        = os.path.join(SYSTEM_DIR, "onew_code_plan_queue.json")
INTERFACE_SUMMARY = os.path.join(SYSTEM_DIR, "interface_summary.json")
REASONING_LOG     = os.path.join(SYSTEM_DIR, "onew_reasoning_log.json")
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
            path = os.path.join(SYSTEM_DIR, task["target"])
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
            path = os.path.join(SYSTEM_DIR, task["target"])
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
    """modify/create 직후 해당 파일의 verify 태스크가 없으면 자동 삽입."""
    result = []
    for i, task in enumerate(tasks_raw):
        result.append(task)
        t_type = task.get("type", "modify")
        target = task.get("target", "")
        if t_type not in ("modify", "create"):
            continue
        base          = os.path.basename(target)
        expected_test = f"test_{base}" if not base.startswith("test_") else base
        # 다음 태스크가 이미 '이 파일'의 verify면 건너뜀 (type + target 둘 다 일치해야 함)
        next_t = tasks_raw[i + 1] if i + 1 < len(tasks_raw) else None
        if (next_t
                and next_t.get("type") == "verify"
                and next_t.get("target") == expected_test):
            continue
        # verify 태스크 삽입
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
    """텔레그램 '승인' 명령 처리 — waiting_approval 플랜을 pending으로 전환."""
    data    = _load_queue()
    waiting = [p for p in data.get("plans", []) if p["status"] == "waiting_approval"]
    if not waiting:
        return "승인 대기 중인 계획 없음"
    target = next((p for p in waiting if p["id"] == plan_id), waiting[-1])
    target["status"]     = "pending"
    target["updated_at"] = datetime.now().isoformat()
    _save_queue(data)
    _notify(f"✅ [코드플래너] 계획 승인됨\n목표: {target['goal'][:50]}")
    return f"계획 승인: {target['goal'][:50]}"


# ==============================================================================
# [v3-7] 오답 노트 — 실패 기록 / 로드
# ==============================================================================
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

    prompt = f"""온유 자율 코딩 시스템입니다.
다음 목표를 달성하기 위한 코딩 태스크 목록을 JSON으로 작성하세요.

목표: {goal}

=== 현재 시스템 파일 구조 (interface_summary) ===
{interface_ctx}
{failure_section}
{DESIGN_PRINCIPLES}

규칙:
1. 태스크 최대 {MAX_TASKS}개, 각각 단일 파일 단위로 원자적 실행 가능
2. type: "modify"(기존 파일 수정) / "create"(새 파일 생성) / "verify"(pytest 실행)
3. [TDD 필수] modify 또는 create 직후에는 반드시 해당 파일을 검증하는 verify 태스크를 배치할 것
   - verify가 없으면 다음 modify/create로 진행할 수 없음
   - 패턴: modify A → verify test_A → modify B → verify test_B
4. modify의 issue: 위 함수 목록을 참고한 구체적 수정 요구사항 (어떤 함수를 어떻게)
5. create의 issue: 파일 목적 + 포함할 핵심 함수/클래스 명세
6. depends_on: 빈 배열 (순서로 의존성 표현)
7. 실행 가능한 순서로 정렬

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

    # [v3-5] TDD 강제: verify 누락 시 자동 삽입
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

    # [v3-6] HITL: 코어 파일 수정 시 승인 대기
    needs_approval = _has_core_file(tasks)
    if needs_approval:
        plan["status"] = "waiting_approval"

    data = _load_queue()
    data["plans"].append(plan)
    _save_queue(data)

    summary = "\n".join(
        f"  {i+1}. [{t['type']}] {t['desc']}" for i, t in enumerate(tasks)
    )

    if needs_approval:
        core_targets = [t["target"] for t in tasks if t.get("target") in CORE_FILES]
        _notify(
            f"⚠️ [코드플래너] 승인 필요\n"
            f"목표: {goal}\n"
            f"코어 파일 수정: {', '.join(core_targets)}\n\n"
            f"{summary}\n\n"
            f"'승인' 또는 '플래너승인'을 입력하면 실행합니다."
        )
    else:
        _notify(f"📋 [코드플래너] 계획 생성\n목표: {goal}\n\n{summary}")

    return plan


# ==============================================================================
# [태스크 실행]
# ==============================================================================
def _can_run(task, all_tasks):
    """의존 태스크가 모두 done인지 확인."""
    if not task["depends_on"]:
        return True
    done_ids = {t["id"] for t in all_tasks if t["status"] == "done"}
    return all(dep in done_ids for dep in task["depends_on"])


def _run_modify(task, engine, context=""):
    """기존 파일 수정 — apply_fix() 위임."""
    target = os.path.join(SYSTEM_DIR, task["target"])
    if not os.path.exists(target):
        return False, f"파일 없음: {task['target']}"
    issue = task["issue"]
    if context:
        issue = f"{issue}\n\n[선행 태스크 컨텍스트]\n{context}"
    result = engine.apply_fix(target, issue)
    return "✅" in result, result[:300]


def _run_create(task, client, context=""):
    """새 파일 생성 — Gemini가 전체 코드 생성."""
    target_path = os.path.join(SYSTEM_DIR, task["target"])
    if os.path.exists(target_path):
        return False, f"이미 존재: {task['target']}"

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

    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"문법 오류: {e}"

    tmp = target_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(code)
    os.replace(tmp, target_path)
    return True, f"생성 완료: {task['target']} ({len(code)}자)"


def _run_verify(task):
    """pytest 실행."""
    target = task.get("target", "")
    if target:
        path = os.path.join(SYSTEM_DIR, target)
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

                    rolled = _rollback_plan(plan)
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
                    _notify(
                        f"✅ [코드플래너] 계획 완료\n"
                        f"목표: {plan['goal']}\n"
                        f"성공 {done}개"
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
