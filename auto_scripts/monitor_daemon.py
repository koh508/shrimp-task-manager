"""
온유 시스템 모니터링 데몬 (monitor_daemon.py)
스킬: proactive_monitoring.md

Windows Task Scheduler에 등록하여 주기적으로 실행.
이상 감지 시 SYSTEM/alerts.json에 기록 → 온유 시작 시 읽기.

설정 방법 (관리자 권한 PowerShell):
  schtasks /create /tn "OnewMonitor" /tr "python SYSTEM/auto_scripts/monitor_daemon.py" ^
    /sc daily /st 09:00 /ru SYSTEM
"""
import json
import shutil
import os
from pathlib import Path
from datetime import datetime

SYSTEM_DIR  = Path(__file__).parent.parent
VAULT_DIR   = SYSTEM_DIR.parent
ALERTS_FILE = SYSTEM_DIR / "alerts.json"
LOGS_DIR    = SYSTEM_DIR / "logs"

# ── 임계치 ───────────────────────────────────────────────────────────────────
DISK_WARN_GB    = 10.0
LOG_WARN_MB     = 5.0
VAULT_MAX_MB    = 500.0


def check_disk() -> list[dict]:
    alerts = []
    usage  = shutil.disk_usage(VAULT_DIR)
    free_gb = usage.free / (1024 ** 3)
    if free_gb < DISK_WARN_GB:
        alerts.append({
            "level":   "WARN",
            "time":    datetime.now().isoformat(),
            "message": f"C: 드라이브 잔여량 {free_gb:.1f}GB - 정리 권장",
            "action":  "disk_cleanup",
        })
    return alerts


def check_logs() -> list[dict]:
    alerts = []
    if not LOGS_DIR.exists():
        return alerts
    for f in LOGS_DIR.iterdir():
        if not f.is_file():
            continue
        mb = f.stat().st_size / (1024 * 1024)
        if mb > LOG_WARN_MB:
            alerts.append({
                "level":   "WARN",
                "time":    datetime.now().isoformat(),
                "message": f"로그 파일 '{f.name}' {mb:.1f}MB 초과 - 로테이션 권장",
                "action":  "log_rotate",
            })
    return alerts


def check_vault_size() -> list[dict]:
    alerts = []
    total_bytes = sum(f.stat().st_size for f in VAULT_DIR.rglob("*.md"))
    total_mb    = total_bytes / (1024 * 1024)
    if total_mb > VAULT_MAX_MB:
        alerts.append({
            "level":   "INFO",
            "time":    datetime.now().isoformat(),
            "message": f"Vault .md 총 크기 {total_mb:.0f}MB - 정상 범위 초과",
            "action":  "none",
        })
    return alerts


def load_existing_alerts() -> list[dict]:
    if not ALERTS_FILE.exists():
        return []
    try:
        return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_alerts(alerts: list[dict]) -> None:
    ALERTS_FILE.write_text(
        json.dumps(alerts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_checks() -> list[dict]:
    new_alerts: list[dict] = []
    new_alerts.extend(check_disk())
    new_alerts.extend(check_logs())
    new_alerts.extend(check_vault_size())
    return new_alerts


if __name__ == "__main__":
    existing = load_existing_alerts()
    new      = run_checks()

    if new:
        # 기존 알림에 추가 (중복 메시지 제거)
        existing_msgs = {a["message"] for a in existing}
        unique_new    = [a for a in new if a["message"] not in existing_msgs]
        all_alerts    = existing + unique_new
        save_alerts(all_alerts)
        print(f"[MonitorDaemon] {len(unique_new)}개 새 알림 기록: {ALERTS_FILE}")
        for a in unique_new:
            print(f"  [{a['level']}] {a['message']}")
    else:
        print("[MonitorDaemon] 이상 없음.")
        # 기존 알림 초기화 (정상 시)
        if existing:
            save_alerts([])
            print(f"  기존 알림 {len(existing)}개 클리어")
