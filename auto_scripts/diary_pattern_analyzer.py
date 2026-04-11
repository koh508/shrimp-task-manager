"""
diary_pattern_analyzer.py — DAILY/ 일기에서 패턴 추출 → patterns/diary_patterns.md 생성.

[설계 원칙]
- LLM 없음, 100% deterministic Python (Pattern RAG Step 0)
- mtime이 아닌 파일명(YYYY-MM-DD) 기준으로 날짜 판별
- Decision Layer가 pattern_stats를 참조할 때 이 파일이 데이터 원천

[출력]
- SYSTEM/patterns/diary_patterns.md (마크다운 통계 요약)
- SYSTEM/patterns/diary_patterns.json (machine-readable, 선택)
"""
import json
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# 경로 설정
SCRIPT_DIR   = Path(__file__).parent
SYSTEM_DIR   = SCRIPT_DIR.parent
VAULT_DIR    = SYSTEM_DIR.parent
DAILY_DIR    = VAULT_DIR / "DAILY"
PATTERNS_DIR = SYSTEM_DIR / "patterns"

# ── 감정 키워드 ──────────────────────────────────────────────────────────────
MOOD_KEYWORDS: dict[str, list[str]] = {
    "피로/무기력": ["피곤", "무기력", "지쳐", "힘들", "무거워", "기진맥진", "졸려", "쉬고싶", "녹초"],
    "불안/스트레스": ["불안", "스트레스", "걱정", "두려", "무섭", "긴장", "압박", "눈치", "초조"],
    "긍정/활기": ["기쁨", "좋아", "행복", "설레", "즐거", "신나", "재미있", "의욕", "뿌듯"],
    "우울/슬픔": ["우울", "슬프", "눈물", "허탈", "공허", "외로", "실망", "허무"],
    "분노/짜증": ["화남", "화가", "짜증", "열받", "분하", "억울", "당황", "기분나쁘"],
}

# ── 활동 키워드 ──────────────────────────────────────────────────────────────
ACTIVITY_KEYWORDS: dict[str, list[str]] = {
    "공부": ["공부", "시험", "문제", "오답", "외웠", "복습", "학습", "수업", "강의", "기출"],
    "운동": ["운동", "헬스", "산책", "걷기", "달리기", "수영", "스트레칭"],
    "식사": ["밥", "먹었", "먹고", "식사", "점심", "저녁", "아침식사", "치킨", "라면",
             "삼겹", "회식", "카페", "커피", "음식"],
    "독서": ["책", "독서", "읽었", "읽고", "소설", "읽는"],
    "수면": ["잠", "수면", "잤다", "잠들", "일어났", "기상", "알람", "깼다", "수면제"],
    "개발": ["코딩", "개발", "클로드", "온유", "파이썬", "스크립트", "배포"],
}

# ── 수면 시각 추출 정규식 ─────────────────────────────────────────────────────
import re

# "밤 10시", "10시 30분쯤에 잠", "오전 1시에 잠들", "새벽 2시 잠" 등 다양한 패턴 처리
_SLEEP_TIME_RE = re.compile(
    r'(오전|오후|밤|새벽|자정)?\s*(\d{1,2})\s*시\s*(\d{0,2})\s*분?\s*'
    r'(쯤|경|께)?\s*(에\s*)?(잠들|잠에\s*들|잠\s*들|잤|취침)'
)
_WAKE_TIME_RE = re.compile(
    r'(오전|오후|아침)?\s*(\d{1,2})\s*시\s*(\d{0,2})\s*분?\s*'
    r'(쯤|경|께)?\s*(에\s*)?(일어|기상|깼|눈\s*떴)'
)


def _to_24h(meridiem: str | None, hour: int) -> int:
    """오전/오후/밤/새벽 + 시각 → 24시간 정수 변환.
    '밤 12시' = 0시(자정), '오후 1시' = 13시.
    """
    if meridiem in ("오후", "밤"):
        if hour == 12:
            return 0   # 밤 12시 = 자정 = 0
        if hour < 12:
            return hour + 12
    if meridiem in ("오전", "아침") and hour == 12:
        return 0   # 오전 12시 = 자정
    if meridiem == "새벽":
        return hour  # 새벽 1~5시 그대로
    if meridiem is None and hour <= 5:
        return hour  # 숫자만 있고 1~5시면 새벽으로 간주
    return hour


