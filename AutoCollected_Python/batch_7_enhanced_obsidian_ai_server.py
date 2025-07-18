#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Enhanced Obsidian AI Server v3.0
===================================
실제 AI 에이전트 로그 연동, Gemini LLM 고급 대화 지원
"""

import asyncio
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
import sqlite3
import threading
import queue
import psutil
import os
import glob
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import tailer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('obsidian_ai_enhanced.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# Gemini API 키 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBU6ZfBdEW5ZglSB7aK8CQ9vWKK7_hvINs')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 요청 모델들
class NaturalLanguageRequest(BaseModel):
    input: str
    context: str = "obsidian_plugin"
    mode: str = "conversation"
    timestamp: str

class ConversationMessage(BaseModel):
    message: str
    context: Optional[Dict] = None

# 전역 로그 큐
log_queue = queue.Queue(maxsize=1000)
connected_clients = set()

class RealAILogManager:
    """실제 AI 에이전트 로그 관리자"""
    
    def __init__(self):
        self.log_files = self._discover_log_files()
        self.log_watchers = {}
        self.current_logs = []
        self.setup_log_watchers()
    
    def _discover_log_files(self) -> List[str]:
        """시스템에서 AI 에이전트 로그 파일들을 찾습니다"""
        log_patterns = [
            "*.log",
            "autonomous_*.log", 
            "evolution_*.log",
            "goal_achievement.log",
            "quantum_intelligence.log",
            "ultra_fast_processing.log"
        ]
        
        log_files = []
        for pattern in log_patterns:
            files = glob.glob(pattern)
            log_files.extend(files)
        
        logger.info(f"✅ 발견된 로그 파일들: {len(log_files)}개")
        return log_files
    
    def setup_log_watchers(self):
        """로그 파일 감시자 설정"""
        for log_file in self.log_files[:10]:  # 최대 10개 파일만 감시
            try:
                if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                    thread = threading.Thread(
                        target=self._watch_log_file, 
                        args=(log_file,),
                        daemon=True
                    )
                    thread.start()
                    self.log_watchers[log_file] = thread
                    logger.info(f"📡 로그 감시 시작: {log_file}")
            except Exception as e:
                logger.error(f"❌ 로그 감시 설정 실패 {log_file}: {e}")
    
    def _watch_log_file(self, log_file: str):
        """개별 로그 파일을 실시간으로 감시"""
        try:
            for line in tailer.follow(open(log_file, 'r', encoding='utf-8', errors='ignore')):
                if line.strip():
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'source': os.path.basename(log_file),
                        'level': self._extract_log_level(line),
                        'message': line.strip()
                    }
                    self.current_logs.append(log_entry)
                    
                    # 최근 1000개만 유지
                    if len(self.current_logs) > 1000:
                        self.current_logs = self.current_logs[-1000:]
                    
                    # 웹소켓으로 전송
                    try:
                        log_queue.put_nowait(log_entry)
                    except queue.Full:
                        pass
        except Exception as e:
            logger.error(f"❌ 로그 파일 감시 오류 {log_file}: {e}")
    
    def _extract_log_level(self, line: str) -> str:
        """로그 라인에서 레벨 추출"""
        if 'ERROR' in line:
            return 'ERROR'
        elif 'WARNING' in line or 'WARN' in line:
            return 'WARNING'
        elif 'INFO' in line:
            return 'INFO'
        elif 'DEBUG' in line:
            return 'DEBUG'
        else:
            return 'INFO'
    
    def get_recent_logs(self, limit: int = 100, agent_type: str = None) -> List[Dict]:
        """최근 로그 가져오기"""
        logs = self.current_logs[-limit:] if self.current_logs else []
        
        if agent_type:
            logs = [log for log in logs if agent_type.lower() in log['source'].lower()]
        
        return logs
    
    def get_log_summary(self) -> Dict:
        """로그 요약 정보"""
        if not self.current_logs:
            return {
                'total_logs': 0,
                'log_sources': [],
                'recent_activity': '활동 없음'
            }
        
        sources = list(set([log['source'] for log in self.current_logs]))
        recent_count = len([log for log in self.current_logs 
                          if datetime.fromisoformat(log['timestamp']) > 
                          datetime.now() - timedelta(minutes=5)])
        
        return {
            'total_logs': len(self.current_logs),
            'log_sources': sources,
            'recent_activity': f'최근 5분간 {recent_count}개 로그',
            'active_agents': len(sources)
        }

class GeminiConversationManager:
    """Gemini LLM을 사용한 고급 대화 관리자"""
    
    def __init__(self):
        self.model = None
        self.chat_sessions = {}
        self.conversation_history = []
        self.initialize_gemini()
    
    def initialize_gemini(self):
        """Gemini 모델 초기화"""
        try:
            if GEMINI_API_KEY:
                self.model = genai.GenerativeModel(
                    model_name='gemini-pro',
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                logger.info("✅ Gemini 모델 초기화 완료")
            else:
                logger.warning("⚠️ Gemini API 키가 없습니다. 시뮬레이션 모드로 동작합니다.")
        except Exception as e:
            logger.error(f"❌ Gemini 초기화 실패: {e}")
            self.model = None
    
    async def process_conversation(self, message: str, context: Dict = None) -> str:
        """자연어 대화 처리"""
        try:
            if not self.model:
                return await self._simulate_response(message)
            
            # 컨텍스트 기반 프롬프트 생성
            system_prompt = self._build_system_prompt(context)
            full_message = f"{system_prompt}\n\n사용자: {message}"
            
            # Gemini로 응답 생성
            response = await self.model.generate_content_async(full_message)
            
            # 대화 기록 저장
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user_message': message,
                'ai_response': response.text,
                'context': context
            })
            
            # 최근 100개 대화만 유지
            if len(self.conversation_history) > 100:
                self.conversation_history = self.conversation_history[-100:]
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ 대화 처리 오류: {e}")
            return await self._simulate_response(message)
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """컨텍스트 기반 시스템 프롬프트 생성"""
        base_prompt = """당신은 고급 AI 에이전트 시스템의 전문 어시스턴트입니다.
        
