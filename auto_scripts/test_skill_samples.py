"""
스킬 샘플 마스터 테스트 러너
skill_samples/ 폴더의 sample_*.py 를 하나씩 실행하고 결과를 보고합니다.
"""
import os
import sys
import subprocess

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "skill_samples")
SKILL_NAMES = [
    "python_async",
    "python_typing",
    "python_testing (pytest)",
    "python_db",
    "dev_code_review",
    "dev_git_workflow",
    "dev_docker",
    "dev_clean_code",
    "security_best_practices",
    "ai_prompt_engineering",
    "productivity_planning",
]

def run_sample(fpath: str, is_pytest: bool = False) -> tuple[bool, str]:
    if is_pytest:
        cmd = [sys.executable, "-m", "pytest", fpath, "-v", "--tb=short", "-q"]
    else:
        cmd = [sys.executable, fpath]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=30)
        ok = res.returncode == 0
        out = (res.stdout + res.stderr).decode("cp949", errors="replace").strip()
        return ok, out
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (30s)"
    except Exception as e:
        return False, f"실행 오류: {e}"

if __name__ == "__main__":
    samples = sorted(f for f in os.listdir(SAMPLES_DIR) if f.startswith("sample_") and f.endswith(".py"))
    print(f"{'='*70}")
    print(f"  스킬 샘플 테스트 - {len(samples)}개")
    print(f"{'='*70}\n")

    passed = 0
    for i, (fname, skill_name) in enumerate(zip(samples, SKILL_NAMES), 1):
        fpath = os.path.join(SAMPLES_DIR, fname)
        is_pytest = "testing" in fname
        ok, output = run_sample(fpath, is_pytest=is_pytest)

        status = "PASS" if ok else "FAIL"
        print(f"[{i:02d}] {skill_name:<30} → {status}")

        # 세부 출력 (들여쓰기)
        for line in output.splitlines():
            if line.strip():
                print(f"      {line}")

        if ok:
            passed += 1
        print()

    print(f"{'='*70}")
    print(f"결과: {passed}/{len(samples)} 통과")
    print(f"{'='*70}")
    sys.exit(0 if passed == len(samples) else 1)
