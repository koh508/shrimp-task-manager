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
import uvicorn

# MCP Gemini 통합 import
try:
    from gemini_mcp_integration import get_mcp_gemini_integration, process_with_mcp_gemini
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP Gemini 통합을 사용할 수 없습니다. 직접 모드로 실행됩니다.")

# Code Agent 시스템 import
try:
    from code_agent_system import get_code_agent_manager, CodeAgentManager
    CODE_AGENT_AVAILABLE = True
except ImportError:
    CODE_AGENT_AVAILABLE = False
    logging.warning("Code Agent 시스템을 사용할 수 없습니다.")

# Free LLM Manager import
try:
    from free_llm_manager import get_free_llm_manager, FreeLLMManager
    FREE_LLM_AVAILABLE = True
except ImportError:
    FREE_LLM_AVAILABLE = False
    logging.warning("Free LLM Manager를 사용할 수 없습니다.")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('obsidian_ai_enhanced_v3.log', encoding='utf-8'),
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
            "autonomous_learning.log",
            "goal_achievement.log", 
            "evolution_optimizer.log",
            "quantum_intelligence.log",
            "ultra_fast_processing.log",
            "24h_evolution_log.log",
            "rag_conversational_ai.log"
        ]
        
        log_files = []
        for pattern in log_patterns:
            if os.path.exists(pattern) and os.path.getsize(pattern) > 0:
                log_files.append(pattern)
        
        logger.info(f"✅ 발견된 활성 로그 파일들: {len(log_files)}개")
        for file in log_files:
            logger.info(f"   📄 {file}")
        return log_files
    
    def setup_log_watchers(self):
        """로그 파일 감시자 설정"""
        for log_file in self.log_files:
            try:
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
            # 기존 로그 읽기 (최근 50줄)
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    if line.strip():
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'source': os.path.basename(log_file),
                            'level': self._extract_log_level(line),
                            'message': line.strip()
                        }
                        self.current_logs.append(log_entry)
            
            # 실시간 모니터링
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
    """무료 LLM 우선 고급 대화 관리자 (Gemini 폴백)"""
    
    def __init__(self):
        self.model = None
        self.chat_sessions = {}
        self.conversation_history = []
        self.mcp_integration = None
        self.code_agent_manager = None
        self.free_llm_manager = None
        self.initialize_free_llms()
        self.initialize_gemini()
        # LLM 초기화 후에 Code Agent 초기화
        if self.has_available_llm():
            self.initialize_code_agent()
    
    def initialize_code_agent(self):
        """Code Agent 시스템 초기화"""
        try:
            if not CODE_AGENT_AVAILABLE:
                logger.warning("⚠️ Code Agent 시스템을 사용할 수 없습니다 - 모듈을 찾을 수 없음")
                return
                
            # 사용할 모델 결정
            gemini_model = None
            if self.mcp_integration and self.mcp_integration.gemini_model:
                gemini_model = self.mcp_integration.gemini_model
            elif self.model:
                gemini_model = self.model
            
            if gemini_model:
                self.code_agent_manager = get_code_agent_manager(gemini_model)
                logger.info("✅ Code Agent 시스템 초기화 완료")
            else:
                logger.warning("⚠️ Code Agent 시스템을 사용할 수 없습니다 - Gemini 모델이 없음")
        except Exception as e:
            logger.error(f"❌ Code Agent 초기화 실패: {e}")
    
    def initialize_gemini(self):
        """Gemini 모델 초기화 (MCP 우선)"""
        try:
            # MCP 통합 우선 시도
            if MCP_AVAILABLE:
                self.mcp_integration = get_mcp_gemini_integration()
                if self.mcp_integration and self.mcp_integration.gemini_model:
                    logger.info("✅ MCP Gemini 통합 초기화 완료")
                    return True
            
            # 직접 Gemini API 폴백
            if GEMINI_API_KEY:
                self.model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',  # 최신 모델명으로 변경
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                logger.info("✅ Gemini 직접 모델 초기화 완료")
                return True
            else:
                logger.warning("⚠️ Gemini API 키가 없습니다. 시뮬레이션 모드로 동작합니다.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gemini 초기화 실패: {e}")
            return False
    
    def initialize_free_llms(self):
        """무료 LLM 매니저 초기화"""
        try:
            if FREE_LLM_AVAILABLE:
                self.free_llm_manager = get_free_llm_manager()
                stats = self.free_llm_manager.get_usage_stats()
                if stats['available_llms']:
                    logger.info(f"✅ 무료 LLM 초기화 완료: {stats['current_llm']}")
                    logger.info(f"📋 사용 가능한 무료 LLM: {', '.join(stats['available_llms'])}")
                else:
                    logger.warning("⚠️ 사용 가능한 무료 LLM이 없습니다")
            else:
                logger.warning("⚠️ Free LLM Manager를 사용할 수 없습니다")
        except Exception as e:
            logger.error(f"❌ 무료 LLM 초기화 실패: {e}")
    
    def has_available_llm(self) -> bool:
        """사용 가능한 LLM이 있는지 확인"""
        if self.free_llm_manager and self.free_llm_manager.current_llm:
            return True
        if self.model or (self.mcp_integration and self.mcp_integration.gemini_model):
            return True
        return False
    
    async def process_conversation(self, message: str, context: Dict = None) -> str:
        """자연어 대화 처리 (무료 LLM 우선, Gemini 폴백)"""
        try:
            # Code Agent 처리 시도 (코드 관련 요청인지 확인)
            if self.code_agent_manager and self._is_code_request(message):
                try:
                    code_result = await self.code_agent_manager.execute_command(message, context)
                    response = self._format_code_agent_response(code_result)
                    
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'user_message': message,
                        'ai_response': response,
                        'context': context,
                        'method': 'code_agent',
                        'code_result': code_result
                    })
                    
                    return response
                except Exception as e:
                    logger.warning(f"Code Agent 처리 실패, 일반 대화로 전환: {e}")
            
            # 1. 무료 LLM 우선 시도
            if self.free_llm_manager and self.free_llm_manager.current_llm:
                try:
                    enhanced_prompt = self._build_system_prompt(context) + f"\n\n사용자: {message}"
                    response = await self.free_llm_manager.generate_response(enhanced_prompt, context)
                    
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'user_message': message,
                        'ai_response': response,
                        'context': context,
                        'method': f'free_llm_{self.free_llm_manager.current_llm.type}',
                        'llm_used': self.free_llm_manager.current_llm.name,
                        'cost_saved': True
                    })
                    
                    return f"🆓 {self.free_llm_manager.current_llm.name}:\n{response}"
                    
                except Exception as e:
                    logger.warning(f"무료 LLM 처리 실패, 유료 LLM으로 폴백: {e}")
            
            # 2. MCP 통합을 통한 처리 시도
            if self.mcp_integration:
                try:
                    enhanced_context = context or {}
                    enhanced_context['mcp_status'] = self.mcp_integration.get_mcp_status()
                    response = await self.mcp_integration.process_with_smart_llm(message, enhanced_context)
                    
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'user_message': message,
                        'ai_response': response,
                        'context': enhanced_context,
                        'method': 'mcp_gemini',
                        'cost_incurred': True
                    })
                    
                    return f"💰 Gemini (MCP):\n{response}"
                except Exception as e:
                    logger.warning(f"MCP 처리 실패, 직접 모드로 전환: {e}")
            
            # 3. 직접 Gemini API 폴백
            if self.model:
                system_prompt = self._build_system_prompt(context)
                full_message = f"{system_prompt}\n\n사용자: {message}"
                response = await self.model.generate_content_async(full_message)
                
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'user_message': message,
                    'ai_response': response.text,
                    'context': context,
                    'method': 'direct_gemini',
                    'cost_incurred': True
                })
                
                return f"💰 Gemini (직접):\n{response.text}"
            
            # 4. 시뮬레이션 폴백
            return await self._simulate_response(message)
            
        except Exception as e:
            logger.error(f"❌ 대화 처리 오류: {e}")
            return await self._simulate_response(message)
            
        except Exception as e:
            logger.error(f"❌ 대화 처리 오류: {e}")
            return await self._simulate_response(message)
    
    def _is_code_request(self, message: str) -> bool:
        """메시지가 코드 관련 요청인지 판단"""
        code_keywords = [
            '코드', 'code', '프로그램', 'program', '스크립트', 'script',
            '만들어', 'create', '생성', '작성', '실행', 'run', '적용', 'apply',
            '파일', 'file', '저장', 'save', '함수', 'function', '클래스', 'class',
            'python', 'javascript', 'html', 'css', 'json', 'api'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in code_keywords)
    
    def _format_code_agent_response(self, code_result: Dict) -> str:
        """Code Agent 결과를 사용자 친화적으로 포맷팅"""
        if not code_result.get('success'):
            return f"❌ 코드 처리 중 오류가 발생했습니다: {code_result.get('error', '알 수 없는 오류')}"
        
        response_parts = []
        
        # 명령 타입에 따른 응답
        command_type = code_result.get('command_type', 'unknown')
        
        if command_type == 'code_request':
            analysis = code_result.get('analysis', {})
            execution = code_result.get('execution')
            application = code_result.get('application')
            
            response_parts.append("🤖 **코드 생성 완료!**")
            
            if analysis.get('analysis'):
                response_parts.append(f"📝 **분석**: {analysis['analysis']}")
            
            if analysis.get('code'):
                response_parts.append("💻 **생성된 코드**:")
                response_parts.append(f"```python\n{analysis['code']}\n```")
            
            if execution:
                if execution.get('success'):
                    response_parts.append("✅ **실행 결과**: 성공적으로 실행되었습니다!")
                    if execution.get('output'):
                        response_parts.append(f"📤 **출력**:\n```\n{execution['output']}\n```")
                else:
                    response_parts.append(f"❌ **실행 오류**: {execution.get('error', '알 수 없는 오류')}")
            
            if application:
                if application.get('success'):
                    response_parts.append(f"💾 **파일 저장**: {application['file_path']}")
                    response_parts.append(f"📊 **파일 크기**: {application.get('file_size', 0)} bytes")
                else:
                    response_parts.append(f"❌ **저장 오류**: {application.get('error', '알 수 없는 오류')}")
            
            if analysis.get('expected_result'):
                response_parts.append(f"🎯 **예상 결과**: {analysis['expected_result']}")
        
        elif command_type == 'project_status':
            status = code_result.get('project_status', {})
            response_parts.append("📊 **프로젝트 상태**")
            response_parts.append(f"📁 생성된 파일: {status.get('total_files', 0)}개")
            
            created_files = status.get('created_files', {})
            if created_files:
                response_parts.append("\n📄 **생성된 파일 목록**:")
                for file_path, info in created_files.items():
                    response_parts.append(f"- {file_path} (크기: {info.get('size', 0)} bytes)")
        
        elif command_type == 'help':
            help_text = code_result.get('help', '')
            response_parts.append(help_text)
        
        else:
            response_parts.append(f"ℹ️ 처리 완료: {code_result.get('message', '명령이 처리되었습니다.')}")
        
        return "\n\n".join(response_parts)
    
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
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['로그', 'log', '기록']):
            return "🔍 실시간 로그 모니터링 중입니다. 현재 여러 AI 에이전트들이 활발히 학습하고 진화하고 있어요!"
        
        elif any(word in message_lower for word in ['에이전트', 'agent', '상태']):
            return "🤖 현재 자율학습, 목표달성, 진화 최적화 등 다양한 AI 에이전트들이 24시간 연속 운영 중입니다!"
        
        elif any(word in message_lower for word in ['안녕', 'hello', '헬로']):
            return "👋 안녕하세요! AI 에이전트 시스템 어시스턴트입니다. 로그 확인이나 에이전트 상태에 대해 궁금한 것이 있으시면 언제든 물어보세요!"
        
        else:
            return f"💭 '{message}'에 대해 이해했습니다. 더 구체적인 정보가 필요하시면 'Gemini API 키'를 설정해주세요!"

