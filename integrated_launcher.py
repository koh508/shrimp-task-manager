import subprocess
import time
import sys
import os
import psutil # psutil 임포트

# 실행할 서비스 목록
services = ["clipper_backend.py", "simple_dashboard.py", "stability_monitor_fixed.py"]

processes = []
log_files = []


def cleanup_ports(ports):
    print("🧹 기존 서비스 포트 정리 시도...")
    cleaned_count = 0
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN' and conn.laddr.port in ports:
            try:
                proc = psutil.Process(conn.pid)
                print(f"   - {conn.laddr.port}번 포트를 사용하는 프로세스 (PID: {conn.pid}, 이름: {proc.name()})를 종료합니다.")
                proc.terminate()
                proc.wait(timeout=3) # 종료 대기
                cleaned_count += 1
            except psutil.NoSuchProcess:
                print(f"   - 프로세스 (PID: {conn.pid})를 찾을 수 없습니다. 이미 종료된 것 같습니다.")
            except psutil.AccessDenied:
                print(f"   - ❌ 권한 부족: 프로세스 (PID: {conn.pid})를 종료할 수 없습니다.")
            except Exception as e:
                print(f"   - ❌ 프로세스 (PID: {conn.pid}) 종료 중 오류: {e}")
    if cleaned_count == 0:
        print("   - 정리할 기존 프로세스가 없습니다.")
    print("✨ 포트 정리 완료.")

def main():
    cleanup_ports([5000, 5001])
    print("\n🚀 단순화된 통합 런처를 시작합니다.")

    # 현재 스크립트의 디렉토리를 기준으로 경로 설정
    base_path = os.path.dirname(os.path.abspath(__file__))

    for service_script in services:
        script_path = os.path.join(base_path, service_script)

        if not os.path.exists(script_path):
            print(f"❌ 스크립트를 찾을 수 없습니다: {script_path}")
            continue

        try:
            # 로그 파일 설정
            log_file_path = script_path + ".log"
            # 기존 로그 파일 삭제
            if os.path.exists(log_file_path):
                os.remove(log_file_path)

            log_file = open(log_file_path, "w", encoding="utf-8")
            log_files.append(log_file)

            # 가상환경의 파이썬으로 각 서비스를 실행하고 출력을 파일로 리디렉션
            print(f"   - {service_script} 시작 시도...")

            # 자식 프로세스의 인코딩을 UTF-8로 강제하여 UnicodeEncodeError 방지
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # Windows에서 자식 프로세스를 부모와 완전히 분리하여 실행
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.DETACHED_PROCESS

            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=log_file,
                stderr=log_file,
                env=env,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                creationflags=creation_flags
            )
            processes.append(process)
            print(f"   - ✅ {service_script} (PID: {process.pid}) 실행 요청 완료. 로그: {os.path.basename(log_file_path)}")
            time.sleep(2)  # 다음 서비스 실행 전 잠시 대기
        except Exception as e:
            print(f"   - ❌ {service_script} 실행 중 오류 발생: {e}")

    print("\n✨ 모든 서비스 시작 요청이 완료되었습니다.")
    print("\n🔍 이제 서비스가 정상적으로 실행되었는지 10초 동안 감시합니다...")

    # 10초 동안 포트 상태 확인
    for i in range(5):
        print(f"   - {i*2}초 경과... 포트 확인 중...")
        try:
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, check=True, encoding="cp949"
            )
            output = result.stdout
            found_5000 = ":5000" in output
            found_5001 = ":5001" in output

            print(f"     - 5000번 포트: {'✅ 열림' if found_5000 else '❌ 닫힘'}")
            print(f"     - 5001번 포트: {'✅ 열림' if found_5001 else '❌ 닫힘'}")

            if found_5000 and found_5001:
                print("\n🎉 모든 서비스가 성공적으로 실행되었습니다!")
                break
        except (subprocess.CalledProcessError, FileNotFoundError, UnicodeDecodeError) as e:
            print(f"     - netstat 실행 오류: {e}")
        except Exception as e:
            print(f"     - 알 수 없는 오류 발생: {e}")
        time.sleep(2)
    else:
        print("\n❌ 시간 내에 모든 서비스가 시작되지 않았습니다. 문제 해결이 필요합니다.")
        print("\n🛑 런처를 종료합니다.")
        return

    print("\n✅ 서비스들이 실행 중입니다. 런처는 계속 대기합니다.")
    print("   (Ctrl+C를 눌러 런처와 모든 서비스를 종료할 수 있습니다.)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Ctrl+C 입력 감지. 모든 서비스를 종료합니다...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5) # 5초간 기다림
                print(f"   - PID {p.pid} 종료 완료.")
            except subprocess.TimeoutExpired:
                p.kill() # 강제 종료
                print(f"   - PID {p.pid} 강제 종료.")
            except Exception as e:
                print(f"   - PID {p.pid} 종료 중 오류: {e}")
        # 로그 파일 핸들 닫기
        for f in log_files:
            try:
                f.close()
            except Exception as e:
                print(f"   - 로그 파일 닫기 오류: {e}")
        print("✅ 모든 서비스가 종료되었습니다.")


if __name__ == "__main__":
    main()
