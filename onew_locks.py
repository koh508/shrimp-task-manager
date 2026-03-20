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
    """JSON을 .tmp 파일에 쓰고 os.replace로 원자적으로 교체.
    쓰는 도중 프로세스가 죽어도 기존 파일은 손상되지 않음."""
    lock = _get_file_lock(filepath)
    with lock:
        tmp = filepath + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, filepath)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise


def _atomic_md_append(filepath: str, content: str):
    """마크다운 파일에 내용을 안전하게 추가 (Lock 보호)."""
    lock = _get_file_lock(filepath)
    with lock:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
