"""
metrics_collector.py — Phase 12.5 RL-Ready Metrics Collector

사용법:
    with MetricsContext(query, intent) as mc:
        # ... 파이프라인 처리 ...
        mc.set_action("ANSWER_RAG")
        mc.set_search_hits(len(chunks))
        mc.set_context_chars(len(context))
    # __exit__ 시 자동 로깅

로그 위치: SYSTEM/metrics_log.jsonl (append-only)
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

SYSTEM_DIR   = Path(__file__).parent.parent
LOG_FILE     = SYSTEM_DIR / "metrics_log.jsonl"


class MetricsContext:
    """
    handle_query() 전체를 감싸는 컨텍스트 매니저.
    with 블록 종료 시 JSONL에 한 줄 기록.
    """

    def __init__(self, query: str, intent: str = ""):
        self._qhash         = hashlib.md5(query.encode("utf-8", errors="replace")).hexdigest()[:8]
        self._intent        = intent
        self._action        = "UNKNOWN"
        self._search_hits   = 0
        self._context_chars = 0
        self._resp_chars    = 0
        self._is_success    = True
        self._error_type    = "NONE"
        self._degraded      = False
        self._t0            = None

    # ── setter ───────────────────────────────────────────────────────────────
    def set_action(self, action: str):
        self._action = action

    def set_search_hits(self, n: int):
        self._search_hits = n

    def set_context_chars(self, n: int):
        self._context_chars = n

    def set_resp_chars(self, n: int):
        self._resp_chars = n

    def set_intent(self, intent: str):
        self._intent = intent

    def set_is_success(self, v: bool):
        self._is_success = v

    def set_error_type(self, v: str):
        self._error_type = v

    def set_degraded(self, v: bool):
        self._degraded = v

    # ── context manager ───────────────────────────────────────────────────────
    def __enter__(self):
        self._t0 = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.monotonic() - self._t0) * 1000) if self._t0 is not None else 0
        record = {
            "ts":            datetime.now(timezone.utc).isoformat(),
            "qhash":         self._qhash,
            "intent":        self._intent,
            "action":        self._action,
            "search_hits":   self._search_hits,
            "context_chars": self._context_chars,
            "latency_ms":    latency_ms,
            "resp_chars":    self._resp_chars,
            "is_success":    self._is_success,
            "error_type":    self._error_type,
            "degraded":      self._degraded,
        }
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 로깅 실패가 파이프라인을 막으면 안 됨
        return False  # 예외 전파 유지


def tail_log(n: int = 20) -> list[dict]:
    """최근 n개 로그 항목 반환 (디버깅용)."""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text("utf-8").splitlines()
    result = []
    for line in lines[-n:]:
        try:
            result.append(json.loads(line))
        except Exception:
            pass
    return result