# 간단한 자연어 처리기 (기존 호환성용)
class NaturalLanguageProcessor:
    def analyze(self, text: str) -> Dict:
        """간단한 자연어 분석"""
        intent_patterns = {
            "로그 조회": ["로그", "log", "기록", "상태"],
            "에이전트 상태": ["에이전트", "agent", "상태", "진행"],
            "대화": ["안녕", "hello", "대화", "chat"]
        }
        
        detected_intent = "대화"
        for intent, keywords in intent_patterns.items():
            if any(keyword in text.lower() for keyword in keywords):
                detected_intent = intent
                break
        
        return {
            "intent": detected_intent,
            "entities": [],
            "suggestions": ["로그 확인해줘", "에이전트 상태는?", "최근 활동 보여줘"]
        }

class EnhancedObsidianAIServerV3:
    """향상된 옵시디언 AI 서버 v3.0"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Enhanced Obsidian AI Server",
            description="실제 AI 에이전트 로그 연동과 Gemini LLM 고급 대화 지원",
            version="3.0.0"
        )
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
            """메인 웹 인터페이스"""
            html_content = """
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>🧠 Enhanced Obsidian AI Server v3.0</title>
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
                    .status {
                        background: rgba(76, 175, 80, 0.3);
                        border: 2px solid #4caf50;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 20px 0;
                        text-align: center;
                    }
                    .chat-area {
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
                        margin: 5px;
                    }
                    .response-area {
                        background: rgba(0, 0, 0, 0.3);
                        border-radius: 10px;
                        padding: 15px;
                        margin: 15px 0;
                        min-height: 100px;
                        color: #e0e0e0;
                    }
                    .logs-area {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        margin: 30px 0;
                        max-height: 400px;
                        overflow-y: auto;
                    }
                    .log-entry {
                        background: rgba(0, 0, 0, 0.2);
                        border-radius: 5px;
                        padding: 10px;
                        margin: 5px 0;
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                    }
                    .log-level-INFO { border-left: 4px solid #2196F3; }
                    .log-level-ERROR { border-left: 4px solid #f44336; }
                    .log-level-WARNING { border-left: 4px solid #ff9800; }
                </style>
                <script>
                    let ws = null;
                    
                    function connectWebSocket() {
                        try {
                            ws = new WebSocket('ws://localhost:8001/api/logs/stream');
                            
                            ws.onopen = function() {
                                console.log('WebSocket 연결됨');
                                document.getElementById('wsStatus').textContent = '🟢 실시간 연결됨';
                            };
                            
                            ws.onmessage = function(event) {
                                const data = JSON.parse(event.data);
                                if (data.type === 'new_log') {
                                    addLogEntry(data.log);
                                } else if (data.type === 'initial') {
                                    const logsArea = document.getElementById('logsArea');
                                    logsArea.innerHTML = '<h3>📊 실시간 로그 스트림</h3>';
                                    data.logs.forEach(log => addLogEntry(log));
                                }
                            };
                            
                            ws.onclose = function() {
                                document.getElementById('wsStatus').textContent = '🔴 연결 끊김';
                                setTimeout(connectWebSocket, 3000);
                            };
                        } catch (e) {
                            console.error('WebSocket 연결 실패:', e);
                        }
                    }
                    
                    function addLogEntry(log) {
                        const logsArea = document.getElementById('logsArea');
                        const logDiv = document.createElement('div');
                        logDiv.className = `log-entry log-level-${log.level}`;
                        logDiv.innerHTML = `
                            <strong>[${log.timestamp.slice(11, 19)}]</strong> 
                            <span style="color: #64b5f6;">${log.source}</span>: 
                            ${log.message}
                        `;
                        logsArea.appendChild(logDiv);
                        
                        // 최대 50개 로그만 표시
                        const entries = logsArea.querySelectorAll('.log-entry');
                        if (entries.length > 50) {
                            entries[0].remove();
                        }
                        
                        logsArea.scrollTop = logsArea.scrollHeight;
                    }
                    
                    async function sendMessage() {
                        const input = document.getElementById('chatInput');
                        const responseArea = document.getElementById('responseArea');
                        
                        if (!input.value.trim()) return;
                        
                        const message = input.value;
                        input.value = '';
                        
                        responseArea.innerHTML = '<div>🤔 처리 중...</div>';
                        
                        try {
                            const response = await fetch('/chat', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    message: message,
                                    context: {}
                                })
                            });
                            
                            const data = await response.json();
                            
                            responseArea.innerHTML = `
                                <div><strong>사용자:</strong> ${message}</div>
                                <div style="margin-top: 10px;"><strong>AI:</strong> ${data.response}</div>
                                ${data.log_summary ? `<div style="margin-top: 10px; font-size: 12px; color: #aaa;">
                                    📊 시스템 상태: ${data.log_summary.total_logs}개 로그, ${data.log_summary.active_agents}개 활성 에이전트
                                </div>` : ''}
                            `;
                        } catch (error) {
                            responseArea.innerHTML = `<div style="color: #f44336;">오류: ${error}</div>`;
                        }
                    }
                    
                    function quickMessage(message) {
                        document.getElementById('chatInput').value = message;
                        sendMessage();
                    }
                    
                    window.onload = function() {
                        connectWebSocket();
                        updateMCPStatus();
                        
                        document.getElementById('chatInput').addEventListener('keypress', function(e) {
                            if (e.key === 'Enter') {
                                sendMessage();
                            }
                        });
                    };
                    
                    function updateMCPStatus() {
                        fetch('/api/mcp/status')
                            .then(response => response.json())
                            .then(data => {
                                const mcpStatusEl = document.getElementById('mcpStatus');
                                if (data.status === 'active') {
                                    mcpStatusEl.innerHTML = '🟢 MCP Shrimp Task Manager 연결됨';
                                    mcpStatusEl.style.color = '#4caf50';
                                } else if (data.status === 'disabled') {
                                    mcpStatusEl.innerHTML = '🔴 MCP 비활성화 (직접 모드)';
                                    mcpStatusEl.style.color = '#ff9800';
                                } else {
                                    mcpStatusEl.innerHTML = '🔴 MCP 연결 실패 (직접 모드)';
                                    mcpStatusEl.style.color = '#f44336';
                                }
                            })
                            .catch(e => {
                                document.getElementById('mcpStatus').innerHTML = '🔴 MCP 상태 확인 실패';
                            });
                    }
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🧠 Enhanced Obsidian AI Server v3.0</h1>
                        <p>실제 AI 에이전트 로그 연동 • Gemini LLM 고급 대화 • 실시간 모니터링</p>
                        <div id="wsStatus">🟡 연결 중...</div>
                    </div>
                    
                    <div class="status">
                        <h2>🟢 시스템 상태: 정상 운영 중</h2>
                        <p>버전 3.0 • 포트 8001 • MCP Shrimp Task Manager 연동 • Gemini Pro API</p>
                        <div id="mcpStatus">🟡 MCP 상태 확인 중...</div>
                    </div>
                    
                    <div class="chat-area">
                        <h3>💬 고급 AI 대화</h3>
                        <input type="text" id="chatInput" class="chat-input" placeholder="자연어로 명령하거나 질문하세요...">
                        <div>
                            <button class="chat-button" onclick="sendMessage()">전송</button>
                            <button class="chat-button" onclick="quickMessage('최근 로그 보여줘')">로그 확인</button>
                            <button class="chat-button" onclick="quickMessage('에이전트 상태는?')">에이전트 상태</button>
                            <button class="chat-button" onclick="quickMessage('자율학습 로그 보여줘')">자율학습 로그</button>
                        </div>
                        <div id="responseArea" class="response-area">
                            AI 어시스턴트가 준비되었습니다. 무엇을 도와드릴까요?
                        </div>
                    </div>
                    
                    <div class="logs-area" id="logsArea">
                        <h3>📊 실시간 로그 스트림</h3>
                        <div>로그 스트림 연결 중...</div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/health")
        async def health_check():
            """헬스 체크"""
            return {
                "status": "healthy",
                "version": "3.0.0",
                "timestamp": datetime.now().isoformat(),
                "active_log_files": len(self.log_manager.log_files),
                "gemini_status": "active" if self.conversation_manager.model else "simulation"
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
        
        @self.app.post("/api/conversation")
        async def natural_language_conversation(request: NaturalLanguageRequest):
            """자연어 대화 처리 (기존 호환성)"""
            try:
                # 자연어 분석
                analysis = self.natural_language_processor.analyze(request.input)
                
                # 로그 관련 요청인지 확인 (한국어 인코딩 문제 해결)
                log_keywords = ['log', 'LOG', '로그', '기록', '상태', 'status', 'recent', '최근']
                is_log_request = any(keyword in request.input for keyword in log_keywords)
                
                if is_log_request:
                    recent_logs = self.log_manager.get_recent_logs(limit=20)
                    log_summary = self.log_manager.get_log_summary()
                    
                    # 특정 에이전트 로그 요청 확인
                    agent_keywords = {
                        'autonomous': ['자율', 'autonomous'],
                        'evolution': ['진화', 'evolution'],
                        'goal': ['목표', 'goal'],
                        'quantum': ['양자', 'quantum']
                    }
                    
                    requested_agent = None
                    for agent_type, keywords in agent_keywords.items():
                        if any(keyword in request.input for keyword in keywords):
                            requested_agent = agent_type
                            break
                    
                    if requested_agent:
                        filtered_logs = self.log_manager.get_recent_logs(limit=50, agent_type=requested_agent)
                        response_text = f"🔍 '{requested_agent}' 관련 최근 로그 {len(filtered_logs)}개를 찾았습니다.\n\n"
                        for log in filtered_logs[-5:]:  # 최근 5개만 표시
                            response_text += f"[{log['timestamp'][:19]}] {log['source']}: {log['message'][:100]}...\n"
                    else:
                        response_text = f"📊 전체 시스템 로그 요약:\n\n"
                        response_text += f"• 총 로그: {log_summary['total_logs']}개\n"
                        response_text += f"• 활성 에이전트: {log_summary['active_agents']}개\n"
                        response_text += f"• {log_summary['recent_activity']}\n\n"
                        response_text += "최근 활동:\n"
                        for log in recent_logs[-3:]:
                            response_text += f"[{log['timestamp'][:19]}] {log['source']}: {log['message'][:80]}...\n"
                else:
                    # 일반 대화는 Gemini로 처리
                    context = {
                        'command_type': analysis.get('intent', 'general'),
                        'entities': analysis.get('entities', [])
                    }
                    response_text = await self.conversation_manager.process_conversation(
                        request.input, 
                        context
                    )
                
                return {
                    "response": response_text,
                    "intent": analysis.get("intent", "conversation"),
                    "entities": analysis.get("entities", []),
                    "suggestions": analysis.get("suggestions", []),
                    "timestamp": request.timestamp,
                    "context": request.context
                }
                
            except Exception as e:
                logger.error(f"❌ 자연어 처리 오류: {e}")
                return {
                    "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                    "intent": "error",
                    "entities": [],
                    "suggestions": [],
                    "timestamp": request.timestamp,
                    "context": request.context
                }
        
        @self.app.get("/api/logs/recent")
        async def get_recent_logs(limit: int = 100, agent_type: str = None):
            """최근 로그 조회"""
            try:
                logs = self.log_manager.get_recent_logs(limit=limit, agent_type=agent_type)
                summary = self.log_manager.get_log_summary()
                
                return {
                    "logs": logs,
                    "summary": summary,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"❌ 로그 조회 오류: {e}")
                return {
                    "logs": [],
                    "summary": {},
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.websocket("/api/logs/stream")
        async def log_stream_websocket(websocket: WebSocket):
            """실시간 로그 스트리밍"""
            await websocket.accept()
            self.active_connections.add(websocket)
            logger.info("🔗 새 웹소켓 연결")
            
            try:
                # 연결 즉시 최근 로그 전송
                recent_logs = self.log_manager.get_recent_logs(limit=20)
                await websocket.send_json({
                    "type": "initial",
                    "logs": recent_logs,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 실시간 로그 스트리밍
                while True:
                    try:
                        # 큐에서 새 로그 확인
                        log_entry = log_queue.get_nowait()
                        await websocket.send_json({
                            "type": "new_log",
                            "log": log_entry,
                            "timestamp": datetime.now().isoformat()
                        })
                    except queue.Empty:
                        # 연결 상태 확인을 위한 ping
                        await websocket.send_json({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        })
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"❌ 웹소켓 전송 오류: {e}")
                        break
                        
            except WebSocketDisconnect:
                logger.info("📡 웹소켓 연결 종료")
            except Exception as e:
                logger.error(f"❌ 웹소켓 오류: {e}")
            finally:
                self.active_connections.discard(websocket)
        
        @self.app.get("/api/mcp/status")
        async def get_mcp_status():
            """MCP 상태 조회"""
            try:
                if hasattr(self.conversation_manager, 'mcp_integration') and self.conversation_manager.mcp_integration:
                    mcp_status = self.conversation_manager.mcp_integration.get_mcp_status()
                    return {
                        "status": "active" if mcp_status.get('status') != 'error' else "error",
                        "mcp_details": mcp_status,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "disabled",
                        "message": "MCP 통합이 비활성화되어 있습니다",
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"MCP 상태 확인 오류: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/status")
        async def get_status():
            """시스템 상태 조회"""
            log_summary = self.log_manager.get_log_summary()
            
            # MCP 상태 확인
            mcp_status = "disabled"
            if hasattr(self.conversation_manager, 'mcp_integration') and self.conversation_manager.mcp_integration:
                mcp_details = self.conversation_manager.mcp_integration.get_mcp_status()
                mcp_status = "active" if mcp_details.get('status') != 'error' else "error"
            
            return {
                "server_status": "running",
                "version": "3.0.0",
                "log_files": self.log_manager.log_files,
                "log_summary": log_summary,
                "gemini_status": "active" if self.conversation_manager.model or (hasattr(self.conversation_manager, 'mcp_integration') and self.conversation_manager.mcp_integration) else "simulation",
                "mcp_status": mcp_status,
                "active_connections": len(self.active_connections),
                "timestamp": datetime.now().isoformat()
            }

# 서버 실행
def create_app():
    server = EnhancedObsidianAIServerV3()
    return server.app

if __name__ == "__main__":
    logger.info("🚀 Enhanced Obsidian AI Server v3.0 시작")
    
    app = create_app()
    
    # uvicorn으로 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )
