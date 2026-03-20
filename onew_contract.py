"""
onew_contract.py — 인터페이스 계약 자동 생성 + 검증

[역할]
1. generate(): SYSTEM/*.py 파일의 모든 함수/메서드 서명을 추출 → interface_contract.json 저장
2. verify(filepath): 수정 후 서명이 계약과 다른지 확인 → 위반 목록 반환
3. summarize(): 파일별 1줄 요약 → 자율코딩 엔진의 타겟 파일 선택에 활용

[onew_self_improve.py 연동]
- apply_fix() 성공 후 verify(filepath) 호출
- 위반 발견 시 rollback 처리
"""

import ast
import json
import os
import re
from datetime import datetime
from pathlib import Path

SYSTEM_DIR       = os.path.dirname(os.path.abspath(__file__))
CONTRACT_FILE    = os.path.join(SYSTEM_DIR, "interface_contract.json")
SUMMARY_FILE     = os.path.join(SYSTEM_DIR, "interface_summary.json")
CRITICAL_FILE    = os.path.join(SYSTEM_DIR, "critical_functions.json")

# 스캔 대상 파일 (자율코딩 허용 파일과 동기화)
SCAN_FILES = [
    "obsidian_agent.py",
    "onew_self_improve.py",
    "onew_contract.py",
]


