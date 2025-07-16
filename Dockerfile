# Python 3.11-slim 버전을 기반으로 이미지를 생성합니다.
# Cache bust: 2025-07-17
FROM python:3.11-slim

# 컨테이너 내부에 작업 디렉토리를 설정합니다.
WORKDIR /app

# 먼저 requirements.txt 파일을 복사하여 의존성을 설치합니다.
# (이렇게 하면 코드 변경 시 매번 의존성을 새로 설치하지 않아 캐시를 효율적으로 사용할 수 있습니다.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 프로젝트 파일들을 작업 디렉토리로 복사합니다.
COPY . .

# 컨테이너가 시작될 때 실행할 기본 명령어를 설정합니다.
CMD ["python", "ultra_ai_assistant_unified.py"]
