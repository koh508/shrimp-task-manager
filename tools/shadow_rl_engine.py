"""
shadow_rl_engine.py — Phase 13-B Safe Shadow RL

오프라인 배치(Offline Batch) 강화학습 엔진.
실시간 파이프라인에는 절대 쓰지 않음.

실행: python SYSTEM/tools/shadow_rl_engine.py
      → shadow_q_table.json 갱신
"""
import json
import logging
import math
import sys
from datetime import datetime
from pathlib import Path

SYSTEM_DIR    = Path(__file__).parent.parent
LOG_FILE      = SYSTEM_DIR / "metrics_log.jsonl"
BASELINE_FILE = SYSTEM_DIR / "baseline.json"
Q_TABLE_FILE  = SYSTEM_DIR / "shadow_q_table.json"

ALPHA          = 0.1   # Q-learning rate
MIN_CONFIDENCE = 3.0   # Soft Override 최소 절대 점수
MIN_SAMPLES    = 5     # Soft Override 최소 샘플 수
RECENT_WINDOW  = 20    # recent_rewards 슬라이딩 윈도우

logger = logging.getLogger(__name__)

# ── Q-table 캐시 (determine_best_action 반복 호출 최적화) ────────────────────
_q_cache: dict = {}    # {"mtime": float, "data": dict}


# ══════════════════════════════════════════════════════════════════════════════
# 1. State 추출 — Action 제거 (State Explosion 방지)
# ══════════════════════════════════════════════════════════════════════════════

def extract_state(log_entry: dict) -> str:
    """
    State = intent | HIT/NOHIT | error_type
    Action은 State에 포함하지 않음 (차원의 저주 방지).
    """
    intent     = log_entry.get("intent", "SEMANTIC") or "SEMANTIC"
    has_hits   = log_entry.get("search_hits", 0) > 0
    error_type = log_entry.get("error_type", "NONE") or "NONE"
    hit_status = "HIT" if has_hits else "NOHIT"
    return f"{intent}|{hit_status}|{error_type}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. 보상 계산 — Quality Bonus + has_hits 기반 Fallback 조정
# ══════════════════════════════════════════════════════════════════════════════

def calculate_reward(baseline: dict, log: dict) -> float:
    """
    성공(+5) + latency 보상 + Quality Bonus + degraded 패널티.
    빠른 오답(Fast Fallback)이 높은 보상을 받지 않도록 설계.
    """
    action     = log.get("action", "UNKNOWN")
    is_success = log.get("is_success", True)
    has_hits   = log.get("search_hits", 0) > 0
    degraded   = log.get("degraded", False)
    latency_ms = log.get("latency_ms", 0)

    reward = 0.0

    # 1. 성공 여부 (가장 중요)
    reward += 5.0 if is_success else -10.0

    # 2. Latency 보상 (baseline p95 기준, 없으면 p90 fallback)
    bl_action  = baseline.get("baseline", {}).get(action, {})
    bl_latency = bl_action.get("latency_ms", {})
    ref_ms     = bl_latency.get("p95") or bl_latency.get("p90") or 1000

    if latency_ms <= ref_ms * 0.5:
        reward += 3.0
    elif latency_ms <= ref_ms:
        reward += 1.0
    elif latency_ms <= ref_ms * 2:
        reward -= 2.0
    else:
        reward -= 5.0

    # 3. Quality Bonus (RAG 우선, Fallback 억제)
    if action == "ANSWER_RAG" and has_hits:
        reward += 1.5
    elif action == "ANSWER_FALLBACK":
        reward -= 1.0
        if not has_hits:
            reward -= 0.5   # 검색도 없는데 fallback → 추가 패널티

    # 4. Degraded 패널티 (가볍게)
    if degraded:
        reward -= 1.0

    return round(reward, 4)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Q-table I/O
# ══════════════════════════════════════════════════════════════════════════════

def _load_q_table() -> dict:
    """mtime 기반 캐시로 파일 읽기 최소화."""
    global _q_cache
    if not Q_TABLE_FILE.exists():
        return {"q_table": {}, "counts": {}, "recent_rewards": {}, "_meta": {}}
    mtime = Q_TABLE_FILE.stat().st_mtime
    if _q_cache.get("mtime") == mtime:
        return _q_cache["data"]
    try:
        data = json.loads(Q_TABLE_FILE.read_text("utf-8"))
        _q_cache = {"mtime": mtime, "data": data}
        return data
    except Exception:
        return {"q_table": {}, "counts": {}, "recent_rewards": {}, "_meta": {}}


def _save_q_table(data: dict):
    global _q_cache
    Q_TABLE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    _q_cache = {}   # 캐시 무효화


# ══════════════════════════════════════════════════════════════════════════════
# 4. Soft Override — 엄격한 5중 조건
# ══════════════════════════════════════════════════════════════════════════════