주요 역할:
- AI 에이전트들의 로그와 활동을 모니터링하고 분석
- 사용자의 자연어 명령을 이해하고 적절히 응답
- 시스템 상태와 에이전트 성능에 대한 인사이트 제공
- 한국어로 친근하고 전문적인 응답

현재 시스템 상태:
- 활성 AI 에이전트들이 24시간 연속 진화 중
- 자율 학습, 목표 달성, 양자 지능 등 다양한 에이전트 운영
- 실시간 로그 모니터링 및 성능 분석 진행"""

        if context:
            if context.get('log_data'):
                base_prompt += f"\n\n최근 로그 정보:\n{context['log_data']}"
            if context.get('command_type'):
                base_prompt += f"\n\n요청 유형: {context['command_type']}"
        
        return base_prompt
    
    async def _simulate_response(self, message: str) -> str:
        """Gemini가 없을 때 시뮬레이션 응답"""
        # 간단한 키워드 기반 응답
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['로그', 'log', '기록']):
            return "🔍 실시간 로그 모니터링 중입니다. 현재 여러 AI 에이전트들이 활발히 학습하고 진화하고 있어요!"
        
        elif any(word in message_lower for word in ['에이전트', 'agent', '상태']):
            return "🤖 현재 자율학습, 목표달성, 진화 최적화 등 다양한 AI 에이전트들이 24시간 연속 운영 중입니다!"
        
        elif any(word in message_lower for word in ['안녕', 'hello', '헬로']):
            return "👋 안녕하세요! AI 에이전트 시스템 어시스턴트입니다. 로그 확인이나 에이전트 상태에 대해 궁금한 것이 있으시면 언제든 물어보세요!"
        
        else:
            return f"💭 '{message}'에 대해 이해했습니다. 더 구체적인 정보가 필요하시면 'Gemini API 키'를 설정해주세요!"

class EnhancedObsidianAIServer:
    """향상된 옵시디언 AI 서버"""
    
    def __init__(self):
        self.app = FastAPI(title="Enhanced Obsidian AI Server v3.0", version="3.0")
        self.setup_cors()
        self.setup_routes()
        self.natural_language_processor = NaturalLanguageProcessor()
        self.log_manager = RealAILogManager()
        self.conversation_manager = GeminiConversationManager()
        self.active_connections = set()
        
    def setup_cors(self):
        """CORS 설정"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def setup_routes(self):
        """라우트 설정"""
        
        @self.app.get("/")
        async def root():
            # HTML 웹 인터페이스 반환
            html_content = """
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>🧠 Enhanced Obsidian AI Server v2.0</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        color: white;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        padding: 30px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .header h1 {
                        font-size: 3em;
                        margin: 0;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    }
                    .features {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }
                    .feature-card {
                        background: rgba(255, 255, 255, 0.15);
                        border-radius: 15px;
                        padding: 25px;
                        text-align: center;
                        transition: transform 0.3s ease;
                    }
                    .feature-card:hover {
                        transform: translateY(-5px);
                    }
                    .feature-icon {
                        font-size: 3em;
                        margin-bottom: 15px;
                    }
                    .status {
                        background: rgba(76, 175, 80, 0.3);
                        border: 2px solid #4caf50;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 20px 0;
                        text-align: center;
                    }
                    .api-endpoints {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        margin: 30px 0;
                    }
                    .endpoint {
                        background: rgba(0, 0, 0, 0.2);
                        border-radius: 8px;
                        padding: 10px 15px;
                        margin: 10px 0;
                        font-family: 'Courier New', monospace;
                    }
                    .test-area {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        margin: 30px 0;
                    }
                    .chat-input {
                        width: 100%;
                        padding: 15px;
                        border: none;
                        border-radius: 10px;
                        margin: 10px 0;
                        font-size: 16px;
                    }
                    .chat-button {
                        background: #4caf50;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        border-radius: 10px;
                        cursor: pointer;
                        font-size: 16px;
                        transition: background 0.3s ease;
                    }
                    .chat-button:hover {
                        background: #45a049;
                    }
                    .response-area {
                        background: rgba(0, 0, 0, 0.3);
                        border-radius: 10px;
                        padding: 15px;
                        margin: 15px 0;
                        min-height: 100px;
                        color: #e0e0e0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🧠 Enhanced Obsidian AI Server</h1>
                        <p>고급 자연어 처리 • 실시간 로그 모니터링 • 지능형 대화 시스템</p>
                    </div>
                    
                    <div class="status">
                        <h2>🟢 시스템 상태: 정상 운영 중</h2>
                        <p>버전 2.0 • 포트 8001 • 실시간 모니터링 활성화</p>
                    </div>
                    
                    <div class="features">
                        <div class="feature-card">
                            <div class="feature-icon">🤖</div>
                            <h3>자연어 처리</h3>
                            <p>고급 의도 분석과 엔티티 추출로 스마트한 응답 생성</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">💬</div>
                            <h3>고급 대화모델</h3>
                            <p>컨텍스트 기반 대화와 제안 시스템</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📊</div>
                            <h3>실시간 로그</h3>
                            <p>시스템 상태와 활동을 실시간으로 모니터링</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🔗</div>
                            <h3>Obsidian 연동</h3>
                            <p>플러그인을 통한 완벽한 Obsidian 통합</p>
                        </div>
                    </div>
                    
                    <div class="api-endpoints">
                        <h2>🔌 API 엔드포인트</h2>
                        <div class="endpoint">GET /health - 헬스 체크</div>
                        <div class="endpoint">POST /chat - 간단한 채팅</div>
                        <div class="endpoint">POST /api/conversation - 고급 대화</div>
                        <div class="endpoint">POST /api/natural-language - 자연어 처리</div>
                        <div class="endpoint">GET /api/system/status - 시스템 상태</div>
                        <div class="endpoint">GET /api/logs/recent - 최근 로그</div>
                        <div class="endpoint">GET /api/logs/stream - 로그 스트림</div>
                    </div>
                    
                    <div class="test-area">
                        <h2>🧪 채팅 테스트</h2>
                        <input type="text" class="chat-input" id="chatInput" placeholder="메시지를 입력하세요...">
                        <button class="chat-button" onclick="sendMessage()">💬 전송</button>
                        <div class="response-area" id="responseArea">
                            응답이 여기에 표시됩니다...
                        </div>
                    </div>
                </div>
                
                <script>
                    async function sendMessage() {
                        const input = document.getElementById('chatInput');
                        const responseArea = document.getElementById('responseArea');
                        const message = input.value.trim();
                        
                        if (!message) return;
                        
                        responseArea.innerHTML = '🤔 처리 중...';
                        
                        try {
                            const response = await fetch('/chat', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ message: message })
                            });
                            
                            const data = await response.json();
                            responseArea.innerHTML = `
                                <strong>🤖 AI 응답:</strong><br>
                                ${data.response}<br><br>
                                <small>📅 ${new Date(data.timestamp).toLocaleString()}</small>
                            `;
                            input.value = '';
                        } catch (error) {
                            responseArea.innerHTML = `❌ 오류: ${error.message}`;
                        }
                    }
                    
                    document.getElementById('chatInput').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            sendMessage();
                        }
                    });
                    
                    // 실시간 상태 업데이트
                    setInterval(async () => {
                        try {
                            const response = await fetch('/health');
                            const data = await response.json();
                            console.log('서버 상태:', data.status);
                        } catch (error) {
                            console.error('상태 확인 실패:', error);
                        }
                    }, 30000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
            
        @self.app.get("/api/status")
        async def api_status():
            """JSON 형태의 상태 정보 (플러그인 호환성)"""
            return {
                "service": "Enhanced Obsidian AI Server",
                "version": "2.0",
                "features": [
                    "자연어 처리",
                    "고급 대화모델", 
                    "실시간 로그 스트리밍",
                    "지능형 의도 분석"
                ],
                "status": "running",
                "timestamp": datetime.now().isoformat()
            }
            
        @self.app.get("/health")
        async def health_check():
            """헬스 체크 엔드포인트"""
            try:
                # 간단한 헬스 체크
                return {
                    "status": "healthy",
                    "service": "Enhanced Obsidian AI Server",
                    "version": "2.0",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": time.time()
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            
        @self.app.post("/api/natural-language")
        async def process_natural_language(request: NaturalLanguageRequest):
            """자연어 처리 API"""
            try:
                logger.info(f"자연어 처리 요청: {request.input[:100]}...")
                
                result = await self.natural_language_processor.process(request.input)
                
                response = {
                    "success": True,
                    "message": result.get("response", "처리 완료"),
                    "action": result.get("action"),
                    "confidence": result.get("confidence", 0.8),
                    "intent": result.get("intent"),
                    "entities": result.get("entities", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # 대화 이력에 추가
                self.conversation_history.append({
                    "user_input": request.input,
                    "ai_response": response,
                    "timestamp": request.timestamp
                })
                
                self.add_log("info", "natural_language", f"자연어 처리 완료: {request.input[:50]}...")
                
                return response
                
            except Exception as e:
                logger.error(f"자연어 처리 오류: {e}")
                self.add_log("error", "natural_language", f"처리 오류: {str(e)}")
                return {
                    "success": False,
                    "message": "자연어 처리 중 오류가 발생했습니다.",
                    "error": str(e)
                }
                
        @self.app.post("/api/conversation")
        async def advanced_conversation(message: ConversationMessage):
            """고급 대화 API"""
            try:
                response = await self.natural_language_processor.generate_response(
                    message.message, 
                    context=message.context,
                    history=self.conversation_history[-10:]  # 최근 10개 대화만
                )
                
                return {
                    "success": True,
                    "response": response["message"],
                    "suggestions": response.get("suggestions", []),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"대화 처리 오류: {e}")
                return {
                    "success": False,
                    "message": "대화 처리 중 오류가 발생했습니다.",
                    "error": str(e)
                }
                
        @self.app.post("/chat")
        async def enhanced_chat(message: ConversationMessage):
            """Gemini 기반 고급 대화"""
            try:
                # 최근 로그 정보를 컨텍스트로 추가
                recent_logs = self.log_manager.get_recent_logs(limit=10)
                log_summary = self.log_manager.get_log_summary()
                
                context = {
                    'log_data': f"최근 로그: {len(recent_logs)}개, 활성 에이전트: {log_summary.get('active_agents', 0)}개",
                    'command_type': 'general_conversation',
                    'timestamp': datetime.now().isoformat()
                }
                
                if message.context:
                    context.update(message.context)
                
                response = await self.conversation_manager.process_conversation(
                    message.message, 
                    context
                )
                
                return {
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                    "context": context,
                    "log_summary": log_summary,
                    "success": True
                }
                
            except Exception as e:
                logger.error(f"❌ 대화 처리 오류: {e}")
                return {
                    "response": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                    "success": False
                }
                
        @self.app.post("/api/analyze")
        async def analyze_file(request: dict):
            """파일 분석 API (플러그인 호환성)"""
            try:
                file_name = request.get("fileName", "unknown")
                content = request.get("content", "")
                
                # 간단한 파일 분석
                analysis = {
                    "lines": len(content.split('\n')),
                    "characters": len(content),
                    "words": len(content.split()),
                    "file_type": file_name.split('.')[-1] if '.' in file_name else "unknown"
                }
                
                # 파일 유형별 분석
                if analysis["file_type"] in ["js", "ts", "javascript", "typescript"]:
                    analysis["language"] = "JavaScript/TypeScript"
                    analysis["suggestions"] = ["함수 최적화", "타입 안정성 확인", "코드 스타일 검토"]
                elif analysis["file_type"] in ["py", "python"]:
                    analysis["language"] = "Python"
                    analysis["suggestions"] = ["PEP 8 준수", "성능 최적화", "타입 힌트 추가"]
                elif analysis["file_type"] in ["md", "markdown"]:
                    analysis["language"] = "Markdown"
                    analysis["suggestions"] = ["구조화 개선", "링크 검증", "가독성 향상"]
                else:
                    analysis["language"] = "기타"
                    analysis["suggestions"] = ["문서화", "구조 개선"]
                
                return {
                    "status": "완료",
                    "summary": f"{analysis['language']} 파일 분석 완료",
                    "details": f"📊 분석 결과:\n- 라인 수: {analysis['lines']}\n- 문자 수: {analysis['characters']}\n- 단어 수: {analysis['words']}\n- 언어: {analysis['language']}\n\n💡 제안사항:\n" + "\n".join(f"• {s}" for s in analysis['suggestions']),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"파일 분석 오류: {e}")
                return {
                    "status": "오류",
                    "summary": "파일 분석 실패",
                    "details": f"오류: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                
        @self.app.get("/api/logs/recent")
        async def get_recent_logs(limit: int = 50):
            """최근 로그 가져오기"""
            try:
                logs = self.log_monitor.get_recent_logs(limit)
                return {"logs": logs}
            except Exception as e:
                logger.error(f"로그 조회 오류: {e}")
                return {"logs": [], "error": str(e)}
                
        @self.app.get("/api/logs/stream")
        async def stream_logs():
            """실시간 로그 스트림"""
            async def log_generator():
                try:
                    while True:
                        try:
                            # 큐에서 로그 가져오기 (비블로킹)
                            log_entry = log_queue.get_nowait()
                            yield f"data: {json.dumps(log_entry)}\n\n"
                        except queue.Empty:
                            # 큐가 비어있으면 잠시 대기
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"로그 스트림 오류: {e}")
                            break
                except Exception as e:
                    logger.error(f"로그 생성기 오류: {e}")
                    
            return StreamingResponse(
                log_generator(), 
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
            
        @self.app.get("/api/system/status")
        async def get_system_status():
            """시스템 상태 조회"""
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                return {
                    "status": "healthy",
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "conversation_count": len(self.conversation_history),
                    "active_connections": len(self.active_connections),
                    "uptime": time.time(),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
                
    def add_log(self, level: str, source: str, message: str):
        """로그 추가"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "source": source,
            "message": message
        }
        
        try:
            log_queue.put_nowait(log_entry)
        except queue.Full:
            # 큐가 가득 찬 경우 오래된 로그 제거
            try:
                log_queue.get_nowait()
                log_queue.put_nowait(log_entry)
            except queue.Empty:
                pass

