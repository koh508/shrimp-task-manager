# HeroicAge 에이전트 설정

# MCP 서버 설정
MCP_SERVER = "http://localhost:8081"

# 에이전트 설정
AGENT_NAME = "HeroicAge"
AGENT_ENDPOINT = "http://localhost:9000"
AGENT_DESCRIPTION = "히로익에이지 에이전트 - Gemini AI 웹훅 처리"

# 서버 설정
HOST = "0.0.0.0"
PORT = 9000
DEBUG = True

# 로그 설정
LOG_LEVEL = "INFO"
LOG_FILE = "logs/heroicage.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 이미지 저장 경로
IMAGE_SAVE_DIR = "data/images"

# MCP 등록 간격 (초)
REGISTRATION_INTERVAL = 300

# API 키 (MCP 서버와의 통신용)
API_KEY = "your-secret-key-here"

# Gemini 웹훅 시크릿 (보안을 위해 환경변수 사용 권장)
WEBHOOK_SECRET = "your-webhook-secret"
