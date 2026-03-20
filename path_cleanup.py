"""
path_cleanup.py — 온유 코드 안전 환경 유틸리티
- 핵심 .py 파일 MD5 체크섬 저장/검증
- 수정 금지 구역(파일 목록) 관리
- 오래된 임시 파일 정리
"""
import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKSUM_FILE = os.path.join(SYSTEM_DIR, "file_checksums.json")

# 수정 금지 구역 (손상 시 시스템 전체 불능)
PROTECTED_FILES = [
    "onew_pure_db.json",
    "onew_location.json",
    "telegram_allowed_ids.json",
    "onew_budget.py",
]

# 체크섬 추적 대상 (핵심 코드 파일)
TRACKED_FILES = [
    "obsidian_agent.py",
    "onew_telegram_bot.py",
    "onew_task_manager.py",
    "onew_watcher.py",
    "onew_night_study.py",
    "onew_adhd_coach.py",
    "path_cleanup.py",
]


def _md5(filepath: str) -> str:
    """파일 MD5 해시 반환."""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return ""


def save_checksums() -> str:
    """현재 추적 파일들의 MD5 체크섬을 저장 (베이스라인 생성)."""
    checksums = {}
    for fname in TRACKED_FILES:
        fpath = os.path.join(SYSTEM_DIR, fname)
        if os.path.exists(fpath):
            checksums[fname] = {
                "md5": _md5(fpath),
                "size": os.path.getsize(fpath),
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
    with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
        json.dump(checksums, f, ensure_ascii=False, indent=2)
    return f"✅ 체크섬 저장 완료: {len(checksums)}개 파일 → file_checksums.json"


def verify_checksums() -> str:
    """저장된 체크섬과 현재 파일을 비교하여 변경된 파일 보고."""
    if not os.path.exists(CHECKSUM_FILE):
        return "⚠️ 체크섬 파일 없음. save_checksums()를 먼저 실행하세요."

    with open(CHECKSUM_FILE, "r", encoding="utf-8") as f:
        saved = json.load(f)

    results = []
    for fname, info in saved.items():
        fpath = os.path.join(SYSTEM_DIR, fname)
        if not os.path.exists(fpath):
            results.append(f"❌ {fname}: 파일 없음 (삭제됨?)")
            continue
        current_md5 = _md5(fpath)
        if current_md5 != info["md5"]:
            results.append(f"⚠️ {fname}: 변경됨 (저장: {info['md5'][:8]}… → 현재: {current_md5[:8]}…)")
        else:
            results.append(f"✅ {fname}: 이상 없음")

    return "\n".join(results)


def is_protected(filepath: str) -> bool:
    """수정 금지 구역 파일인지 확인."""
    return Path(filepath).name in PROTECTED_FILES


def cleanup_temp_files() -> str:
    """SYSTEM 폴더 내 임시/잔여 파일 정리 (.tmp, .bak, stop.flag 등)."""
    removed = []
    patterns = ["*.tmp", "*.bak", "stop.flag"]
    for pattern in patterns:
        for f in Path(SYSTEM_DIR).glob(pattern):
            try:
                f.unlink()
                removed.append(f.name)
            except Exception as e:
                removed.append(f"{f.name} (실패: {e})")

    if removed:
        return f"🧹 정리 완료: {', '.join(removed)}"
    return "🧹 정리할 임시 파일 없음"


def check_backup_age() -> str:
    """code_backup 폴더의 최근 백업 날짜 확인."""
    backup_base = Path(r"C:\Users\User\AppData\Local\onew\code_backup")
    if not backup_base.exists():
        return "⚠️ 백업 폴더 없음"
    date_dirs = sorted([d for d in backup_base.iterdir() if d.is_dir()], reverse=True)
    if not date_dirs:
        return "⚠️ 백업 없음"
    latest = date_dirs[0].name
    files = list(date_dirs[0].glob("*.py"))
    return f"📦 최근 백업: {latest} ({len(files)}개 파일)"


def run_all_checks() -> str:
    """전체 안전 점검 실행 (체크섬 + 백업 현황 + 임시파일)."""
    lines = [
        "=" * 50,
        "🔍 온유 코드 안전 점검",
        "=" * 50,
        "",
        "[ 체크섬 검증 ]",
        verify_checksums(),
        "",
        "[ 백업 현황 ]",
        check_backup_age(),
        "",
        "[ 임시 파일 정리 ]",
        cleanup_temp_files(),
        "=" * 50,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "save":
        print(save_checksums())
    elif cmd == "verify":
        print(verify_checksums())
    elif cmd == "cleanup":
        print(cleanup_temp_files())
    else:
        print(run_all_checks())
