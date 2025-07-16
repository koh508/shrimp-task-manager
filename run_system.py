#!/usr/bin/env python3
"""
통합 시스템 실행 스크립트 (간결 버전)
"""
import asyncio
import os
import sys
from datetime import datetime


def print_banner():
    """시스템 배너 출력"""
    print("🚀 통합 개발 시스템")
    print("=" * 40)
    print("🛡️ 안정성 | 🔧 확장성 | ⚡ 성능 | 🎨 사용성")
    print("=" * 40)


def show_menu():
    """메뉴 표시"""
    print("\n📋 실행 옵션:")
    print("1. 🧪 전체 테스트")
    print("2. 🛡️ 안정성 모니터링")
    print("3. 💾 백업 시스템")
    print("4. 🔌 플러그인 시스템")
    print("5. ⚡ 성능 최적화")
    print("6. 🎨 대시보드")
    print("7. 🚀 통합 시스템")
    print("0. 종료")


def run_test():
    """테스트 실행"""
    print("🧪 전체 테스트 실행 중...")
    os.system("python comprehensive_test.py")


def run_stability_monitor():
    """안정성 모니터 실행"""
    print("🛡️ 안정성 모니터 실행 중...")
    os.system("python stability_monitor_fixed.py")


def run_backup_system():
    """백업 시스템 실행"""
    print("💾 백업 시스템 실행 중...")
    os.system("python backup_system_fixed.py")


def run_plugin_system():
    """플러그인 시스템 실행"""
    print("🔌 플러그인 시스템 실행 중...")
    os.system("python plugin_system.py")


def run_performance_optimizer():
    """성능 최적화 실행"""
    print("⚡ 성능 최적화 실행 중...")
    os.system("python performance_optimizer.py")


def run_dashboard():
    """대시보드 실행"""
    print("🎨 대시보드 실행 중...")
    os.system("python simple_dashboard.py")


def run_integrated_system():
    """통합 시스템 실행"""
    print("🚀 통합 시스템 실행 중...")
    os.system("python integrated_development_system.py")


def main():
    """메인 실행 함수"""
    print_banner()

    # 시스템 상태 확인
    required_files = [
        "comprehensive_test.py",
        "stability_monitor_fixed.py",
        "backup_system_fixed.py",
        "plugin_system.py",
        "performance_optimizer.py",
        "simple_dashboard.py",
        "integrated_development_system.py",
    ]

    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ 누락된 파일: {', '.join(missing_files)}")
        return

    print("✅ 모든 시스템 파일 확인 완료")

    # 메뉴 루프
    while True:
        show_menu()

        try:
            choice = input("\n선택하세요 (0-7): ").strip()

            if choice == "0":
                print("👋 시스템 종료")
                break
            elif choice == "1":
                run_test()
            elif choice == "2":
                run_stability_monitor()
            elif choice == "3":
                run_backup_system()
            elif choice == "4":
                run_plugin_system()
            elif choice == "5":
                run_performance_optimizer()
            elif choice == "6":
                run_dashboard()
            elif choice == "7":
                run_integrated_system()
            else:
                print("❌ 잘못된 선택입니다. 0-7 사이의 숫자를 입력하세요.")

            print("\n" + "=" * 40)

        except KeyboardInterrupt:
            print("\n👋 시스템 종료")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
