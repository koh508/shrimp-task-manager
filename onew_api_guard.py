"""
onew_api_guard.py — API 충돌 방지 및 속도 제한
────────────────────────────────────────────────
- 동시 Gemini 호출 최대 2개로 제한 (Semaphore)
- 분당 최대 호출 수 제한 (Rate Limiter)
- 배경 작업용 / 대화용 별도 채널 (대화 우선)
"""
import threading
import time
from collections import deque

# 동시 호출 제한
_CONVERSATION_SLOTS = 2   # 대화용 슬롯 (항상 여유 확보)
_BACKGROUND_SLOTS   = 1   # 배경 작업 동시 실행 최대 1개

_bg_semaphore   = threading.Semaphore(_BACKGROUND_SLOTS)
_conv_semaphore = threading.Semaphore(_CONVERSATION_SLOTS)

# 분당 호출 제한
_RATE_LIMIT_PER_MIN = 20       # 전체 분당 최대 호출
_call_times: deque  = deque()  # 최근 호출 타임스탬프
_rate_lock          = threading.Lock()


def _check_rate_limit(timeout: float = 30.0) -> bool:
    """
    분당 호출 한도 체크. 한도 초과 시 슬롯이 날 때까지 대기.
    timeout 초 내 슬롯 없으면 False 반환.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        with _rate_lock:
            now = time.time()
            # 1분 지난 기록 제거
            while _call_times and now - _call_times[0] > 60:
                _call_times.popleft()
            if len(_call_times) < _RATE_LIMIT_PER_MIN:
                _call_times.append(now)
                return True
        time.sleep(1)
    return False


def guarded_call(generate_fn, prompt: str, is_background: bool = True) -> str:
    """
    generate_fn을 안전하게 호출.
    - is_background=True: 배경 작업용 (동시 1개, 분당 제한 적용)
    - is_background=False: 대화용 (동시 2개, 제한 완화)
    """
    if is_background:
        acquired = _bg_semaphore.acquire(timeout=60)
        if not acquired:
            return ''
        try:
            if not _check_rate_limit():
                return ''
            return generate_fn(prompt)
        finally:
            _bg_semaphore.release()
    else:
        # 대화용: rate limit만 체크, semaphore 없음
        _check_rate_limit(timeout=10)
        return generate_fn(prompt)


def make_bg_generate_fn(generate_fn):
    """
    배경 모듈에 넘길 generate_fn 래퍼 반환.
    기존 코드 변경 없이 generate_fn 교체만으로 적용.
    """
    def _wrapped(prompt: str) -> str:
        return guarded_call(generate_fn, prompt, is_background=True)
    return _wrapped


def make_conv_generate_fn(generate_fn):
    """대화용 generate_fn 래퍼"""
    def _wrapped(prompt: str) -> str:
        return guarded_call(generate_fn, prompt, is_background=False)
    return _wrapped
