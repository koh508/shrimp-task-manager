import os
import shutil
import glob
import subprocess
import time

def clear_vscode_cache():
    """VSCode 캐시 및 임시 파일들을 정리합니다."""
    
    print("VSCode 캐시 정리를 시작합니다...")
    
    # 삭제할 캐시 경로들
    cache_paths = [
        r"C:\Users\koko1\AppData\Roaming\Code\CachedExtensions",
        r"C:\Users\koko1\AppData\Roaming\Code\logs", 
        r"C:\Users\koko1\AppData\Roaming\Code\CachedExtensionVSIXs",
        r"C:\Users\koko1\AppData\Roaming\Code\User\workspaceStorage",
        r"C:\Users\koko1\AppData\Roaming\Code\User\globalStorage"
    ]
    
    # TEMP 폴더의 vscode 관련 파일들
    temp_path = os.path.expandvars(r"%TEMP%\vscode-*")
    
    deleted_count = 0
    
    # 일반 캐시 폴더들 삭제
    for path in cache_paths:
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"✓ 삭제됨: {path}")
                    deleted_count += 1
                elif os.path.isfile(path):
                    os.remove(path)
                    print(f"✓ 삭제됨: {path}")
                    deleted_count += 1
        except Exception as e:
            print(f"✗ 삭제 실패: {path} - {e}")
    
    # TEMP 폴더의 VSCode 관련 파일들
    try:
        temp_files = glob.glob(temp_path)
        for temp_file in temp_files:
            if os.path.isdir(temp_file):
                shutil.rmtree(temp_file, ignore_errors=True)
            elif os.path.isfile(temp_file):
                os.remove(temp_file)
            print(f"✓ 임시파일 삭제됨: {temp_file}")
            deleted_count += 1
    except Exception as e:
        print(f"✗ 임시파일 삭제 실패: {e}")
    
    print(f"\n캐시 정리 완료! {deleted_count}개 항목이 삭제되었습니다.")
    return deleted_count > 0

def kill_vscode_processes():
    """실행 중인 VSCode 프로세스를 종료합니다."""
    
    print("\nVSCode 프로세스를 종료하고 있습니다...")
    
    processes = ['Code.exe', 'code.exe']
    killed = False
    
    for process in processes:
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', process], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {process} 프로세스 종료됨")
                killed = True
        except Exception as e:
            print(f"✗ {process} 종료 실패: {e}")
    
    if killed:
        print("프로세스 종료 후 3초 대기...")
        time.sleep(3)
    
    return killed

def start_vscode_safe_mode(disable_extensions=True):
    """VSCode를 안전 모드로 시작합니다."""
    
    print(f"\nVSCode를 {'확장 프로그램 비활성화' if disable_extensions else '일반'} 모드로 시작합니다...")
    
    try:
        if disable_extensions:
            # 확장 프로그램 비활성화하고 메모리 제한 설정
            subprocess.Popen(['code', '--disable-extensions', '--max-memory=4096'])
        else:
            subprocess.Popen(['code'])
        
        print("✓ VSCode 시작됨")
        return True
    except Exception as e:
        print(f"✗ VSCode 시작 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    
    print("=== VSCode 캐시 정리 및 재시작 도구 ===\n")
    
    # 1. VSCode 프로세스 종료
    kill_vscode_processes()
    
    # 2. 캐시 정리
    cache_cleared = clear_vscode_cache()
    
    # 3. 사용자 선택
    if cache_cleared:
        print("\n다음 옵션을 선택하세요:")
        print("1. 확장 프로그램 비활성화 모드로 시작")
        print("2. 일반 모드로 시작") 
        print("3. 시작하지 않음")
        
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == '1':
            start_vscode_safe_mode(disable_extensions=True)
        elif choice == '2':
            start_vscode_safe_mode(disable_extensions=False)
        else:
            print("VSCode를 수동으로 시작하세요.")
    else:
        print("캐시 정리가 완료되지 않았습니다.")
    
    print("\n작업 완료!")

if __name__ == "__main__":
    main()
