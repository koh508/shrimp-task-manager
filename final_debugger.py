import sys
import os

print("--- 임포트 문제 최종 디버거 ---")

# 1. 현재 작업 디렉터리를 sys.path에서 일시적으로 제거
#    이것은 로컬 파일/폴더가 설치된 라이브러리를 가리는(shadowing) 문제를 방지합니다.
current_dir = os.getcwd()
if current_dir in sys.path:
    print(f"\n모듈 검색 경로에서 현재 디렉터리를 제거합니다: {current_dir}")
    sys.path.remove(current_dir)

# ''는 현재 디렉터리를 의미하므로, 이 또한 제거합니다.
if "" in sys.path:
    print("모듈 검색 경로에서 '' (현재 디렉터리)를 제거합니다.")
    sys.path.remove("")

print("\n--- 수정된 모듈 검색 경로 (sys.path) ---")
for p in sys.path:
    print(p)
print("-----------------------------------------\n")

# 2. 경로 수정 후, 다시 임포트 시도
try:
    from dotenv import load_dotenv
    import inspect

    print("성공: 'load_dotenv' 함수를 성공적으로 불러왔습니다!")

    # 성공했다면, 올바른 모듈의 위치를 출력합니다.
    import dotenv

    file_path = inspect.getfile(dotenv)
    print(f"불러온 모듈의 실제 위치: {file_path}")
    print("\n결론: 프로젝트 폴더 내에 'dotenv'라는 이름의 다른 파일이나 폴더가 있어 충돌을 일으키고 있었습니다.")

except ImportError as e:
    print(f"실패: 여전히 'load_dotenv'를 불러올 수 없습니다.")
    print(f"오류: {e}")
    print("\n결론: 문제가 더 복잡하며, 파이썬 설치 자체나 환경 변수 문제일 수 있습니다.")
except Exception as e:
    print(f"!!! 예기치 않은 오류 발생: {e}")
