"""
Vault 데이터 분석 및 트렌드 예측 (vault_analyzer.py)
스킬: data_analysis.md

분석 항목:
  1. 키워드 빈도 트렌드 (DAILY 노트 기반)
  2. OCU 취약 파트 탐지
  3. 작업일지 활동 패턴
  4. 전체 인사이트 리포트

사용:
  python auto_scripts/vault_analyzer.py
  python auto_scripts/vault_analyzer.py --days 14
  python auto_scripts/vault_analyzer.py --keyword 피로 --days 30
"""
import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

VAULT_DIR = Path(__file__).parent.parent.parent


# ── 1. 키워드 트렌드 분석 (DAILY 노트) ────────────────────────────────────────

def analyze_keyword_trend(keyword: str, days: int = 30) -> dict:
    daily_dir = VAULT_DIR / "DAILY"
    if not daily_dir.exists():
        return {"error": "DAILY 폴더 없음"}

    cutoff = datetime.now() - timedelta(days=days)
    trend = {}

    for f in sorted(daily_dir.glob("*.md")):
        try:
            date = datetime.strptime(f.stem, "%Y-%m-%d")
        except ValueError:
            continue
        if date < cutoff:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore").lower()
        count = text.count(keyword.lower())
        if count:
            trend[f.stem] = count

    total = sum(trend.values())
    avg   = round(total / days, 2) if trend else 0
    peak  = max(trend.items(), key=lambda x: x[1]) if trend else None

    return {
        "keyword":    keyword,
        "days":       days,
        "days_found": len(trend),
        "total":      total,
        "avg_per_day": avg,
        "peak":       peak,
        "trend":      trend,
    }


# ── 2. OCU 취약 파트 탐지 ────────────────────────────────────────────────────

WEAKNESS_KEYWORDS = ["오답", "틀", "모름", "헷갈", "다시", "이해안됨", "??", "복습"]

def find_weak_topics(top_n: int = 5) -> list[tuple[str, int]]:
    ocu_dir = VAULT_DIR / "OCU"
    if not ocu_dir.exists():
        return []

    scores = {}
    for f in sorted(ocu_dir.rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        score = sum(text.count(kw) for kw in WEAKNESS_KEYWORDS)
        if score:
            scores[f.stem] = score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]


# ── 3. 작업일지 활동 패턴 ────────────────────────────────────────────────────

def analyze_work_journal(days: int = 30) -> dict:
    journal_dir = VAULT_DIR / "작업일지"
    if not journal_dir.exists():
        return {"error": "작업일지 폴더 없음"}

    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    all_words: Counter = Counter()

    for f in sorted(journal_dir.glob("*.md")):
        # 파일명에서 날짜 추출 (YYYY-MM-DD_제목.md)
        match = re.match(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not match:
            continue
        try:
            date = datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            continue
        if date < cutoff:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        entries.append({"date": match.group(1), "file": f.name, "chars": len(text)})
        # 단어 빈도 (한글 2글자 이상)
        words = re.findall(r"[가-힣]{2,}", text)
        all_words.update(words)

    return {
        "entry_count":   len(entries),
        "days_analyzed": days,
        "recent_entries": entries[-5:],
        "top_keywords":  all_words.most_common(10),
    }


# ── 4. Vault 전체 성장 분석 ───────────────────────────────────────────────────

def analyze_vault_growth() -> dict:
    subdirs = {}
    for d in VAULT_DIR.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            md_files = list(d.rglob("*.md"))
            if md_files:
                total_kb = sum(f.stat().st_size for f in md_files) / 1024
                subdirs[d.name] = {
                    "files": len(md_files),
                    "size_kb": round(total_kb, 1),
                }
    return dict(sorted(subdirs.items(), key=lambda x: x[1]["size_kb"], reverse=True))


# ── 리포트 생성 ───────────────────────────────────────────────────────────────

def build_report(days: int, keywords: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"[VAULT ANALYSIS REPORT] {now} (최근 {days}일)", ""]

    # 키워드 트렌드
    if keywords:
        lines.append("=== 키워드 트렌드 ===")
        for kw in keywords:
            r = analyze_keyword_trend(kw, days)
            if "error" in r:
                lines.append(f"  {kw}: {r['error']}")
            elif r["total"] == 0:
                lines.append(f"  '{kw}': 기간 내 등장 없음")
            else:
                peak_str = f"{r['peak'][0]} ({r['peak'][1]}회)" if r["peak"] else "없음"
                lines.append(f"  '{kw}': 총 {r['total']}회 / 평균 {r['avg_per_day']}회/일 / 피크: {peak_str}")
        lines.append("")

    # OCU 취약 파트
    lines.append("=== OCU 취약 파트 TOP5 ===")
    weak = find_weak_topics()
    if weak:
        for i, (topic, score) in enumerate(weak, 1):
            lines.append(f"  {i}. {topic} (취약 지표: {score})")
    else:
        lines.append("  OCU 폴더 없거나 취약 키워드 미발견")
    lines.append("")

    # 작업 패턴
    lines.append("=== 작업일지 패턴 ===")
    wr = analyze_work_journal(days)
    if "error" in wr:
        lines.append(f"  {wr['error']}")
    else:
        lines.append(f"  {days}일간 작업일지: {wr['entry_count']}건")
        if wr["top_keywords"]:
            kws = ", ".join(f"{w}({c})" for w, c in wr["top_keywords"][:5])
            lines.append(f"  주요 키워드: {kws}")
        if wr["recent_entries"]:
            lines.append(f"  최근 작업: {wr['recent_entries'][-1]['file']}")
    lines.append("")

    # Vault 성장
    lines.append("=== Vault 폴더별 크기 ===")
    growth = analyze_vault_growth()
    for folder, info in list(growth.items())[:5]:
        lines.append(f"  {folder}: {info['files']}개 파일 ({info['size_kb']:.0f}KB)")

    # 권장 액션
    lines.append("")
    lines.append("=== 권장 액션 ===")
    weak_top = find_weak_topics(top_n=1)
    if weak_top:
        lines.append(f"  -> '{weak_top[0][0]}' 집중 복습 (취약 지표 최고)")

    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vault 데이터 분석")
    parser.add_argument("--days",    type=int, default=30, help="분석 기간 (기본 30일)")
    parser.add_argument("--keyword", type=str, action="append", default=[], help="키워드 트렌드 분석 (반복 사용 가능)")
    args = parser.parse_args()

    # 기본 키워드
    keywords = args.keyword or ["피로", "완료", "오답"]
    print(build_report(args.days, keywords))


if __name__ == "__main__":
    main()
