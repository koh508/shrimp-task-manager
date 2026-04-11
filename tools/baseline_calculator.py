"""
baseline_calculator.py — Phase 12.5

metrics_log.jsonl 를 읽어 action별 기준선(baseline) 통계를 계산하고
SYSTEM/baseline.json 에 저장한다.

실행: python baseline_calculator.py [--min N]
  --min N : 기준선 계산에 필요한 최소 샘플 수 (기본 5)
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

SYSTEM_DIR   = Path(__file__).parent.parent
LOG_FILE     = SYSTEM_DIR / "metrics_log.jsonl"
BASELINE_OUT = SYSTEM_DIR / "baseline.json"


def _load_log() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    records = []
    for line in LOG_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def _stats(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "p50": None, "p90": None}
    mean = sum(values) / n
    std  = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0
    sv   = sorted(values)
    p50  = sv[int(n * 0.5)]
    p90  = sv[min(int(n * 0.9), n - 1)]
    p95  = sv[min(int(n * 0.95), n - 1)]
    return {"n": n, "mean": round(mean, 1), "std": round(std, 1),
            "p50": p50, "p90": p90, "p95": p95}


def calculate(min_samples: int = 5) -> dict:
    records = _load_log()
    if not records:
        print("metrics_log.jsonl 없거나 비어 있음.")
        return {}

    # action별 그룹
    groups: dict[str, dict[str, list]] = {}
    for r in records:
        action = r.get("action", "UNKNOWN")
        if action not in groups:
            groups[action] = {"latency_ms": [], "context_chars": [], "search_hits": [], "resp_chars": []}
        for key in ("latency_ms", "context_chars", "search_hits", "resp_chars"):
            val = r.get(key)
            if isinstance(val, (int, float)):
                groups[action][key].append(val)

    baseline = {}
    for action, data in groups.items():
        n = len(data["latency_ms"])
        if n < min_samples:
            print(f"  {action}: 샘플 {n}개 — 기준선 skip (최소 {min_samples}개 필요)")
            continue
        baseline[action] = {
            "latency_ms":    _stats(data["latency_ms"]),
            "context_chars": _stats(data["context_chars"]),
            "search_hits":   _stats(data["search_hits"]),
            "resp_chars":    _stats(data["resp_chars"]),
        }
        print(f"  {action}: n={n}, latency p50={baseline[action]['latency_ms']['p50']}ms")

    meta = {
        "_generated": datetime.now().isoformat(),
        "_total_records": len(records),
        "_min_samples": min_samples,
        "baseline": baseline,
    }
    BASELINE_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {BASELINE_OUT}")
    return meta


if __name__ == "__main__":
    min_n = 5
    if "--min" in sys.argv:
        idx = sys.argv.index("--min")
        try:
            min_n = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass
    calculate(min_n)
