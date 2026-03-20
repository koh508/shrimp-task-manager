"""
test_canary.py — 실환경 검증 (Canary Test)

실제 DB/파일 시스템 1회 최소 접근 → 즉시 원상복구 보장.
Mock과 실제 환경 차이 제거.

실행: python -m pytest test_canary.py -v
"""
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import onew_self_improve as si

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))


# ==============================================================================
# [파일 시스템 실환경]
# ==============================================================================
def test_canary_json_write_read_rollback():
    """실제 JSON 파일 1회 쓰기 → 검증 → 즉시 삭제."""
    test_file = os.path.join(SYSTEM_DIR, "_canary_json.json")
    try:
        data = {"canary": True, "ts": time.time()}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        assert os.path.exists(test_file)
        with open(test_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["canary"] is True
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
        assert not os.path.exists(test_file), "정리 실패 — rollback 보장 안됨"


def test_canary_atomic_replace():
    """os.replace 원자적 교체 실환경 검증 — 중간 실패 시 원본 보호."""
    test_file = os.path.join(SYSTEM_DIR, "_canary_atomic.json")
    tmp_file  = test_file + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump({"atomic": True}, f)
        os.replace(tmp_file, test_file)
        assert os.path.exists(test_file)
        assert not os.path.exists(tmp_file), ".tmp 파일 잔존 — 원자성 깨짐"
    finally:
        for f in [test_file, tmp_file]:
            if os.path.exists(f):
                os.remove(f)


def test_canary_backup_and_rollback():
    """SafetyGate.backup() + rollback() 실환경 검증."""
    test_file = os.path.join(SYSTEM_DIR, "_canary_backup.py")
    original  = "# canary original\nprint('original')\n"
    modified  = "# canary modified\nprint('modified')\n"
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(original)

        backup_path = si.SafetyGate.backup(test_file)
        assert not backup_path.startswith("ERROR"), f"백업 실패: {backup_path}"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(modified)
        assert "modified" in open(test_file).read()

        rolled = si.SafetyGate.rollback(test_file)
        assert rolled, "rollback() 실패"
        assert "original" in open(test_file).read(), "롤백 후 내용 불일치"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_canary_syntax_verify_real_file():
    """SafetyGate.verify_syntax() 실파일 문법 검사."""
    # 정상 파일
    ok, err = si.SafetyGate.verify_syntax(
        os.path.join(SYSTEM_DIR, "onew_self_improve.py"))
    assert ok, f"정상 파일 문법 오류: {err}"

    # 오류 파일
    bad_file = os.path.join(SYSTEM_DIR, "_canary_bad.py")
    try:
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("def broken(\n")
        ok, err = si.SafetyGate.verify_syntax(bad_file)
        assert not ok, "문법 오류 파일을 통과시킴"
    finally:
        if os.path.exists(bad_file):
            os.remove(bad_file)


# ==============================================================================
# [Race Condition — 실환경 동시 쓰기]
# ==============================================================================
def test_canary_concurrent_atomic_write():
    """5개 스레드 동시 atomic write — Race Condition 실환경 검증.

    Windows: os.replace() 동시 경합 시 WinError 5 (Access Denied) 발생 가능.
    이는 OS 수준 정상 동작 — 데이터 손상(partial write) 없음이 핵심 보장.
    검증 기준: 최소 1개 성공 + 최종 파일 내용이 유효한 JSON.
    """
    test_file = os.path.join(SYSTEM_DIR, "_canary_race.json")
    errors    = []
    results   = []

    def worker(i):
        try:
            tmp = test_file + f".tmp{i}"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"worker": i}, f)
            os.replace(tmp, test_file)
            results.append(i)
        except Exception as e:
            errors.append(f"worker{i}: {e}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    try:
        # Windows는 동시 os.replace() 경합 시 일부 WinError 5 발생 — 정상
        assert len(results) >= 1, f"모든 워커 실패 — 쓰기 불가: {errors}"
        assert os.path.exists(test_file), "최종 파일 없음"
        # 파일 내용 무결성 검증 (partial write 없음)
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "worker" in data, f"파일 내용 손상: {data}"
    finally:
        for i in range(5):
            tmp = test_file + f".tmp{i}"
            if os.path.exists(tmp): os.remove(tmp)
        if os.path.exists(test_file): os.remove(test_file)


# ==============================================================================
# [Timeout — 실환경 응답 시간]
# ==============================================================================
def test_canary_file_write_timeout():
    """파일 쓰기가 1초 이내 완료되어야 함."""
    test_file = os.path.join(SYSTEM_DIR, "_canary_timeout.json")
    try:
        start = time.time()
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"timeout_test": True}, f)
        elapsed = time.time() - start
        assert elapsed < 1.0, f"파일 쓰기 {elapsed:.2f}s 초과 — I/O 병목"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_canary_circuit_breaker_file_io():
    """CircuitBreaker 블랙리스트 파일 I/O 실환경 — 0.5s 이내."""
    cb    = si.CircuitBreaker()
    start = time.time()
    cb._load()
    elapsed = time.time() - start
    assert elapsed < 0.5, f"CircuitBreaker._load() {elapsed:.3f}s 초과"
