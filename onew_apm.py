"""onew_apm.py — 온유 APM 일일 리포트 (규칙 기반)
사용: python onew_apm.py [--date YYYY-MM-DD]
"""
import json, sys, os
from datetime import date
from collections import defaultdict

# Windows 콘솔 UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUERY_LOG = os.path.join(os.path.dirname(__file__), "memory", "query_log.jsonl")

def load_entries(target_date: str) -> list[dict]:
    if not os.path.exists(QUERY_LOG):
        return []
    entries = []
    with open(QUERY_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                if e.get("date") == target_date:
                    entries.append(e)
            except:
                pass
    return entries

def diagnose(entries: list[dict], target_date: str = "") -> list[str]:
    if not entries:
        return ["데이터 없음"]
    n = len(entries)
    elapsed_list   = [e.get("elapsed", 0)      for e in entries]
    profile_list   = [e.get("profile_len", 0)  for e in entries]
    reused_list    = [e.get("reused", False)    for e in entries]

    avg_elapsed    = sum(elapsed_list) / n
    avg_profile    = sum(profile_list) / n
    slow_count     = sum(1 for x in elapsed_list if x > 5)
    slow_ratio     = slow_count / n
    reused_ratio   = sum(reused_list) / n

    # --- 출력 ---
    icons = {"ok": "✅", "warn": "🟡", "crit": "🔴"}

    def fmt(val, ok_thr, warn_thr, unit="", reverse=False):
        """reverse=True → 값이 클수록 좋음 (reused_ratio)"""
        if reverse:
            level = "ok" if val >= ok_thr else ("warn" if val >= warn_thr else "crit")
        else:
            level = "ok" if val <= ok_thr else ("warn" if val <= warn_thr else "crit")
        return f"{icons[level]} {val:.1f}{unit}"

    lines = [
        f"\n{'='*48}",
        f"[APM DAILY REPORT]  {target_date}",
        f"{'='*48}",
        f"요청 수          : {n}건",
        f"평균 응답시간    : {fmt(avg_elapsed,   5, 10, 's')}",
        f"느린 요청 비율   : {fmt(slow_ratio*100, 20, 30, '%')}",
        f"캐시 재사용률    : {fmt(reused_ratio*100, 50, 30, '%', reverse=True)}",
        f"프로필 평균 크기 : {fmt(avg_profile,   5000, 8000, ' chars')}",
        "",
        "[진단]",
    ]

    issues = []

    # 규칙 1 — LLM 병목
    if slow_ratio > 0.30 and avg_profile < 5000:
        issues.append("🔴 LLM latency 또는 외부 API 문제 (컨텍스트는 가벼운데 느림)")

    # 규칙 2 — 컨텍스트 과부하
    if avg_profile > 6000 and slow_ratio > 0.20:
        issues.append("🔴 프롬프트 다이어트 필요 (profile 크기 + 느린 요청 동시 발생)")
    elif avg_profile > 6000:
        issues.append("🟡 프로필 크기 주의 (아직 latency 영향 없음)")

    # 규칙 3 — 캐시 활용 부족
    if reused_ratio < 0.30:
        issues.append("🔴 메모리 재활용 거의 안 됨 (query_log 매칭 실패)")
    elif reused_ratio < 0.50:
        issues.append("🟡 캐시 재사용률 개선 여지 있음")

    # 규칙 5 — 건강한 상태
    if not issues and reused_ratio >= 0.50 and slow_ratio < 0.20 and avg_profile < 5000:
        issues.append("🟢 시스템 안정적 — 주요 병목 없음")

    lines += issues if issues else ["🟢 특이사항 없음"]
    lines.append("=" * 48)
    return lines

def main():
    target = date.today().isoformat()
    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]

    entries = load_entries(target)
    report  = diagnose(entries, target)
    print("\n".join(report))

if __name__ == "__main__":
    main()
