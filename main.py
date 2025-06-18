import uvicorn
import logging
import asyncio
import httpx
import time
import base64
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
from pathlib import Path

# MCP 클라이언트 클래스 정의
class MCPClient:
    def __init__(self, mcp_server: str):
        self.mcp_server = mcp_server.rstrip('/')
        self.session = httpx.AsyncClient()
        self.registered = False
    
    async def register(self, agent_name: str, agent_endpoint: str):
        """MCP 서버에 에이전트 등록"""
        try:
            # MCP 서버의 기본 엔드포인트로 요청
            register_url = f"{self.mcp_server}/register"
            logger.info(f"Registering agent at: {register_url}")
            logger.info(f"Agent name: {agent_name}, Endpoint: {agent_endpoint}")
            
            response = await self.session.post(
                register_url,
                json={"name": agent_name, "endpoint": agent_endpoint},
                timeout=10.0
            )
            response.raise_for_status()
            self.registered = True
            logger.info(f"Successfully registered with MCP server: {self.mcp_server}")
        except Exception as e:
            logger.error(f"Failed to register with MCP server: {e}")
            self.registered = False

# 분석기와 학습 시스템 클래스 정의 (더미 구현)
class CodeAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        logger.info(f"Initialized CodeAnalyzer with data_dir: {data_dir}")

class LearningSystem:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        logger.info(f"Initialized LearningSystem with data_dir: {data_dir}")

# 로깅 설정
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "heroicage.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HeroicAge")

app = FastAPI(
    title="HeroicAge Agent",
    description="히로익에이지 에이전트 - Gemini AI 웹훅 처리 및 MCP 연동",
    version="1.0.0"
)

# MCP 클라이언트 초기화
MCP_SERVER = os.getenv("MCP_SERVER", "https://shrimp-mcp-production.up.railway.app")
mcp_client = MCPClient(MCP_SERVER)
logger.info(f"MCP Server URL: {MCP_SERVER}")

# 분석기와 학습 시스템 초기화
analyzer = CodeAnalyzer("analysis_data")
learning_system = LearningSystem("learning_data")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 이벤트"""
    agent_endpoint = f"http://localhost:{os.getenv('PORT', '9000')}"
    logger.info(f"Starting HeroicAge Agent...")
    logger.info(f"Connecting to MCP at: {MCP_SERVER}")
    await mcp_client.register("HeroicAge", agent_endpoint)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "status": "running",
        "agent": agent_status.name,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Starting HeroicAge Agent...")
    logger.info(f"Connecting to MCP at: {MCP_SERVER}")
    logger.info("="*50)
    
    # 기본 포트(8000)를 사용하여 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        log_level="info"
    )
