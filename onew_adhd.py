"""
onew_adhd.py — ADHD 보조 엔진
근거: Barkley (비반응 폐기), Hallowell (과집중 보호), Ratey (즉각 보상)

핵심 수식:
    response_rate(feature) = responses / suggestions  (최근 30일)
    feature 활성 조건: suggestions < MIN_SAMPLES OR response_rate >= PRUNE_THRESHOLD
"""

import os, json, time
from datetime import datetime, date, timedelta
from pathlib import Path

# ── 경로 ─────────────────────────────────────────────────────────────────────
SYSTEM_DIR        = os.path.dirname(os.path.abspath(__file__))
OBSIDIAN_VAULT    = os.path.dirname(SYSTEM_DIR)
ADHD_DB_FILE      = os.path.join(SYSTEM_DIR, "onew_adhd_db.json")

# ── 파라미터 ─────────────────────────────────────────────────────────────────
PRUNE_THRESHOLD   = 0.2   # 반응률 20% 미만 + 최소 샘플 충족 시 기능 비활성
MIN_SAMPLES       = 3     # 폐기 판단에 필요한 최소 제안 횟수
LOOKBACK_DAYS     = 30    # 반응률 계산 기간
HYPERFOCUS_GAP    = 180   # 마지막 메시지로부터 이 초(3분) 이내 연속 입력 → 과집중 의심
HYPERFOCUS_MIN    = 4     # 과집중 판정에 필요한 연속 메시지 수
STREAK_FILE       = os.path.join(SYSTEM_DIR, "onew_streak.json")

# ── DB 입출력 ─────────────────────────────────────────────────────────────────
def _load() -> dict:
    if os.path.exists(ADHD_DB_FILE):
        try:
            with open(ADHD_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"features": {}, "hyperfocus_log": [], "message_times": []}

