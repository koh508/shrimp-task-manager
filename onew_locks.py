"""
onew_locks.py — 파일 충돌 방지 / 원자적 쓰기

Strangler Fig Step 1:
  obsidian_agent.py에서 분리 예정인 파일 잠금 유틸리티.
  현재 obsidian_agent.py는 동일 코드를 자체 보유 (중복) — Step 2에서 import로 교체.

제공:
  _get_file_lock(filepath)    → threading.Lock (파일별 캐시)
  _atomic_json_write(fp, d)   → .tmp → os.replace (원자적 교체)
  _atomic_md_append(fp, c)    → Lock 보호 append
"""
import json
import os
import threading
import time

# WinError 5 (Access Denied) 재시도 설정
_RETRY_MAX     = 4      # 최대 재시도 횟수
_RETRY_BASE    = 0.05   # 초기 대기 (초): 0.05 → 0.1 → 0.2 → 0.4
_WINERROR_5    = 5      # Windows Access Denied errno

# 파일 경로별 Lock 캐시
_FILE_LOCKS: dict = {}
_FILE_LOCKS_META = threading.Lock()  # Lock 캐시 자체 보호


def _get_file_lock(filepath: str) -> threading.Lock:
    """파일별 전용 Lock 반환 (없으면 생성)."""
    with _FILE_LOCKS_META:
        if filepath not in _FILE_LOCKS:
            _FILE_LOCKS[filepath] = threading.Lock()
        return _FILE_LOCKS[filepath]


def _atomic_json_write(filepath: str, data: dict | list):
    """JSON을 .tmp → os.replace로 원자적 교체.

    Windows WinError 5 (Access Denied) 발생 시 지수 백오프 재시도:
      1회차: 0.05s, 2회차: 0.10s, 3회차: 0.20s, 4회차: 0.40s
    모든 재시도 소진 시 예외 전파.
    """
    lock = _get_file_lock(filepath)
    with lock:
        tmp = filepath + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise

        # os.replace — WinError 5 재시도
        last_exc = None
        for attempt in range(_RETRY_MAX + 1):
            try:
                os.replace(tmp, filepath)
                return  # 성공
            except OSError as e:
                if getattr(e, "winerror", None) == _WINERROR_5 and attempt < _RETRY_MAX:
                    last_exc = e
                    time.sleep(_RETRY_BASE * (2 ** attempt))
                else:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                    raise
        # 여기까지 오면 모든 재시도 소진
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise last_exc  # type: ignore[misc]


def _atomic_md_append(filepath: str, content: str):
    """마크다운 파일에 내용을 안전하게 추가 (Lock + WinError 5 재시도)."""
    lock = _get_file_lock(filepath)
    with lock:
        last_exc = None
        for attempt in range(_RETRY_MAX + 1):
            try:
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(content)
                return
            except OSError as e:
                if getattr(e, "winerror", None) == _WINERROR_5 and attempt < _RETRY_MAX:
                    last_exc = e
                    time.sleep(_RETRY_BASE * (2 ** attempt))
                else:
                    raise
        raise last_exc  # type: ignore[misc]
