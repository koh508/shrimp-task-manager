# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import time
import json
from datetime import datetime

class UltraSimpleCollector:
    def __init__(self):
        self.source_drive = "D:\\"
        self.target_repo = "D:\\my workspace\\OneDrive NEW\\GNY"
        self.batch_size = 10
        self.max_files = 1000

    def safe_git_commit(self, message):
        """안전한 Git 커밋"""
        try:
            os.chdir(self.target_repo)
            subprocess.run(["git", "add", "."], check=True, timeout=30)
            subprocess.run(["git", "commit", "-m", message], check=True, timeout=30)
            subprocess.run(["git", "push"], check=True, timeout=60)
            return True
        except:
            return False

    def collect_and_commit(self):
        """파일 수집 및 커밋"""
        print("🏥 어깨 수술 회복용 자동 수집기 시작")
        print("=" * 50)

        python_files = []
        file_count = 0

        for root, dirs, files in os.walk(self.source_drive):
            if file_count >= self.max_files:
                break

            dirs[:] = [d for d in dirs if not d.startswith(('.', '$', 'System', 'Windows'))]

            for file in files:
                if file_count >= self.max_files:
                    break

                if file.lower().endswith(('.py', '.pyw', '.ipynb')):
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) > 0:
                            python_files.append(file_path)
                            file_count += 1

                            if file_count % 100 == 0:
                                print(f"📄 {file_count}개 파일 발견...")
                    except:
                        continue

        print(f"✅ 총 {len(python_files)}개 파일 발견")

        target_dir = os.path.join(self.target_repo, "AutoCollected_Python")
        os.makedirs(target_dir, exist_ok=True)

        batch_count = 0
        for i in range(0, len(python_files), self.batch_size):
            batch = python_files[i:i + self.batch_size]
            batch_count += 1

            print(f"🔄 배치 {batch_count} 처리 중...")

            copied = 0
            for file_path in batch:
                try:
                    filename = os.path.basename(file_path)
                    target_path = os.path.join(target_dir, f"batch_{batch_count}_{filename}")
                    shutil.copy2(file_path, target_path)
                    copied += 1
                except:
                    continue

            print(f"  📁 {copied}개 파일 복사 완료")

            if copied > 0:
                if self.safe_git_commit(f"Auto batch {batch_count}: {copied} Python files"):
                    print(f"  ✅ 배치 {batch_count} 커밋 완료")
                else:
                    print(f"  ⚠️ 배치 {batch_count} 커밋 실패")

            time.sleep(1)

        print("\n🎉 자동 수집 완료!")
        print("💝 어깨 수술 회복에 집중하세요!")

def main():
    collector = UltraSimpleCollector()
    collector.collect_and_commit()

if __name__ == "__main__":
    main()
