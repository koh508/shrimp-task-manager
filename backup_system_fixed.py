#!/usr/bin/env python3
"""
백업 시스템 (수정 버전)
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BackupManager:
    """백업 관리자"""

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        # 백업할 파일들 (우선순위 순)
        self.backup_files = [
            # 설정 파일
            "config.json",
            "clipper_config.json",
            # 데이터 파일
            "health_report.json",
            "test_results.json",
            "integrated_system_data.json",
            # 핵심 시스템 파일
            "run_system.py",
            "simple_dashboard.py",
            "comprehensive_test.py",
            "stability_monitor_fixed.py",
            "backup_system_fixed.py",
            # 기타 중요 파일
            "debug_utils.py",
            "smoke_test.py",
        ]

        self.max_backups = 20  # 최대 백업 개수

    def create_backup(self, backup_type: str = "manual", description: str = "") -> Optional[str]:
        """백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)

            print(f"📦 백업 생성 시작: {backup_name}")
            logger.info(f"백업 생성 시작: {backup_name}")

            backed_up_files = []
            skipped_files = []

            # 파일 백업
            for file in self.backup_files:
                if os.path.exists(file):
                    try:
                        shutil.copy2(file, backup_path / file)
                        backed_up_files.append(file)
                        print(f"   ✅ {file}")
                    except Exception as e:
                        skipped_files.append(f"{file} (오류: {e})")
                        print(f"   ❌ {file} - {e}")
                else:
                    skipped_files.append(f"{file} (없음)")
                    print(f"   ⚠️ {file} (파일 없음)")

            # 추가 Python 파일 백업 (선택적)
            python_files = [
                f for f in os.listdir(".") if f.endswith(".py") and f not in self.backup_files
            ]
            additional_backup_count = 0

            for py_file in python_files[:10]:  # 최대 10개 추가 파일
                try:
                    shutil.copy2(py_file, backup_path / py_file)
                    backed_up_files.append(py_file)
                    additional_backup_count += 1
                except Exception as e:
                    logger.warning(f"추가 파일 백업 실패: {py_file} - {e}")

            # 백업 정보 저장
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "backup_type": backup_type,
                "description": description,
                "files_backed_up": backed_up_files,
                "skipped_files": skipped_files,
                "total_files": len(backed_up_files),
                "additional_files": additional_backup_count,
                "backup_size_bytes": self.calculate_backup_size(backup_path),
            }

            info_file = backup_path / "backup_info.json"
            with open(info_file, "w") as f:
                json.dump(backup_info, f, indent=2)

            print(f"✅ 백업 완료: {backup_name}")
            print(f"   📁 백업된 파일: {len(backed_up_files)}개")
            print(f"   📦 백업 크기: {backup_info['backup_size_bytes']/1024:.1f}KB")

            if skipped_files:
                print(f"   ⚠️ 건너뛴 파일: {len(skipped_files)}개")

            logger.info(f"백업 완료: {backup_name} ({len(backed_up_files)}개 파일)")

            # 오래된 백업 정리
            self.cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            logger.error(f"백업 실패: {e}")
            return None

    def calculate_backup_size(self, backup_path: Path) -> int:
        """백업 크기 계산"""
        try:
            total_size = 0
            for file in backup_path.iterdir():
                if file.is_file():
                    total_size += file.stat().st_size
            return total_size
        except Exception:
            return 0

    def cleanup_old_backups(self):
        """오래된 백업 정리"""
        try:
            backup_folders = [d for d in self.backup_dir.iterdir() if d.is_dir()]
            backup_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            removed_count = 0
            for old_backup in backup_folders[self.max_backups :]:
                shutil.rmtree(old_backup)
                removed_count += 1
                print(f"🗑️ 오래된 백업 삭제: {old_backup.name}")
                logger.info(f"오래된 백업 삭제: {old_backup.name}")

            if removed_count > 0:
                print(f"✅ {removed_count}개 오래된 백업 정리 완료")

        except Exception as e:
            print(f"⚠️ 백업 정리 오류: {e}")
            logger.error(f"백업 정리 오류: {e}")

    def list_backups(self) -> List[Dict]:
        """백업 목록 조회"""
        try:
            backup_folders = [d for d in self.backup_dir.iterdir() if d.is_dir()]
            backup_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            backups = []

            print(f"📋 백업 목록 ({len(backup_folders)}개):")
            print("-" * 50)

            for i, backup in enumerate(backup_folders, 1):
                info_file = backup / "backup_info.json"

                if info_file.exists():
                    try:
                        with open(info_file, "r") as f:
                            info = json.load(f)

                        backup_data = {
                            "name": backup.name,
                            "timestamp": info.get("timestamp", ""),
                            "type": info.get("backup_type", "unknown"),
                            "files_count": info.get("total_files", 0),
                            "size_bytes": info.get("backup_size_bytes", 0),
                            "description": info.get("description", ""),
                        }

                        backups.append(backup_data)

                        size_kb = backup_data["size_bytes"] / 1024
                        print(f"   {i:2d}. 📦 {backup.name}")
                        print(f"       📅 {backup_data['timestamp']}")
                        print(f"       📁 {backup_data['files_count']}개 파일 ({size_kb:.1f}KB)")
                        print(f"       🏷️ {backup_data['type']}")
                        if backup_data["description"]:
                            print(f"       📝 {backup_data['description']}")
                        print()

                    except Exception as e:
                        print(f"   {i:2d}. 📦 {backup.name} (정보 읽기 실패: {e})")
                        backups.append({"name": backup.name, "error": str(e)})
                else:
                    print(f"   {i:2d}. 📦 {backup.name} (정보 없음)")
                    backups.append({"name": backup.name, "error": "no_info"})

            return backups

        except Exception as e:
            print(f"❌ 백업 목록 조회 실패: {e}")
            logger.error(f"백업 목록 조회 실패: {e}")
            return []

    def restore_backup(self, backup_name: str) -> bool:
        """백업 복원"""
        try:
            backup_path = self.backup_dir / backup_name

            if not backup_path.exists():
                print(f"❌ 백업을 찾을 수 없음: {backup_name}")
                return False

            print(f"🔄 백업 복원 시작: {backup_name}")
            logger.info(f"백업 복원 시작: {backup_name}")

            # 현재 파일 비상 백업 생성
            emergency_backup = self.create_backup(
                "emergency_before_restore", f"복원 전 비상 백업 ({backup_name})"
            )
            if emergency_backup:
                print(f"💾 비상 백업 생성: {Path(emergency_backup).name}")

            # 파일 복원
            restored_files = []
            failed_files = []

            for file in backup_path.iterdir():
                if file.name == "backup_info.json":
                    continue

                try:
                    shutil.copy2(file, file.name)
                    restored_files.append(file.name)
                    print(f"   ✅ {file.name}")
                except Exception as e:
                    failed_files.append(f"{file.name} (오류: {e})")
                    print(f"   ❌ {file.name} - {e}")

            print(f"✅ 복원 완료: {len(restored_files)}개 파일 성공")

            if failed_files:
                print(f"⚠️ 복원 실패: {len(failed_files)}개 파일")
                for failed in failed_files:
                    print(f"   - {failed}")

            logger.info(f"복원 완료: {backup_name} ({len(restored_files)}개 파일)")

            return len(restored_files) > 0

        except Exception as e:
            print(f"❌ 복원 실패: {e}")
            logger.error(f"복원 실패: {e}")
            return False

    def get_backup_status(self) -> Dict:
        """백업 상태 조회"""
        try:
            backup_folders = [d for d in self.backup_dir.iterdir() if d.is_dir()]

            if not backup_folders:
                return {
                    "total_backups": 0,
                    "latest_backup": None,
                    "total_size_mb": 0,
                    "status": "no_backups",
                }

            # 최신 백업 정보
            latest_backup = max(backup_folders, key=lambda x: x.stat().st_mtime)

            # 전체 크기 계산
            total_size = 0
            for backup in backup_folders:
                try:
                    total_size += sum(f.stat().st_size for f in backup.iterdir() if f.is_file())
                except Exception:
                    pass

            # 최신 백업 정보 로드
            latest_info = {}
            info_file = latest_backup / "backup_info.json"
            if info_file.exists():
                try:
                    with open(info_file, "r") as f:
                        latest_info = json.load(f)
                except Exception:
                    pass

            return {
                "total_backups": len(backup_folders),
                "latest_backup": {
                    "name": latest_backup.name,
                    "timestamp": latest_info.get("timestamp", ""),
                    "type": latest_info.get("backup_type", "unknown"),
                    "files_count": latest_info.get("total_files", 0),
                },
                "total_size_mb": total_size / (1024 * 1024),
                "backup_directory": str(self.backup_dir),
                "status": "healthy",
            }

        except Exception as e:
            logger.error(f"백업 상태 조회 실패: {e}")
            return {"error": str(e), "status": "error"}


