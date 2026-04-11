"""
onew_shared/git_sync.py
코드 변경 자동 git 커밋 — PC/태블릿 공통

사용법:
    python git_sync.py            # 1회 커밋
    python git_sync.py --watch    # 변경 감지 시 자동 커밋 (30분 간격)

PC: python onew_shared/git_sync.py --watch &
태블릿: Termux cron에 등록
  */30 * * * * cd ~/storage/shared/Documents/Obsidian\ Vault/SYSTEM && python onew_shared/git_sync.py
"""
import argparse
import subprocess
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

from .config import get_system_path, get_device_name

log = logging.getLogger(__name__)

REPO_PATH = get_system_path()
COMMIT_INTERVAL = 30 * 60  # 30분


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    """git 명령 실행. (returncode, output) 반환."""
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def ensure_git_repo(path: Path) -> bool:
    """git 저장소가 없으면 초기화."""
    if not (path / ".git").exists():
        code, out = _run(["git", "init"], path)
        if code != 0:
            log.error("git init 실패: %s", out)
            return False
        # 기본 .gitignore 생성
        gitignore = path / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(
                "__pycache__/\n*.pyc\n*.pyo\n*.session\n"
                "lancedb/\nonew_lance_db/\nlogs/\n"
                "*.json.tmp\ndb_backup/\ncode_backup/\n",
                encoding="utf-8",
            )
        _run(["git", "add", ".gitignore"], path)
        _run(["git", "commit", "-m", "init: onew_shared git 저장소 초기화"], path)
        log.info("git 저장소 초기화 완료: %s", path)
    return True


def has_changes(path: Path) -> bool:
    """커밋되지 않은 변경이 있는지 확인."""
    code, out = _run(["git", "status", "--porcelain"], path)
    return code == 0 and bool(out.strip())


def commit(path: Path, message: str = "") -> bool:
    """변경된 파일 전체 커밋. 변경 없으면 스킵."""
    if not has_changes(path):
        return False

    if not message:
        device = get_device_name()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"auto({device}): {now}"

    _run(["git", "add", "-A"], path)
    code, out = _run(["git", "commit", "-m", message], path)
    if code == 0:
        log.info("[git] 커밋 완료: %s", message)
        return True
    else:
        log.warning("[git] 커밋 실패: %s", out)
        return False


def watch(path: Path, interval: int = COMMIT_INTERVAL):
    """주기적으로 변경 감지 후 자동 커밋."""
    print(f"[git-sync] {get_device_name()} 자동 커밋 감시 시작 ({interval//60}분 간격)")
    print(f"[git-sync] 경로: {path}")
    while True:
        try:
            if commit(path):
                print(f"[git-sync] 커밋 완료 — {datetime.now().strftime('%H:%M')}")
        except Exception as e:
            log.error("[git-sync] 오류: %s", e)
        time.sleep(interval)


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="온유 코드 자동 git 커밋")
    parser.add_argument("--watch", action="store_true", help="변경 감지 자동 커밋 모드")
    parser.add_argument("--interval", type=int, default=30, help="커밋 간격 (분, 기본 30)")
    parser.add_argument("--message", "-m", default="", help="커밋 메시지")
    args = parser.parse_args()

    path = REPO_PATH
    if not ensure_git_repo(path):
        sys.exit(1)

    if args.watch:
        watch(path, interval=args.interval * 60)
    else:
        changed = commit(path, message=args.message)
        if not changed:
            print("[git-sync] 변경 없음 — 커밋 스킵")


if __name__ == "__main__":
    main()
