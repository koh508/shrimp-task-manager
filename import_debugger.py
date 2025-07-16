import sys
import os
import inspect

print("--- Python의 모듈 검색 경로 (sys.path) ---")
for p in sys.path:
    print(p)
print("-----------------------------------------\n")

try:
    import dotenv

    print("--- 'dotenv' 모듈 상세 정보 ---")
    print("성공적으로 'dotenv' 모듈을 불러왔습니다.")

    try:
        # inspect.getfile()은 모듈의 소스 파일 위치를 찾는 가장 확실한 방법입니다.
        file_path = inspect.getfile(dotenv)
        print(f"모듈의 실제 파일 위치: {file_path}")
    except TypeError:
        # __file__ 속성이 없는 빌트인 모듈이나 패키지의 경우
        if hasattr(dotenv, "__path__"):
            print(f"모듈의 경로 위치: {dotenv.__path__}")
        else:
            print("모듈의 파일 위치를 특정할 수 없습니다.")

    print("모듈 내용물 (dir):", dir(dotenv))
    print("---------------------------\n")

    # load_dotenv 함수 임포트 시도
    from dotenv import load_dotenv

    print("'load_dotenv' 함수를 성공적으로 불러왔습니다.")

except ImportError as e:
    print(f"!!! 임포트 오류 발생: {e}")
    print("오류의 원인은 위에서 확인된 'dotenv' 모듈이 올바른 'python-dotenv' 라이브러리가 아니기 때문일 가능성이 높습니다.")
except Exception as e:
    print(f"!!! 예기치 않은 오류 발생: {e}")
