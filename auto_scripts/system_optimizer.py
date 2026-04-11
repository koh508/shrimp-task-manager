"""
온유 시스템 자가 최적화 스크립트 (system_optimizer.py)
스킬: system_optimizer.md

분석 항목:
  1. 스킬 파일 크기 / 분리 필요성
  2. experimental/ 누적 파일
  3. 로그 파일 크기
  4. Vault 기본 통계
  5. 최적화 제안 생성

사용:
  python auto_scripts/system_optimizer.py
  python auto_scripts/system_optimizer.py --json   # JSON 출력
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

SYSTEM_DIR = Path(__file__).parent.parent
VAULT_DIR  = SYSTEM_DIR.parent
SKILLS_DIR = SYSTEM_DIR / "skills"
LOGS_DIR   = SYSTEM_DIR / "logs"

# ── 임계치 상수 ───────────────────────────────────────────────────────────────
SKILL_SIZE_WARN_KB     = 5      # 스킬 파일 크기 경고
EXPERIMENTAL_WARN_COUNT = 5     # experimental 누적 경고
LOG_SIZE_WARN_MB       = 3      # 로그 파일 크기 경고
DISK_WARN_GB           = 10     # 디스크 잔여 경고


# ── 분석 함수 ─────────────────────────────────────────────────────────────────

def analyze_skills() -> dict:
    results = {"optional": [], "experimental": [], "large_files": [], "suggestions": []}

    for subdir in ["optional", "experimental"]:
        d = SKILLS_DIR / subdir
        if not d.exists():
            continue
        files = [f for f in d.iterdir() if f.suffix == ".md" and not f.name.startswith(".")]
        results[subdir] = [
            {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
            for f in sorted(files)
        ]
        for f in files:
            kb = f.stat().st_size / 1024
            if kb > SKILL_SIZE_WARN_KB:
                results["large_files"].append(f.name)
                results["suggestions"].append(
                    f"'{f.name}' 크기({kb:.1f}KB)가 {SKILL_SIZE_WARN_KB}KB 초과 - 섹션 분리 권장"
                )

    exp_count = len(results["experimental"])
    if exp_count >= EXPERIMENTAL_WARN_COUNT:
        results["suggestions"].append(
            f"experimental/ 에 {exp_count}개 파일 누적 - 검토 후 optional/으로 승격 또는 삭제 권장"
        )

    return results


def analyze_logs() -> dict:
    results = {"files": [], "suggestions": []}
    if not LOGS_DIR.exists():
        return results

    for f in LOGS_DIR.iterdir():
        if f.is_file():
            mb = f.stat().st_size / (1024 * 1024)
            results["files"].append({"name": f.name, "size_mb": round(mb, 2)})
            if mb > LOG_SIZE_WARN_MB:
                results["suggestions"].append(
                    f"'{f.name}' 로그({mb:.1f}MB) {LOG_SIZE_WARN_MB}MB 초과 - 로테이션 권장"
                )
    return results


def analyze_disk() -> dict:
    import shutil
    usage = shutil.disk_usage(VAULT_DIR)
    free_gb  = usage.free  / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    used_pct = (usage.used / usage.total) * 100
    suggestions = []
    if free_gb < DISK_WARN_GB:
        suggestions.append(f"C: 드라이브 잔여량 {free_gb:.1f}GB — 정리 권장 (사용률 {used_pct:.0f}%)")
    return {
        "free_gb":  round(free_gb, 1),
        "total_gb": round(total_gb, 1),
        "used_pct": round(used_pct, 1),
        "suggestions": suggestions,
    }


def analyze_vault() -> dict:
    md_files = list(VAULT_DIR.rglob("*.md"))
    total_kb = sum(f.stat().st_size for f in md_files) / 1024
    daily_dir = VAULT_DIR / "DAILY"
    daily_count = len(list(daily_dir.glob("*.md"))) if daily_dir.exists() else 0
    return {
        "total_md_files": len(md_files),
        "total_size_kb":  round(total_kb, 1),
        "daily_notes":    daily_count,
    }


# ── 리포트 생성 ───────────────────────────────────────────────────────────────

def build_report(skill_r: dict, log_r: dict, disk_r: dict, vault_r: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"[SYSTEM REPORT] {now}",
        "",
        "=== 스킬 현황 ===",
        f"  optional  : {len(skill_r['optional'])}개",
        f"  experimental: {len(skill_r['experimental'])}개",
    ]
    if skill_r["large_files"]:
        lines.append(f"  대용량 파일: {', '.join(skill_r['large_files'])}")

    lines += ["", "=== 디스크 ===",
              f"  잔여: {disk_r['free_gb']}GB / {disk_r['total_gb']}GB (사용률 {disk_r['used_pct']}%)"]

    lines += ["", "=== Vault ===",
              f"  .md 파일: {vault_r['total_md_files']}개 ({vault_r['total_size_kb']:.0f}KB)",
              f"  일일 노트: {vault_r['daily_notes']}개"]

    if log_r["files"]:
        lines += ["", "=== 로그 ==="]
        for lf in log_r["files"]:
            lines.append(f"  {lf['name']}: {lf['size_mb']}MB")

    # 제안 통합
    all_suggestions = (
        skill_r["suggestions"] + log_r["suggestions"] + disk_r["suggestions"]
    )
    if all_suggestions:
        lines += ["", "=== 최적화 제안 ==="]
        for i, s in enumerate(all_suggestions, 1):
            lines.append(f"  {i}. {s}")
    else:
        lines += ["", "=== 최적화 제안 ===", "  현재 최적화 필요 항목 없음."]

    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = parser.parse_args()

    skill_r = analyze_skills()
    log_r   = analyze_logs()
    disk_r  = analyze_disk()
    vault_r = analyze_vault()

    if args.json:
        result = {
            "timestamp": datetime.now().isoformat(),
            "skills":    skill_r,
            "logs":      log_r,
            "disk":      disk_r,
            "vault":     vault_r,
            "suggestions": (
                skill_r["suggestions"] + log_r["suggestions"] + disk_r["suggestions"]
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(build_report(skill_r, log_r, disk_r, vault_r))


if __name__ == "__main__":
    main()
