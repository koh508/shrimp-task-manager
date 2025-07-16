#!/usr/bin/env python3
"""
자동 백업 및 복원 시스템
"""
import json
import logging
import os
import shutil
import tarfile
import time
from datetime import datetime

import schedule


class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        self.max_backups = 30
        self.backup_files = [
            "config.json",
            "monitoring_report.json",
            "alerts.json",
            "security_audit.log",
        ]
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        with tarfile.open(backup_path, "w:gz") as tar:
            for file in self.backup_files:
                if os.path.exists(file):
                    tar.add(file)
            system_state = {
                "backup_time": datetime.now().isoformat(),
                "version": "1.0.0",
                "files_backed_up": self.backup_files,
            }
            with open("system_state.json", "w", encoding="utf-8") as f:
                json.dump(system_state, f, ensure_ascii=False)
            tar.add("system_state.json")
            os.remove("system_state.json")
        self.cleanup_old_backups()
        logging.info(f"백업 생성 완료: {backup_filename}")
        return backup_path

    def cleanup_old_backups(self):
        backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("backup_")]
        backup_files.sort(reverse=True)
        for old_backup in backup_files[self.max_backups :]:
            old_path = os.path.join(self.backup_dir, old_backup)
            os.remove(old_path)
            logging.info(f"오래된 백업 삭제: {old_backup}")

    def restore_backup(self, backup_filename: str) -> bool:
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            logging.error(f"백업 파일 없음: {backup_filename}")
            return False
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall()
            logging.info(f"백업 복원 완료: {backup_filename}")
            return True
        except Exception as e:
            logging.error(f"백업 복원 실패: {e}")
            return False

    def schedule_backups(self):
        schedule.every().day.at("00:00").do(self.create_backup)
        while True:
            schedule.run_pending()
            time.sleep(60)