def _parse_sleep_times(text: str) -> dict[str, int | None]:
    """잠든 시각, 일어난 시각 파싱. 없으면 None."""
    result: dict[str, int | None] = {"sleep_hour": None, "wake_hour": None}

    m = _SLEEP_TIME_RE.search(text)
    if m:
        meridiem = m.group(1)
        hour = int(m.group(2))
        result["sleep_hour"] = _to_24h(meridiem, hour)

    m2 = _WAKE_TIME_RE.search(text)
    if m2:
        meridiem2 = m2.group(1)
        hour2 = int(m2.group(2))
        result["wake_hour"] = _to_24h(meridiem2, hour2)

    return result


# ── 메인 분석 ─────────────────────────────────────────────────────────────────

def parse_diary_files(days: int = 90) -> dict:
    """DAILY/ 파일을 읽어 날짜별 카운트 데이터 반환."""
    cutoff = datetime.now() - timedelta(days=days)
    daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sleep_records: list[dict] = []
    total_files = 0
    date_list: list[str] = []

    # DAILY/ 내의 .md 파일만 (하위 폴더 제외)
    for f in sorted(DAILY_DIR.glob("*.md")):
        if f.parent != DAILY_DIR:
            continue
        try:
            date = datetime.strptime(f.stem, "%Y-%m-%d")
        except ValueError:
            continue
        if date < cutoff:
            continue

        text = f.read_text(encoding="utf-8", errors="ignore")
        date_str = f.stem
        date_list.append(date_str)
        total_files += 1

        # 감정 키워드
        for cat, keywords in MOOD_KEYWORDS.items():
            for kw in keywords:
                cnt = text.count(kw)
                if cnt:
                    daily_counts[date_str][f"mood_{cat}"] += cnt

        # 활동 키워드
        for cat, keywords in ACTIVITY_KEYWORDS.items():
            for kw in keywords:
                cnt = text.count(kw)
                if cnt:
                    daily_counts[date_str][f"activity_{cat}"] += cnt

        # 수면 시각
        times = _parse_sleep_times(text)
        if times["sleep_hour"] is not None or times["wake_hour"] is not None:
            sleep_records.append({"date": date_str, **times})

    return {
        "days": days,
        "total_files": total_files,
        "date_list": date_list,
        "daily_counts": daily_counts,
        "sleep_records": sleep_records,
    }


def _split_recent(date_list: list[str], daily_counts: dict,
                  recent_days: int = 7) -> tuple[set[str], set[str]]:
    """날짜 목록을 최근 N일 / 이전 M일로 분리."""
    cutoff = datetime.now() - timedelta(days=recent_days)
    recent = {d for d in date_list
              if datetime.strptime(d, "%Y-%m-%d") >= cutoff}
    older  = set(date_list) - recent
    return recent, older