# ==============================================================================
# [서명 추출]
# ==============================================================================
def _extract_signatures(filepath: str) -> list[dict]:
    """AST로 함수/메서드 서명 추출."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree   = ast.parse(source)
    except Exception as e:
        return [{"error": str(e)}]

    results  = []
    filename = os.path.basename(filepath)

    def _type_str(annotation) -> str:
        if annotation is None:
            return "unknown"
        try:
            return ast.unparse(annotation)
        except Exception:
            return "unknown"

    def _has_side_effect(func_node) -> list[str]:
        """단순 휴리스틱으로 부작용 탐지."""
        effects = []
        src = ast.unparse(func_node)
        if "open(" in src and ("'w'" in src or '"w"' in src or "'a'" in src or '"a"' in src):
            effects.append("file_write")
        if "json.dump" in src or "_atomic_json_write" in src:
            effects.append("json_write")
        if re.search(r'\bglobal\b', src):
            effects.append("global_state")
        if "subprocess" in src:
            effects.append("subprocess")
        if "requests" in src or "urllib" in src or "genai" in src:
            effects.append("network")
        return effects

    current_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            current_class = node.name
            # 클래스 메서드 추출
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = []
                    for a in item.args.args:
                        if a.arg == "self":
                            continue
                        args.append({
                            "name": a.arg,
                            "type": _type_str(a.annotation),
                        })
                    results.append({
                        "file":        filename,
                        "class":       current_class,
                        "name":        item.name,
                        "args":        args,
                        "returns":     _type_str(item.returns),
                        "is_async":    isinstance(item, ast.AsyncFunctionDef),
                        "side_effects": _has_side_effect(item),
                        "has_kwargs":  item.args.kwarg is not None,
                        "has_varargs": item.args.vararg is not None,
                    })

    # 모듈 레벨 함수
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for a in node.args.args:
                args.append({
                    "name": a.arg,
                    "type": _type_str(a.annotation),
                })
            results.append({
                "file":        filename,
                "class":       None,
                "name":        node.name,
                "args":        args,
                "returns":     _type_str(node.returns),
                "is_async":    isinstance(node, ast.AsyncFunctionDef),
                "side_effects": _has_side_effect(node),
                "has_kwargs":  node.args.kwarg is not None,
                "has_varargs": node.args.vararg is not None,
            })

    return results


# ==============================================================================
# [파일별 1줄 요약]
# ==============================================================================
def _summarize_file(filepath: str) -> str:
    """파일의 class/def 목록으로 1줄 요약 생성."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree   = ast.parse(source)
    except Exception:
        return "파싱 실패"

    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    funcs   = [n.name for n in ast.iter_child_nodes(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    lines   = Path(filepath).read_text(encoding="utf-8").count("\n")

    parts = []
    if classes:
        parts.append(f"클래스: {', '.join(classes[:5])}")
    if funcs:
        parts.append(f"함수 {len(funcs)}개")
    parts.append(f"{lines}줄")
    return " | ".join(parts)


# ==============================================================================
# [생성]
# ==============================================================================
def generate() -> str:
    """
    SCAN_FILES 의 서명을 추출해 interface_contract.json 저장.
    interface_summary.json (파일별 1줄 요약) 도 함께 저장.

    계약 오염 방지: 문법 오류 파일이 있으면 해당 파일은 계약 갱신 거부.
    """
    import subprocess as _sp, sys as _sys

    contract = {}
    summary  = {}
    skipped  = []

    for fname in SCAN_FILES:
        fpath = os.path.join(SYSTEM_DIR, fname)
        if not os.path.exists(fpath):
            continue

        # 계약 오염 방지: 문법 오류 파일은 기존 계약 유지
        if fname.endswith(".py"):
            r = _sp.run([_sys.executable, "-m", "py_compile", fpath],
                        capture_output=True, timeout=10)
            if r.returncode != 0:
                skipped.append(fname)
                continue  # 기존 계약 덮어쓰지 않음

        sigs = _extract_signatures(fpath)
        contract[fname] = {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "functions": sigs,
        }
        summary[fname] = _summarize_file(fpath)

    # 기존 계약에서 스킵된 파일 항목 보존
    if os.path.exists(CONTRACT_FILE):
        with open(CONTRACT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        for fname in skipped:
            if fname in existing:
                contract[fname] = existing[fname]  # 기존 계약 유지

    with open(CONTRACT_FILE, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    total = sum(len(v["functions"]) for v in contract.values())
    msg = f"계약 생성 완료\n파일 {len(contract)}개 | 함수/메서드 {total}개"
    if skipped:
        msg += f"\n문법 오류로 갱신 거부 (기존 계약 유지): {', '.join(skipped)}"
    return msg


# ==============================================================================
# [검증]
# ==============================================================================
def verify(filepath: str) -> list[str]:
    """
    수정된 filepath의 현재 서명을 계약과 비교.
    위반 목록 반환 (빈 리스트 = 계약 준수).

    검증 2단계:
    1. critical_functions.json — strict 모드 (인자 추가도 FAIL)
    2. interface_contract.json — 일반 모드 (삭제만 FAIL, 추가는 허용)
    """
    fname = os.path.basename(filepath)
    if not os.path.exists(CONTRACT_FILE):
        return []

    with open(CONTRACT_FILE, "r", encoding="utf-8") as f:
        contract = json.load(f)
    if fname not in contract:
        return []

    # critical_functions.json 로드 (없으면 빈 dict)
    critical = {}
    if os.path.exists(CRITICAL_FILE):
        with open(CRITICAL_FILE, "r", encoding="utf-8") as f:
            critical = json.load(f)

    saved_sigs = {
        (s.get("class"), s["name"]): s
        for s in contract[fname]["functions"]
        if "name" in s
    }
    current_sigs = {
        (s.get("class"), s["name"]): s
        for s in _extract_signatures(filepath)
        if "name" in s
    }

    violations = []

    for key in saved_sigs:
        cls, name = key
        label     = f"{cls}.{name}" if cls else name
        is_critical = name in critical and critical[name].get("strict", False)

        # 1. 삭제 — critical/일반 모두 FAIL
        if key not in current_sigs:
            violations.append(f"❌ 함수 삭제됨: {label}")
            continue

        saved   = saved_sigs[key]
        current = current_sigs[key]

        saved_args   = [a["name"] for a in saved.get("args", [])]
        current_args = [a["name"] for a in current.get("args", [])]

        if is_critical:
            # strict: 인자 추가도 FAIL
            if saved_args != current_args:
                violations.append(
                    f"❌ [critical] 인자 변경: {label}\n"
                    f"   계약: {saved_args} → 현재: {current_args}"
                )
        else:
            # 일반: 인자 제거만 FAIL (추가는 허용)
            removed = [a for a in saved_args if a not in current_args]
            if removed:
                violations.append(
                    f"⚠️ 인자 제거됨: {label}  제거: {removed}"
                )

        # 반환 타입: unknown→구체 허용, 구체→다른구체 경고
        s_ret = saved.get("returns", "unknown")
        c_ret = current.get("returns", "unknown")
        if s_ret != "unknown" and c_ret != "unknown" and s_ret != c_ret:
            prefix = "❌ [critical]" if is_critical else "⚠️"
            violations.append(f"{prefix} 반환 타입 변경: {label}  {s_ret} → {c_ret}")

    return violations


# ==============================================================================
# [요약 조회 — 자율코딩 타겟 선택용]
# ==============================================================================
def get_project_summary() -> str:
    """
    파일별 1줄 요약 반환.
    onew_self_improve.py _generate_fix() 프롬프트에 주입해
    AI가 타겟 파일을 스스로 결정하게 함.
    """
    if not os.path.exists(SUMMARY_FILE):
        return "요약 없음 — generate() 먼저 실행"
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        summary = json.load(f)
    lines = ["[프로젝트 파일 구조]"]
    for fname, desc in summary.items():
        lines.append(f"  {fname}: {desc}")
    return "\n".join(lines)


# ==============================================================================
# [실행]
# ==============================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(generate())
    print()
    print(get_project_summary())