class NaturalLanguageProcessor:
    """자연어 처리기"""
    
    def __init__(self):
        self.intent_patterns = {
            "code_analysis": [
                r"코드.*분석", r"파일.*분석", r"분석.*해", r"analyze", r"check.*code"
            ],
            "hero_summon": [
                r"영웅.*소환", r"hero.*summon", r"에이전트.*호출", r"agent.*call"
            ],
            "dashboard_open": [
                r"대시보드.*열", r"dashboard.*open", r"모니터.*보", r"상태.*확인"
            ],
            "schedule_management": [
                r"일정.*정리", r"스케줄", r"계획.*세", r"todo", r"task"
            ],
            "file_operations": [
                r"파일.*생성", r"문서.*만들", r"노트.*작성", r"create.*file"
            ],
            "question_answer": [
                r".*어떻게", r".*방법", r".*뭐야", r".*무엇", r"what.*", r"how.*"
            ]
        }
        
        self.response_templates = {
            "code_analysis": [
                "코드 분석을 시작하겠습니다! 현재 활성 파일을 분석하고 있어요.",
                "파일 분석 기능을 실행합니다. 잠시만 기다려 주세요.",
                "코드 구조와 품질을 분석해 드리겠습니다."
            ],
            "hero_summon": [
                "🦸 영웅을 소환하고 있습니다! Super Heroic Agent가 곧 나타날 거예요.",
                "강력한 AI 에이전트를 호출하겠습니다. 준비 완료!",
                "특별한 미션을 위해 영웅을 소환합니다!"
            ],
            "dashboard_open": [
                "대시보드를 열어드리겠습니다. 시스템 상태를 확인하실 수 있어요.",
                "AI 시스템 모니터링 대시보드로 이동합니다.",
                "현재 시스템 상태와 성능을 확인해 보세요!"
            ],
            "greeting": [
                "안녕하세요! 무엇을 도와드릴까요? 😊",
                "반갑습니다! 저는 여러분의 AI 비서입니다.",
                "안녕하세요! 코딩, 분석, 일정 관리 등 무엇이든 도와드릴게요!"
            ]
        }
        
    async def process(self, user_input: str) -> Dict[str, Any]:
        """자연어 입력 처리"""
        user_input = user_input.lower().strip()
        
        # 의도 분석
        intent = self.analyze_intent(user_input)
        
        # 엔티티 추출
        entities = self.extract_entities(user_input)
        
        # 응답 생성
        response_data = await self.generate_response_for_intent(intent, entities, user_input)
        
        return {
            "intent": intent,
            "entities": entities,
            "response": response_data["response"],
            "action": response_data.get("action"),
            "confidence": response_data.get("confidence", 0.8)
        }
        
    def analyze_intent(self, user_input: str) -> str:
        """의도 분석"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return intent
                    
        # 인사말 감지
        greetings = ["안녕", "hello", "hi", "반가", "좋은"]
        if any(greeting in user_input for greeting in greetings):
            return "greeting"
            
        return "question_answer"
        
    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """엔티티 추출"""
        entities = {}
        
        # 파일 확장자 감지
        file_extensions = re.findall(r'\\.([a-zA-Z0-9]+)', user_input)
        if file_extensions:
            entities["file_types"] = file_extensions
            
        # 숫자 감지
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
            
        # 시간 표현 감지
        time_expressions = re.findall(r'(\d{1,2}:\d{2}|\d{1,2}시)', user_input)
        if time_expressions:
            entities["times"] = time_expressions
            
        return entities
        
    async def generate_response_for_intent(self, intent: str, entities: Dict, user_input: str) -> Dict[str, Any]:
        """의도별 응답 생성"""
        import random
        
        if intent in self.response_templates:
            response = random.choice(self.response_templates[intent])
        else:
            response = "네, 이해했습니다. 해당 작업을 처리해 드리겠습니다."
            
        action = None
        confidence = 0.8
        
        # 액션 매핑
        if intent == "code_analysis":
            action = {"type": "analyze_file"}
            confidence = 0.9
        elif intent == "hero_summon":
            action = {"type": "summon_hero"}
            confidence = 0.95
        elif intent == "dashboard_open":
            action = {"type": "open_dashboard"}
            confidence = 0.9
            
        return {
            "response": response,
            "action": action,
            "confidence": confidence
        }
        
    async def generate_response(self, message: str, context: Dict = None, history: List = None) -> Dict[str, Any]:
        """대화형 응답 생성"""
        # 간단한 대화형 응답 (실제로는 더 정교한 모델 사용)
        suggestions = [
            "코드를 분석해 드릴까요?",
            "영웅을 소환해 보시겠어요?",
            "대시보드를 확인해 보세요!",
            "다른 도움이 필요하시면 말씀해 주세요."
        ]
        
        # 컨텍스트 기반 응답 개선
        if context and "current_file" in context:
            suggestions.insert(0, f"{context['current_file']} 파일을 분석해 드릴까요?")
            
        return {
            "message": "네, 무엇을 도와드릴까요? 아래 제안들을 참고해 보세요.",
            "suggestions": suggestions[:3]  # 최대 3개 제안
        }

class LogMonitor:
    """로그 모니터"""
    
    def __init__(self):
        self.log_history = []
        self.max_history = 1000
        
    def add_log(self, level: str, source: str, message: str):
        """로그 추가"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "source": source,
            "message": message
        }
        
        self.log_history.append(log_entry)
        
        # 히스토리 크기 제한
        if len(self.log_history) > self.max_history:
            self.log_history = self.log_history[-self.max_history:]
            
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """최근 로그 가져오기"""
        return self.log_history[-limit:] if limit > 0 else self.log_history

