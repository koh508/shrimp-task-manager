"""
sre_dashboard.py — 온유 SRE 관제 대시보드 (CLI)

실행: python SYSTEM/tools/sre_dashboard.py

읽는 파일 (read-only):
  - metrics_log.jsonl   : 최근 쿼리 성능 기록
  - baseline.json       : action별 기준선
  - shadow_q_table.json : Q-learning 학습 결과
  - rl_rollout_state.json : Drift 상태
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

# Windows 터미널 UTF-8 출력 보장
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYSTEM_DIR = Path(__file__).parent.parent
LOG_FILE   = SYSTEM_DIR / "metrics_log.jsonl"
BL_FILE    = SYSTEM_DIR / "baseline.json"
QT_FILE    = SYSTEM_DIR / "shadow_q_table.json"
RS_FILE    = SYSTEM_DIR / "rl_rollout_state.json"


def _load_jsonl(path: Path, limit: int = 100) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text("utf-8").splitlines()
    records = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
        if len(records) >= limit:
            break
    return list(reversed(records))


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def _bar(value: float, width: int = 20, char: str = "█") -> str:
    """0.0~1.0 값을 바 차트로 변환."""
    filled = int(value * width)
    filled = max(0, min(filled, width))
    return char * filled + "░" * (width - filled)


def render():
    logs     = _load_jsonl(LOG_FILE, 100)
    baseline = _load_json(BL_FILE)
    qt_data  = _load_json(QT_FILE)
    rs_data  = _load_json(RS_FILE)

    # ── 기본 통계 ────────────────────────────────────────────────────────────
    total     = len(logs)
    successes = sum(1 for r in logs if r.get("is_success", True))
    win_rate  = successes / total if total > 0 else 0.0

    # drift 상태
    history   = rs_data.get("win_rate_history", [])
    drift     = len(history) >= 3 and all(a > b for a, b in zip(history[-3:], history[-2:]))

    # action 분포 (최근 100건)
    action_counts = Counter(r.get("action", "UNKNOWN") for r in logs)

    # Q-table
    qt     = qt_data.get("q_table", {})
    counts = qt_data.get("counts", {})
    meta   = qt_data.get("_meta", {})

    # ── 렌더링 ──────────────────────────────────────────────────────────────
    W = 52
    print()
    print("=" * W)
    print(" [온유 SRE & Shadow RL 관제 대시보드]")
    print("=" * W)

    # 1. Shadow RL 상태
    rl_on = QT_FILE.exists()
    print(f" RL 엔진    : [ {'ON ' if rl_on else 'OFF'} ]")
    print(f" Q-table    : {len(qt)}개 state  "
          f"(마지막 업데이트: {meta.get('last_updated', '없음')[:19]})")

    print()

    # 2. 성능 지표
    wr_warn = "[!] " if win_rate >= 0 and win_rate < 0.7 else "    "
    print(f" Win Rate   :{wr_warn}{win_rate*100:.1f}%  [{_bar(win_rate)}]")
    print(f"    최근 {total}건 기준  (성공 {successes} / 실패 {total - successes})")

    # 3. Drift 감지
    drift_str = "YES [!] -> 성능 하락 추세 (RL 결과 재확인 권장)" if drift else "NO      정상"
    print(f" Drift      : {drift_str}")

    if history:
        wr_trend = " -> ".join(f"{v*100:.0f}%" for v in history[-5:])
        print(f"    최근 추세  : {wr_trend}")

    print()

    # 4. Action 분포
    print(f" Action 분포 (최근 {total}건):")
    if action_counts:
        for action, cnt in action_counts.most_common():
            ratio = cnt / total if total > 0 else 0
            bar   = _bar(ratio, 15)
            print(f"    {action:<22} {bar} {cnt:3}건 ({ratio*100:.0f}%)")
    else:
        print("    (데이터 없음)")

    print()

    # 5. Q-table Best Actions
    print(" Q-table Best Actions:")
    if qt:
        for state, actions in sorted(qt.items()):
            if not actions:
                continue
            best_a = max(actions, key=lambda a: actions[a])
            best_q = actions[best_a]
            n      = counts.get(state, {}).get(best_a, 0)
            conf   = "[OK]" if best_q >= 3.0 and n >= 5 else "[  ]"
            print(f"  {conf} {state:<28} -> {best_a} (Q={best_q:.2f}, n={n})")
    else:
        print("    (학습 데이터 없음 -- shadow_rl_engine.py 실행 필요)")

    print()

    # 6. Baseline 요약
    bl = baseline.get("baseline", {})
    if bl:
        print(" Baseline (action별 latency p50):")
        for action, stats in bl.items():
            p50 = stats.get("latency_ms", {}).get("p50", "?")
            p95 = stats.get("latency_ms", {}).get("p95", "?")
            n   = stats.get("latency_ms", {}).get("n", 0)
            print(f"    {action:<22} p50={p50}ms  p95={p95}ms  n={n}")
    else:
        print(" Baseline: (없음 -- baseline_calculator.py 실행 필요)")

    print("=" * W)
    print()


if __name__ == "__main__":
    render()
