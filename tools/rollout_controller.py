"""
rollout_controller.py — Phase 16-B Drift Detection & Shadow RL 상태 관리

역할:
  - metrics_log.jsonl 최근 N건 기반 win_rate 계산
  - 3회 연속 하락 추세 감지 (Drift)
  - RL 신뢰도 권고 반환 (강제 off 아님 — _SHADOW_RL_ON 플래그와 독립)

실행: python SYSTEM/tools/rollout_controller.py  (상태 출력만)
"""
import json
import math
from pathlib import Path

SYSTEM_DIR  = Path(__file__).parent.parent
LOG_FILE    = SYSTEM_DIR / "metrics_log.jsonl"
Q_FILE      = SYSTEM_DIR / "shadow_q_table.json"
STATE_FILE  = SYSTEM_DIR / "rl_rollout_state.json"

WINDOW      = 20   # win_rate 계산 슬라이딩 윈도우
DRIFT_N     = 3    # 연속 하락 판정 횟수
MIN_WIN_RATE = 0.55  # 이 미만이면 경고


# ── Win Rate 계산 ─────────────────────────────────────────────────────────────

def _load_recent_logs(n: int = WINDOW) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text("utf-8").splitlines()
    records = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
        if len(records) >= n:
            break
    return list(reversed(records))


def calc_win_rate(logs: list[dict]) -> float:
    """is_success=True 비율. 로그 없으면 -1.0."""
    if not logs:
        return -1.0
    wins = sum(1 for r in logs if r.get("is_success", True))
    return round(wins / len(logs), 4)


# ── Drift 감지 ────────────────────────────────────────────────────────────────

def detect_drift(win_rates: list[float]) -> bool:
    """
    최근 DRIFT_N개의 win_rate가 단조 감소하면 True.
    값이 부족하면 False.
    """
    if len(win_rates) < DRIFT_N:
        return False
    tail = win_rates[-DRIFT_N:]
    return all(earlier > later for earlier, later in zip(tail, tail[1:]))


# ── 상태 저장/로드 ─────────────────────────────────────────────────────────────

def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"win_rate_history": [], "drift_count": 0}
    try:
        return json.loads(STATE_FILE.read_text("utf-8"))
    except Exception:
        return {"win_rate_history": [], "drift_count": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 메인: 상태 업데이트 + 권고 반환 ──────────────────────────────────────────

def update_and_check() -> dict:
    """
    최신 로그로 win_rate 갱신 → drift 감지 → 결과 반환.

    반환:
        {
            "win_rate":   float,      # 현재 win_rate (-1.0 = 데이터 없음)
            "drift":      bool,       # True = 성능 하락 추세 감지
            "recommend":  str,        # "OK" | "WATCH" | "FREEZE"
            "history":    list[float],
        }
    """
    logs      = _load_recent_logs(WINDOW)
    win_rate  = calc_win_rate(logs)
    state     = load_state()

    history = state.get("win_rate_history", [])
    if win_rate >= 0:
        history.append(win_rate)
        history = history[-20:]   # 최대 20개 유지

    drift = detect_drift(history)

    if drift:
        recommend = "FREEZE"
    elif win_rate >= 0 and win_rate < MIN_WIN_RATE:
        recommend = "WATCH"
    else:
        recommend = "OK"

    state["win_rate_history"] = history
    state["drift_count"] = state.get("drift_count", 0) + (1 if drift else 0)
    save_state(state)

    return {
        "win_rate":  win_rate,
        "drift":     drift,
        "recommend": recommend,
        "history":   history,
    }


# ── Q-table 요약 ──────────────────────────────────────────────────────────────

def q_table_summary() -> dict:
    """shadow_q_table.json 요약: state 수, 최고 Q값 action 목록."""
    if not Q_FILE.exists():
        return {"states": 0, "best_actions": {}}
    try:
        data  = json.loads(Q_FILE.read_text("utf-8"))
        qt    = data.get("q_table", {})
        best  = {}
        for state, actions in qt.items():
            if actions:
                ba = max(actions, key=lambda a: actions[a])
                best[state] = {"action": ba, "q": round(actions[ba], 3)}
        return {"states": len(qt), "best_actions": best}
    except Exception:
        return {"states": 0, "best_actions": {}}


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = update_and_check()
    qt     = q_table_summary()

    print("\n=== Shadow RL Rollout Controller ===")
    wr = result["win_rate"]
    print(f"Win Rate  : {wr*100:.1f}%" if wr >= 0 else "Win Rate  : (데이터 없음)")
    print(f"Drift     : {'YES ⚠' if result['drift'] else 'NO'}")
    print(f"권고      : {result['recommend']}")
    print(f"Q-table   : {qt['states']}개 state")
    if qt["best_actions"]:
        print("Best Actions:")
        for st, info in qt["best_actions"].items():
            print(f"  {st} → {info['action']} (Q={info['q']})")
    print("=" * 36)