def aggregate_patterns(data: dict) -> dict:
    """날짜별 카운트 → 전체 통계 + 최근 7일 vs 이전 기간 비교 집계."""
    daily_counts = data["daily_counts"]
    date_list    = data["date_list"]
    category_totals: Counter = Counter()
    category_days:   Counter = Counter()

    for _date, counts in daily_counts.items():
        for cat, cnt in counts.items():
            category_totals[cat] += cnt
            category_days[cat] += 1

    tf = data["total_files"]
    result: dict = {
        "mood": {},
        "activity": {},
        "sleep": {},
        "delta": {},   # 최근 7일 vs 이전 기간 변화량
        "meta": {
            "period_days": data["days"],
            "total_files": tf,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    }

    for cat_key, total in category_totals.items():
        days_n = category_days[cat_key]
        avg = round(total / tf, 2) if tf else 0
        entry = {"total": total, "days": days_n, "avg_per_day": avg,
                 "frequency_pct": round(days_n / tf * 100) if tf else 0}
        if cat_key.startswith("mood_"):
            result["mood"][cat_key[5:]] = entry
        elif cat_key.startswith("activity_"):
            result["activity"][cat_key[9:]] = entry

    # ── 최근 7일 vs 이전 기간 변화 (delta) ─────────────────────────────────
    recent_dates, older_dates = _split_recent(date_list, daily_counts)
    n_recent = max(len(recent_dates), 1)
    n_older  = max(len(older_dates), 1)

    for cat_key in category_totals:
        recent_total = sum(daily_counts[d].get(cat_key, 0) for d in recent_dates)
        older_total  = sum(daily_counts[d].get(cat_key, 0) for d in older_dates)
        recent_avg = round(recent_total / n_recent, 2)
        older_avg  = round(older_total  / n_older,  2)
        delta      = round(recent_avg - older_avg, 2)

        name = cat_key[5:] if cat_key.startswith("mood_") else (
               cat_key[9:] if cat_key.startswith("activity_") else cat_key)
        result["delta"][name] = {
            "recent_7d_avg": recent_avg,
            "older_avg":     older_avg,
            "delta":         delta,        # 양수 = 최근 증가, 음수 = 최근 감소
            "direction":     "▲" if delta > 0.1 else ("▼" if delta < -0.1 else "→"),
        }

    # ── 수면 통계 ──────────────────────────────────────────────────────────
    records    = data["sleep_records"]
    sleep_hrs  = [r["sleep_hour"] for r in records if r["sleep_hour"] is not None]
    wake_hrs   = [r["wake_hour"]  for r in records if r["wake_hour"]  is not None]
    if sleep_hrs:
        result["sleep"]["avg_bedtime_hour"] = round(sum(sleep_hrs) / len(sleep_hrs), 1)
        result["sleep"]["samples"]          = len(sleep_hrs)
    if wake_hrs:
        result["sleep"]["avg_wake_hour"] = round(sum(wake_hrs) / len(wake_hrs), 1)

    return result


def build_markdown(patterns: dict) -> str:
    """패턴 통계 → 마크다운 문자열."""
    meta     = patterns["meta"]
    mood     = patterns["mood"]
    activity = patterns["activity"]
    sleep    = patterns["sleep"]

    lines = [
        "# 일기 패턴 분석 (Pattern RAG)",
        "",
        f"생성: {meta['generated_at']} | 기간: 최근 {meta['period_days']}일 "
        f"| 분석 파일: {meta['total_files']}개",
        "",
        "## 감정 패턴",
        "",
        "| 카테고리 | 총 횟수 | 등장 일수 | 비율 | 일평균 |",
        "|---------|---------|---------|------|-------|",
    ]
    for name, s in sorted(mood.items(), key=lambda x: x[1]["total"], reverse=True):
        lines.append(
            f"| {name} | {s['total']} | {s['days']}일 "
            f"| {s['frequency_pct']}% | {s['avg_per_day']} |"
        )

    lines += [
        "",
        "## 활동 패턴",
        "",
        "| 카테고리 | 총 횟수 | 등장 일수 | 비율 | 일평균 |",
        "|---------|---------|---------|------|-------|",
    ]
    for name, s in sorted(activity.items(), key=lambda x: x[1]["total"], reverse=True):
        lines.append(
            f"| {name} | {s['total']} | {s['days']}일 "
            f"| {s['frequency_pct']}% | {s['avg_per_day']} |"
        )

    if sleep:
        lines += ["", "## 수면 패턴", ""]
        if "avg_sleep_hour" in sleep:
            h = sleep["avg_sleep_hour"]
            lines.append(f"- 평균 취침 시각: {int(h)}시 {int((h % 1) * 60):02d}분 "
                         f"(샘플 {sleep['samples']}개)")
        if "avg_wake_hour" in sleep:
            h = sleep["avg_wake_hour"]
            lines.append(f"- 평균 기상 시각: {int(h)}시 {int((h % 1) * 60):02d}분")

    # 요약
    top_mood     = max(mood.items(),     key=lambda x: x[1]["total"]) if mood     else None
    top_activity = max(activity.items(), key=lambda x: x[1]["total"]) if activity else None
    lines += ["", "## 요약", ""]
    if top_mood:
        lines.append(f"- 가장 자주 기록된 감정: **{top_mood[0]}** "
                     f"({top_mood[1]['total']}회, {top_mood[1]['frequency_pct']}% 일수)")
    if top_activity:
        lines.append(f"- 가장 자주 기록된 활동: **{top_activity[0]}** "
                     f"({top_activity[1]['total']}회, {top_activity[1]['frequency_pct']}% 일수)")

    return "\n".join(lines)


def run(days: int = 90, save_json: bool = True) -> dict:
    """메인 실행: 분석 → patterns/ 저장."""
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[Pattern RAG] DAILY/ 분석 중 (최근 {days}일)...")
    data     = parse_diary_files(days)
    print(f"  → 파일 {data['total_files']}개 처리")

    patterns = aggregate_patterns(data)
    md       = build_markdown(patterns)

    md_path = PATTERNS_DIR / "diary_patterns.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"  → 저장: {md_path}")

    if save_json:
        json_path = PATTERNS_DIR / "diary_patterns.json"
        json_path.write_text(
            json.dumps(patterns, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  → 저장: {json_path}")

    print(f"\n{'=' * 60}")
    print(md)
    return patterns


if __name__ == "__main__":
    days_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    run(days=days_arg)
