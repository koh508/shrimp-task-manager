#!/usr/bin/env python3
"""
통합 시스템 실행 스크립트 (수정 버전)
"""
import sys
import os
from datetime import datetime

# 스크립트의 디렉토리로 작업 디렉토리 변경
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


def print_banner():
    """시스템 배너 출력"""
    print("통합 개발 시스템")
    print("=" * 40)
    print("안정성 | 확장성 | 성능 | 사용성")
    print("=" * 40)

def show_menu():
    """메뉴 표시"""
    print("\n실행 옵션:")
    print("1. 전체 테스트")
    print("2. 안정성 모니터링")
    print("3. 백업 시스템")
    print("4. 플러그인 시스템")
    print("5. 통합 개발 시스템")
    print("6. 대시보드 (수정 버전)")
    print("-" * 20)
    print("7. 옵시디언 모니터 실행")
    print("8. WindSurf 통합 테스트")
    print("9. 자체 진화 에이전트 테스트")
    print("-" * 20)
    print("10. [통합] 자동 클리핑 및 진화 시스템 (구현 예정)")
    print("0. 종료")

def run_script(script_name):
    """스크립트 실행 및 파일 존재 여부 확인"""
    if not os.path.exists(script_name):
        print(f"오류: '{script_name}' 파일을 찾을 수 없습니다.")
        print("   먼저 모든 필수 파일을 생성했는지 확인하세요.")
        return
    os.system(f"python {script_name}")

def check_system_status():
    """시스템 상태 확인"""
    print("\n시스템 상태 확인:")
    
    important_files = [
        'comprehensive_test.py',
        'stability_monitor_fixed.py',
        'backup_system_fixed.py',
        'plugin_system.py',
        'integrated_development_system.py',
        'simple_dashboard_fixed.py',
        'obsidian_monitor.py',
        'windsurf_integration.py',
        'self_evolving_agent.py'
    ]
    
    print(f"\n중요 파일 상태:")
    all_present = True
    for file in important_files:
        if os.path.exists(file):
            print(f"   [OK] {file}")
        else:
            print(f"   [!!] {file}")
            all_present = False
    
    if all_present:
        print("\n모든 중요 시스템 파일이 존재합니다.")
    else:
        print("\n일부 중요 파일이 누락되었습니다. 먼저 파일을 생성하세요.")
    
    return all_present

def main():
    """메인 실행 함수"""
    print_banner()
    
    system_ok = check_system_status()
    
    if not system_ok:
        print("\n경고: 시스템이 불안정합니다. 일부 기능이 동작하지 않을 수 있습니다.")
    
    while True:
        show_menu()
        
        try:
            choice = input("\n선택하세요 (0-10): ").strip()
            
            if choice == "0":
                print("시스템 종료")
                break
            elif choice == "1":
                run_script('comprehensive_test.py')
            elif choice == "2":
                run_script('stability_monitor_fixed.py')
            elif choice == "3":
                run_script('backup_system_fixed.py')
            elif choice == "4":
                run_script('plugin_system.py')
            elif choice == "5":
                run_script('integrated_development_system.py')
            elif choice == "6":
                run_script('simple_dashboard_fixed.py')
            elif choice == "7":
                run_script('obsidian_monitor.py')
            elif choice == "8":
                run_script('windsurf_integration.py')
            elif choice == "9":
                run_script('self_evolving_agent.py')
            elif choice == "10":
                print("이 기능은 아직 구현되지 않았습니다.")
            else:
                print("잘못된 선택입니다. 0-10 사이의 숫자를 입력하세요.")
            
            print("\n" + "="*50)
            
        except KeyboardInterrupt:
            print("\n시스템 종료")
            break
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
