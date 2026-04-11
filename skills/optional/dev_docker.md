# [OPTIONAL SKILL] Docker & Container Patterns

## Dockerfile 모범사례
```dockerfile
# 1. 작은 베이스 이미지
FROM python:3.12-slim

# 2. 비루트 사용자
RUN useradd -m appuser

# 3. 의존성 먼저 복사 (레이어 캐시 최적화)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스코드 복사
COPY --chown=appuser:appuser . .
USER appuser

# 5. 헬스체크
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

## docker-compose 기본 구조
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 10s
```

## 자주 쓰는 명령어
```bash
# 실행 중 컨테이너 쉘 접속
docker exec -it <container> bash

# 로그 실시간 확인
docker compose logs -f app

# 이미지/컨테이너 정리
docker system prune -af

# 빌드 캐시 없이 재빌드
docker compose build --no-cache
```

## .dockerignore
```
__pycache__/
*.pyc
.env
*.db
.git
```