def _save(db: dict):
    with open(ADHD_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ==============================================================================
# 1. 비반응 폐기 시스템
# ==============================================================================
class FeatureTracker:
    """
    기능별 반응률 추적 및 자동 폐기.
    response_rate = responses / suggestions  (최근 LOOKBACK_DAYS일)
    response_rate < PRUNE_THRESHOLD AND suggestions >= MIN_SAMPLES → 비활성
    """

    def __init__(self):
        self.db = _load()

    def _cutoff(self) -> str:
        return (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()

    def record_suggestion(self, feature: str):
        """온유가 특정 기능의 제안을 했을 때 호출."""
        today = date.today().isoformat()
        feat  = self.db["features"].setdefault(feature, {"suggestions": [], "responses": []})
        feat["suggestions"].append(today)
        # 오래된 기록 정리
        cutoff = self._cutoff()
        feat["suggestions"] = [d for d in feat["suggestions"] if d >= cutoff]
        feat["responses"]   = [d for d in feat["responses"]   if d >= cutoff]
        _save(self.db)

    def record_response(self, feature: str):
        """사용자가 해당 기능 제안에 실제로 반응했을 때 호출."""
        today = date.today().isoformat()
        feat  = self.db["features"].setdefault(feature, {"suggestions": [], "responses": []})
        feat["responses"].append(today)
        _save(self.db)

    def response_rate(self, feature: str) -> float:
        """반응률 반환. 샘플 없으면 1.0 (아직 판단 불가)."""
        feat = self.db["features"].get(feature, {})
        s = len(feat.get("suggestions", []))
        r = len(feat.get("responses",   []))
        if s == 0:
            return 1.0
        return r / s

    def is_active(self, feature: str) -> bool:
        """
        기능 활성 여부.
        MIN_SAMPLES 미충족 → True (아직 판단 보류)
        response_rate >= PRUNE_THRESHOLD → True (살아있음)
        response_rate <  PRUNE_THRESHOLD → False (폐기)
        """
        feat = self.db["features"].get(feature, {})
        s = len(feat.get("suggestions", []))
        if s < MIN_SAMPLES:
            return True
        return self.response_rate(feature) >= PRUNE_THRESHOLD

    def status_report(self) -> str:
        """현재 기능별 반응률 보고."""
        if not self.db["features"]:
            return "아직 수집된 반응 데이터가 없습니다."
        lines = ["## 🎯 ADHD 기능 반응률 현황\n"]
        for feat, data in sorted(self.db["features"].items()):
            s = len(data.get("suggestions", []))
            r = len(data.get("responses",   []))
            rate = (r / s) if s else 1.0
            active = "✅ 활성" if self.is_active(feat) else "❌ 폐기"
            lines.append(f"- **{feat}**: {rate:.0%} ({r}/{s}) {active}")
        lines.append(f"\n기준: 제안 {MIN_SAMPLES}회 이상 + 반응률 {PRUNE_THRESHOLD:.0%} 미만 → 자동 폐기")
        return "\n".join(lines)


# ==============================================================================
# 2. 과집중 보호 시스템
# ==============================================================================
class HyperfocusGuard:
    """
    사용자 메시지 타이밍 분석 → 과집중 상태 감지.
    HYPERFOCUS_GAP초 이내 연속 메시지 HYPERFOCUS_MIN개 이상 → 과집중 판정.
    과집중 중에는 모든 Push 제안 차단.
    """

    def __init__(self):
        self.db = _load()

    def record_message(self):
        """사용자 메시지 수신 시 호출."""
        now = time.time()
        times = self.db.get("message_times", [])
        times.append(now)
        # 최근 20개만 유지
        self.db["message_times"] = times[-20:]
        _save(self.db)

    def is_hyperfocused(self) -> bool:
        """
        과집중 판정:
        최근 HYPERFOCUS_MIN개 메시지 간격이 모두 HYPERFOCUS_GAP초 이내 → True
        """
        times = self.db.get("message_times", [])
        if len(times) < HYPERFOCUS_MIN:
            return False
        recent = times[-HYPERFOCUS_MIN:]
        gaps = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        return all(g <= HYPERFOCUS_GAP for g in gaps)

    def can_push(self) -> bool:
        """Push 제안 허용 여부 (과집중 중이면 False)."""
        return not self.is_hyperfocused()


# ==============================================================================
# 3. 공부 스트릭 추적
# ==============================================================================
class StudyStreak:
    """
    하루 공부 완료 기록 → 연속일 계산 → 즉각 피드백.
    Barkley: 즉각 보상만 ADHD 뇌에 작동.
    """

    def _load(self) -> dict:
        if os.path.exists(STREAK_FILE):
            try:
                with open(STREAK_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"dates": []}

    def _save(self, data: dict):
        with open(STREAK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_study(self) -> str:
        """
        오늘 공부 완료 기록.
        반환: 즉각 피드백 문자열
        """
        data  = self._load()
        today = date.today().isoformat()
        dates = data.get("dates", [])

        if today in dates:
            streak = self._calc_streak(dates)
            return f"✅ 오늘 공부 이미 기록됨. 현재 {streak}일 연속."

        dates.append(today)
        dates = sorted(set(dates))[-365:]  # 최근 1년
        data["dates"] = dates
        self._save(data)

        streak = self._calc_streak(dates)
        return self._feedback(streak)

    def _calc_streak(self, dates: list) -> int:
        """연속 학습일 계산."""
        if not dates:
            return 0
        sorted_dates = sorted(dates, reverse=True)
        streak = 1
        for i in range(len(sorted_dates) - 1):
            d1 = date.fromisoformat(sorted_dates[i])
            d2 = date.fromisoformat(sorted_dates[i+1])
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak

    def _feedback(self, streak: int) -> str:
        """연속일 기반 즉각 피드백 (지연 보상 없음)."""
        if streak == 1:
            return "✅ 오늘 공부 완료. 시작했다."
        elif streak < 7:
            return f"✅ {streak}일 연속. 끊기지 않았다."
        elif streak < 30:
            return f"✅ {streak}일 연속. 습관이 만들어지고 있다."
        else:
            return f"✅ {streak}일 연속. 이미 다른 사람이다."

    def get_status(self) -> str:
        data   = self._load()
        dates  = data.get("dates", [])
        streak = self._calc_streak(dates)
        total  = len(dates)
        return f"📅 공부 스트릭: {streak}일 연속 | 총 {total}일 기록"


# ==============================================================================
# 4. 도파민 메뉴 (Pull 전용 — 요청 시에만)
# ==============================================================================
DOPAMINE_MENU = {
    "애피타이저 (1~5분)": [
        "스트레칭 2분",
        "냉수 한 잔",
        "좋아하는 노래 1곡",
        "창문 열고 바깥 공기",
    ],
    "메인 (15~30분)": [
        "빠르게 걷기 or 철봉",
        "샤워",
        "집 안 짧은 청소",
    ],
    "디저트 (공부 완료 후)": [
        "유튜브 10분",
        "게임 1판",
        "간식 1개",
    ]
}

def get_dopamine_menu() -> str:
    """도파민 메뉴 반환 (요청 시에만 — Push 금지)."""
    lines = ["## 🎮 도파민 메뉴\n자극이 필요할 때 아래에서 고르세요.\n"]
    for category, items in DOPAMINE_MENU.items():
        lines.append(f"**{category}**")
        for item in items:
            lines.append(f"  - {item}")
    lines.append("\n⚠️ 공부 시작 전 애피타이저만. 디저트는 완료 후.")
    return "\n".join(lines)


# ==============================================================================
# 5. 통합 엔진
# ==============================================================================
class ADHDEngine:
    def __init__(self):
        self.tracker  = FeatureTracker()
        self.guard    = HyperfocusGuard()
        self.streak   = StudyStreak()

    def on_message(self):
        """사용자 메시지마다 호출 — 과집중 타이밍 기록."""
        self.guard.record_message()

    def suggest(self, feature: str, text: str) -> str | None:
        """
        기능 제안 시도.
        - 과집중 중이면 None 반환 (Push 차단)
        - 기능 폐기됐으면 None 반환
        - 통과 시 제안 기록 후 text 반환
        """
        if not self.guard.can_push():
            return None
        if not self.tracker.is_active(feature):
            return None
        self.tracker.record_suggestion(feature)
        return text

    def respond(self, feature: str):
        """사용자가 기능 제안에 반응했을 때 호출."""
        self.tracker.record_response(feature)

    def complete_study(self) -> str:
        """공부 완료 기록 + 즉각 피드백."""
        return self.streak.record_study()

    def status(self) -> str:
        return "\n\n".join([
            self.streak.get_status(),
            self.tracker.status_report(),
            f"과집중 상태: {'🔴 보호 중 (Push 차단)' if self.guard.is_hyperfocused() else '🟢 일반 모드'}",
        ])


# 싱글턴
_engine: ADHDEngine | None = None

def get_engine() -> ADHDEngine:
    global _engine
    if _engine is None:
        _engine = ADHDEngine()
    return _engine


# ==============================================================================
# 공개 API (obsidian_agent.py에서 호출)
# ==============================================================================
def on_user_message():
    """사용자 메시지 수신 시 호출 (타이밍 기록)."""
    get_engine().on_message()

def try_suggest(feature: str, text: str) -> str | None:
    """기능 제안 시도. 과집중/폐기 시 None."""
    return get_engine().suggest(feature, text)

def mark_responded(feature: str):
    """사용자가 제안에 반응했을 때 호출."""
    get_engine().respond(feature)

def record_study_done() -> str:
    """공부 완료 기록 + 즉각 피드백 반환."""
    return get_engine().complete_study()

def adhd_status() -> str:
    """전체 현황 보고."""
    return get_engine().status()

def dopamine_menu() -> str:
    """도파민 메뉴 (Pull 전용)."""
    return get_dopamine_menu()
