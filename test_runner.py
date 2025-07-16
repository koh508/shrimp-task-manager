import subprocess
import sys
import time
import os

print("🚀 단일 서비스 테스트 러너 시작")

service_script = 'clipper_backend.py'
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), service_script)

log_file_path = script_path + ".test.log"
if os.path.exists(log_file_path):
    os.remove(log_file_path)

log_file = open(log_file_path, "w", encoding="utf-8")

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

process = None
try:
    print(f"   - {service_script} 실행 시도...")
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=log_file,
        stderr=log_file,
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    print(f"   - ✅ {service_script} (PID: {process.pid}) 실행 완료. 15초 후 상태 확인...")
    
    # 서비스가 시작될 충분한 시간을 기다립니다.
    time.sleep(15)

    print("\n🔍 네트워크 상태 확인:")
    os.system('netstat -ano -p TCP | findstr ":5001"')

except Exception as e:
    print(f"❌ 실행 오류: {e}")
finally:
    if process:
        print("\n✅ 테스트 종료. 프로세스 정리 중...")
        process.terminate()
        process.wait()
    log_file.close()
    print("✨ 테스트 완료.")
