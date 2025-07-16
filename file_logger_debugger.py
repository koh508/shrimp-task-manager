import sys
import os
import inspect
from datetime import datetime

# 로그를 기록할 파일 경로
LOG_FILE = "debug_log.txt"


def write_log(message):
    """로그 파일에 메시지를 기록합니다."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")


# 이전 로그 파일 삭제
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

write_log("--- 임포트 문제 디버깅 시작 ---")

# 1. sys.path 정보 기록
write_log("\n--- Python 모듈 검색 경로 (sys.path) ---")
sys_path_str = "\n".join(sys.path)
write_log(sys_path_str)
write_log("-----------------------------------------")

# 2. dotenv 모듈 임포트 시도 및 정보 기록
try:
    import dotenv

    write_log("\n--- 'dotenv' 모듈 정보 ---")
    write_log("성공적으로 'dotenv' 모듈을 불러왔습니다.")

    try:
        file_path = inspect.getfile(dotenv)
        write_log(f"모듈의 실제 파일 위치: {file_path}")
    except TypeError:
        if hasattr(dotenv, "__path__"):
            write_log(f"모듈의 경로 위치: {dotenv.__path__}")
        else:
            write_log("모듈의 파일 위치를 특정할 수 없습니다.")

    write_log(f"모듈 내용물 (dir): {dir(dotenv)}")
    write_log("---------------------------")

    # 3. load_dotenv 함수 임포트 시도
    from dotenv import load_dotenv

    write_log("\n성공: 'load_dotenv' 함수를 성공적으로 불러왔습니다!")
    write_log("결론: 이제 임포트가 정상적으로 작동합니다.")

except ImportError as e:
    write_log(f"\n!!! 임포트 오류 발생: {e}")
    write_log(
        "원인: 위에서 확인된 'dotenv' 모듈이 올바른 'python-dotenv' 라이브러리가 아니거나, 라이브러리가 올바른 경로에 설치되지 않았을 수 있습니다."
    )
except Exception as e:
    write_log(f"\n!!! 예기치 않은 오류 발생: {e}")

write_log("\n--- 디버깅 종료 ---")

print(f"디버그 로그가 '{LOG_FILE}' 파일에 저장되었습니다. 내용을 확인해주세요.")