def main():
    """메인 실행 함수"""
    backup_manager = BackupManager()

    print("💾 백업 시스템")
    print("=" * 40)

    while True:
        print("\n📋 메뉴:")
        print("1. 백업 생성")
        print("2. 백업 목록 조회")
        print("3. 백업 복원")
        print("4. 백업 상태 조회")
        print("5. 자동 백업 생성")
        print("0. 종료")

        choice = input("\n선택하세요 (0-5): ").strip()

        if choice == "0":
            print("👋 백업 시스템 종료")
            break
        elif choice == "1":
            description = input("백업 설명 (선택사항): ").strip()
            backup_path = backup_manager.create_backup("manual", description)
            if backup_path:
                print(f"✅ 백업 생성 완료: {Path(backup_path).name}")
        elif choice == "2":
            backup_manager.list_backups()
        elif choice == "3":
            backups = backup_manager.list_backups()
            if backups:
                backup_name = input("\n복원할 백업 이름을 입력하세요: ").strip()
                if backup_name:
                    confirm = input(f"⚠️ '{backup_name}' 백업을 복원하시겠습니까? (y/N): ").strip().lower()
                    if confirm == "y":
                        backup_manager.restore_backup(backup_name)
                    else:
                        print("복원이 취소되었습니다.")
            else:
                print("복원할 백업이 없습니다.")
        elif choice == "4":
            status = backup_manager.get_backup_status()
            print(f"\n📊 백업 상태:")
            print(f"   총 백업: {status.get('total_backups', 0)}개")
            print(f"   총 크기: {status.get('total_size_mb', 0):.1f}MB")
            print(f"   상태: {status.get('status', 'unknown')}")

            if status.get("latest_backup"):
                latest = status["latest_backup"]
                print(f"   최신 백업: {latest['name']}")
                print(f"   타입: {latest['type']}")
                print(f"   파일 수: {latest['files_count']}개")
        elif choice == "5":
            print("🔄 자동 백업 생성 중...")
            backup_path = backup_manager.create_backup("auto", "자동 백업")
            if backup_path:
                print(f"✅ 자동 백업 완료: {Path(backup_path).name}")
        else:
            print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
