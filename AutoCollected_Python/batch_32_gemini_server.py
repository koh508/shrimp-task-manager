from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import json
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini 클라이언트 초기화
class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro-latest')
        self.chat_sessions: Dict[str, Any] = {}

    def start_chat(self, session_id: str, history: List[Dict] = None):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = self.model.start_chat(history=history or [])
        return self.chat_sessions[session_id]

    async def send_message(self, session_id: str, message: str) -> str:
        try:
            chat = self.start_chat(session_id)
            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# API 키 확인
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

gemini_client = GeminiClient(GEMINI_API_KEY)

# 요청/응답 모델
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

# 채팅 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    response = await gemini_client.send_message(
        chat_request.session_id, 
        chat_request.message
    )
    return ChatResponse(
        response=response,
        session_id=chat_request.session_id
    )

# 웹소켓 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

# 웹소켓 엔드포인트
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if "message" in message_data:
                    response = await gemini_client.send_message(
                        client_id,
                        message_data["message"]
                    )
                    await manager.send_personal_message(
                        json.dumps({"response": response}),
                        client_id
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON format"}),
                    client_id
                )
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")

# 상태 확인 엔드포인트
@app.get("/health")
async def health_check():
    try:
        # 간단한 Gemini API 호출로 연결 테스트
        test_chat = gemini_client.model.start_chat()
        response = test_chat.send_message("Test message")
        return {
            "status": "healthy",
            "model": "gemini-2.5-pro-latest",
            "gemini_status": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }, 500

# 루트 엔드포인트
@app.get("/")
async def read_root():
    return {
        "message": "Gemini Chat API 서버가 실행 중입니다.",
        "endpoints": {
            "chat": "/chat (POST)",
            "websocket": "/ws/{client_id} (WebSocket)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    print("서버를 시작합니다... (http://localhost:8000)")
    print("API 문서: http://localhost:8000/docs")
    print("상태 확인: http://localhost:8000/health")
    uvicorn.run("gemini_server:app", host="0.0.0.0", port=8000, reload=True)