def determine_best_action(state: str, heuristic_action: str | None = None) -> str | None:
    """
    RL 제안 action 반환. 5개 조건 중 하나라도 불통이면 None.
    None → heuristic 그대로 사용.

    조건:
    1. 학습 데이터 존재 (state 있음)
    2. action 다양성 >= 2 (비교 대상 필요)
    3. MIN_SAMPLES >= 5
    4. MIN_CONFIDENCE >= 3.0 (절대 점수)
    5. 분산 필터 (std < 0.5 → 과적합 의심 → 금지)
    6. 최근 성능 필터 (recent_avg < 1.0 → 금지)
    """
    try:
        qt = _load_q_table()
        state_actions  = qt.get("q_table", {}).get(state, {})
        state_counts   = qt.get("counts", {}).get(state, {})
        state_recent   = qt.get("recent_rewards", {}).get(state, {})

        # 조건 1+2: 학습 데이터 + action 다양성
        if len(state_actions) < 2:
            return None

        best_action = max(state_actions, key=lambda a: state_actions[a])
        best_q      = state_actions[best_action]
        best_count  = state_counts.get(best_action, 0)
        best_recent = state_recent.get(best_action, [])

        # heuristic과 같으면 override 불필요
        if best_action == heuristic_action:
            return None

        # 조건 3: 최소 샘플
        if best_count < MIN_SAMPLES:
            return None

        # 조건 4: 절대 신뢰도
        if best_q < MIN_CONFIDENCE:
            return None

        # 조건 5: 분산 필터 (값들이 너무 일정하면 과적합)
        if len(best_recent) >= 3:
            avg = sum(best_recent) / len(best_recent)
            std = math.sqrt(sum((x - avg) ** 2 for x in best_recent) / len(best_recent))
            if std < 0.5:
                return None

        # 조건 6: 최근 성능
        if best_recent:
            recent_avg = sum(best_recent[-5:]) / min(len(best_recent), 5)
            if recent_avg < 1.0:
                return None

        logger.info("[Shadow RL] Override: %s → %s (Q=%.2f, n=%d)",
                    heuristic_action, best_action, best_q, best_count)
        return best_action

    except Exception as e:
        logger.warning("[Shadow RL] determine_best_action 오류: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 5. Offline Batch 업데이트
# ══════════════════════════════════════════════════════════════════════════════

def run_batch_rl_update(alpha: float = ALPHA) -> dict:
    """
    metrics_log.jsonl 전체 → Q-table 배치 갱신 → shadow_q_table.json 저장.
    하루 1회 수동 또는 스케줄 실행.
    """
    if not LOG_FILE.exists():
        print("metrics_log.jsonl 없음. 종료.")
        return {}

    if not BASELINE_FILE.exists():
        print("baseline.json 없음. 먼저 baseline_calculator.py 실행.")
        return {}

    logs     = []
    for line in LOG_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            logs.append(json.loads(line))
        except Exception:
            pass

    if not logs:
        print("로그 없음.")
        return {}

    baseline = json.loads(BASELINE_FILE.read_text("utf-8"))
    existing = _load_q_table()

    q_table       = existing.get("q_table", {})
    counts        = existing.get("counts", {})
    recent_rewards = existing.get("recent_rewards", {})

    for log in logs:
        state  = extract_state(log)
        action = log.get("action", "UNKNOWN")
        reward = calculate_reward(baseline, log)

        # Q-table 초기화
        if state not in q_table:
            q_table[state]        = {}
            counts[state]         = {}
            recent_rewards[state] = {}

        # Q-value 업데이트 (incremental mean → weighted update)
        old_q = q_table[state].get(action, 0.0)
        q_table[state][action] = round((1 - alpha) * old_q + alpha * reward, 4)

        # 샘플 수 갱신
        counts[state][action] = counts[state].get(action, 0) + 1

        # Recent rewards 슬라이딩 윈도우
        if action not in recent_rewards[state]:
            recent_rewards[state][action] = []
        recent_rewards[state][action].append(reward)
        recent_rewards[state][action] = recent_rewards[state][action][-RECENT_WINDOW:]

    result = {
        "q_table":        q_table,
        "counts":         counts,
        "recent_rewards": recent_rewards,
        "_meta": {
            "last_updated":   datetime.now().isoformat(),
            "total_records":  len(logs),
            "alpha":          alpha,
        },
    }
    _save_q_table(result)

    # 요약 출력
    print(f"배치 완료: {len(logs)}개 로그 → {len(q_table)}개 state")
    for state, actions in q_table.items():
        best = max(actions, key=lambda a: actions[a])
        print(f"  {state}: best={best} (Q={actions[best]:.3f})")

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_batch_rl_update()