def start_background_tasks(server):
    """백그라운드 작업 시작"""
    def log_system_stats():
        """시스템 통계 로깅"""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=5)
                memory = psutil.virtual_memory()
                
                if cpu_percent > 80:
                    server.add_log("warning", "system", f"높은 CPU 사용률: {cpu_percent:.1f}%")
                    
                if memory.percent > 85:
                    server.add_log("warning", "system", f"높은 메모리 사용률: {memory.percent:.1f}%")
                    
                server.add_log("info", "system", f"시스템 상태: CPU {cpu_percent:.1f}%, 메모리 {memory.percent:.1f}%")
                
            except Exception as e:
                server.add_log("error", "system", f"시스템 모니터링 오류: {e}")
                
            time.sleep(30)  # 30초마다 체크
            
    # 백그라운드 스레드 시작
    threading.Thread(target=log_system_stats, daemon=True).start()

async def main():
    """메인 실행 함수"""
    import uvicorn
    
    server = EnhancedObsidianAIServer()
    
    # 백그라운드 작업 시작
    start_background_tasks(server)
    
    # 초기 로그
    server.add_log("info", "startup", "Enhanced Obsidian AI Server v2.0 시작됨")
    server.add_log("info", "features", "자연어 처리, 실시간 로그, 고급 대화모델 활성화")
    
    logger.info("🚀 Enhanced Obsidian AI Server v2.0 시작")
    logger.info("🧠 자연어 처리 엔진 준비 완료")
    logger.info("📊 실시간 로그 모니터링 활성화")
    
    # 서버 실행
    config = uvicorn.Config(
        app=server.app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    
    server_instance = uvicorn.Server(config)
    await server_instance.serve()

if __name__ == "__main__":
    asyncio.run(main())
