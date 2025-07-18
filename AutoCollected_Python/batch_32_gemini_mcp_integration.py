#!/usr/bin/env python3
"""
Gemini MCP Integration + Free LLM Support for Shrimp Task Manager  
쉬림프 태스크 매니저를 통한 Gemini API 연동 + 무료 LLM 지원
"""

import asyncio
import json
import logging
import requests
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
import aiohttp

# Free LLM Manager import
try:
    from free_llm_manager import get_free_llm_manager
    FREE_LLM_AVAILABLE = True
except ImportError:
    FREE_LLM_AVAILABLE = False

# 환경 변수 로드
load_dotenv()

class ShrimpMCPGeminiIntegration:
    """쉬림프 MCP를 통한 Gemini API 연동"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyAkypgSS2fZ9c2oqiFpe0QYPefRUwtNzb0')
        self.shrimp_url = os.getenv('SHRIMP_MCP_URL', 'http://localhost:8000')
        self.mcp_enabled = os.getenv('SHRIMP_MCP_ENABLED', 'true').lower() == 'true'
        
        self.logger = logging.getLogger(__name__)
        self.gemini_model = None
        self.mcp_session = None
        
        # Free LLM Manager 초기화
        self.free_llm_manager = None
        self.free_llm_enabled = os.getenv('FREE_LLM_ENABLED', 'true').lower() == 'true'
        
        self.initialize_gemini()
        self.initialize_mcp()
        self.initialize_free_llm()

    def initialize_gemini(self):
        """Gemini API 초기화"""
        try:
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',  # 최신 모델명으로 변경
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                self.logger.info("✅ Gemini API 초기화 완료")
                return True
            else:
                self.logger.warning("⚠️ Gemini API 키가 설정되지 않았습니다")
                return False
        except Exception as e:
            self.logger.error(f"❌ Gemini API 초기화 실패: {e}")
            return False
    
    def initialize_mcp(self):
        """MCP Shrimp Task Manager 연결 초기화"""
        try:
            if not self.mcp_enabled:
                self.logger.info("MCP 비활성화됨")
                return False
            
            # Shrimp MCP 상태 확인 (올바른 엔드포인트 사용)
            response = requests.get(f"{self.shrimp_url}/mcp", timeout=5)
            if response.status_code == 200:
                mcp_info = response.json()
                self.logger.info(f"✅ Shrimp MCP Task Manager 연결됨: {mcp_info}")
                
                # MCP 세션 생성 시도
                try:
                    session_response = requests.post(
                        f"{self.shrimp_url}/mcp/session", 
                        json={"client": "obsidian_ai_server", "capabilities": ["gemini_api"]},
                        timeout=5
                    )
                    
                    if session_response.status_code == 200:
                        self.mcp_session = session_response.json().get('session_id')
                        self.logger.info(f"✅ MCP 세션 생성: {self.mcp_session}")
                        return True
                    else:
                        self.logger.warning(f"MCP 세션 생성 실패: {session_response.status_code}")
                        # 세션 없이도 기본 기능 사용 가능
                        return True
                        
                except Exception as session_error:
                    self.logger.warning(f"MCP 세션 생성 실패, 기본 모드로 동작: {session_error}")
                    # 세션 없이도 기본 MCP 연결은 성공으로 처리
                    return True
            else:
                self.logger.warning(f"MCP 응답 오류: {response.status_code}")
                return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ MCP 연결 실패, 직접 모드로 전환: {e}")
            self.mcp_enabled = False
            return False
    
    def initialize_free_llm(self):
        """무료 LLM 매니저 초기화"""
        try:
            if FREE_LLM_AVAILABLE and self.free_llm_enabled:
                self.free_llm_manager = get_free_llm_manager()
                self.logger.info("✅ 무료 LLM 매니저 초기화 완료")
                return True
            else:
                self.logger.info("⚠️ 무료 LLM 비활성화 또는 모듈 없음")
                return False
        except Exception as e:
            self.logger.error(f"❌ 무료 LLM 초기화 실패: {e}")
            return False

    async def process_with_gemini(self, message: str, context: Dict = None) -> str:
        """Gemini를 통한 메시지 처리"""
        try:
            if not self.gemini_model:
                return "Gemini API가 초기화되지 않았습니다."
            
            # 컨텍스트 기반 프롬프트 생성
            system_prompt = self._build_system_prompt(context)
            full_prompt = f"{system_prompt}\n\n사용자: {message}"
            
            # MCP를 통한 처리 시도
            if self.mcp_enabled and self.mcp_session:
                try:
                    return await self._process_via_mcp(full_prompt, context)
                except Exception as e:
                    self.logger.warning(f"MCP 처리 실패, 직접 처리로 전환: {e}")
            
            # 직접 Gemini API 호출
            response = await self.gemini_model.generate_content_async(full_prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"❌ Gemini 처리 오류: {e}")
            return f"처리 중 오류가 발생했습니다: {str(e)}"
    
    async def _process_via_mcp(self, prompt: str, context: Dict = None) -> str:
        """MCP를 통한 Gemini 처리"""
        try:
            # MCP 태스크 생성
            task_data = {
                "session_id": self.mcp_session,
                "task_type": "gemini_generation",
                "prompt": prompt,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # MCP 태스크 전송
            response = requests.post(
                f"{self.shrimp_url}/mcp/tasks",
                json=task_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                
                # 태스크 완료 대기
                return await self._wait_for_mcp_result(task_id)
            else:
                raise Exception(f"MCP 태스크 생성 실패: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"MCP 처리 오류: {e}")
            raise e
    
    async def _wait_for_mcp_result(self, task_id: str, timeout: int = 30) -> str:
        """MCP 태스크 결과 대기"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            try:
                response = requests.get(f"{self.shrimp_url}/mcp/tasks/{task_id}")
                
                if response.status_code == 200:
                    task_result = response.json()
                    status = task_result.get('status')
                    
                    if status == 'completed':
                        return task_result.get('result', {}).get('generated_text', '')
                    elif status == 'failed':
                        raise Exception(f"MCP 태스크 실패: {task_result.get('error')}")
                    
                # 아직 처리 중이면 잠시 대기
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"MCP 결과 확인 오류: {e}")
                break
        
        raise Exception("MCP 태스크 타임아웃")
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """시스템 프롬프트 생성"""
        base_prompt = """당신은 고급 AI 에이전트 시스템의 전문 어시스턴트입니다.

주요 역할:
- AI 에이전트들의 로그와 활동을 모니터링하고 분석
- 사용자의 자연어 명령을 이해하고 적절히 응답
- Shrimp MCP Task Manager를 통한 태스크 관리 지원
- 시스템 상태와 에이전트 성능에 대한 인사이트 제공
- 한국어로 친근하고 전문적인 응답

현재 시스템 상태:
- MCP Shrimp Task Manager 연동 활성화
- 실시간 AI 에이전트 모니터링
- Gemini Pro 모델 활용한 고급 대화"""

        if context:
            if context.get('log_data'):
                base_prompt += f"\n\n최근 로그 정보:\n{context['log_data']}"
            if context.get('mcp_status'):
                base_prompt += f"\n\nMCP 상태: {context['mcp_status']}"
            if context.get('command_type'):
                base_prompt += f"\n\n요청 유형: {context['command_type']}"
        
        return base_prompt
    
    def get_mcp_status(self) -> Dict:
        """MCP 및 무료 LLM 상태 조회"""
        try:
            status_info = {
                "mcp_status": "disabled",
                "free_llm_status": "disabled",
                "available_models": [],
                "cost_savings": 0.0
            }
            
            # MCP 상태 확인
            if self.mcp_enabled:
                response = requests.get(f"{self.shrimp_url}/mcp", timeout=5)
                if response.status_code == 200:
                    mcp_data = response.json()
                    status_info.update({
                        "mcp_status": "active",
                        "mcp_details": mcp_data,
                        "gemini_model": "gemini-1.5-flash" if self.gemini_model else None
                    })
                else:
                    status_info["mcp_status"] = "error"
            
            # 무료 LLM 상태 확인
            if self.free_llm_manager:
                usage_stats = self.free_llm_manager.get_usage_stats()
                status_info.update({
                    "free_llm_status": "active",
                    "available_models": usage_stats['available_llms'],
                    "current_free_llm": usage_stats['current_llm'],
                    "cost_savings": usage_stats['cost_saved'],
                    "free_llm_requests": usage_stats['successful_requests']
                })
            
            return status_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"상태 확인 실패: {str(e)}",
                "mcp_status": "error",
                "free_llm_status": "error"
            }
    
    async def execute_mcp_task(self, task_type: str, task_data: Dict) -> Dict:
        """MCP 태스크 실행"""
        try:
            if not self.mcp_enabled:
                return {"success": False, "error": "MCP가 활성화되지 않았습니다"}
            
            # Shrimp MCP에 태스크 전송 (기본 방식으로 시도)
            task_payload = {
                "task_type": task_type,
                "data": task_data,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.mcp_session:
                task_payload["session_id"] = self.mcp_session
            
            # MCP 태스크 엔드포인트 확인 후 전송
            available_endpoints = ["/mcp/tasks", "/mcp/execute", "/tasks"]
            
            for endpoint in available_endpoints:
                try:
                    response = requests.post(
                        f"{self.shrimp_url}{endpoint}",
                        json=task_payload,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {"success": True, "result": result, "endpoint": endpoint}
                    elif response.status_code == 404:
                        continue  # 다음 엔드포인트 시도
                    else:
                        return {"success": False, "error": f"MCP 태스크 실행 실패: {response.status_code}"}
                        
                except requests.exceptions.RequestException:
                    continue  # 다음 엔드포인트 시도
            
            return {"success": False, "error": "사용 가능한 MCP 태스크 엔드포인트를 찾을 수 없습니다"}
                
        except Exception as e:
            return {"success": False, "error": f"MCP 태스크 실행 오류: {str(e)}"}
    
    async def get_available_mcp_endpoints(self) -> List[str]:
        """MCP에서 사용 가능한 엔드포인트 확인"""
        endpoints = []
        test_endpoints = ["/mcp", "/mcp/status", "/mcp/tasks", "/mcp/session", "/health", "/tasks"]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.shrimp_url}{endpoint}", timeout=3)
                if response.status_code != 404:
                    endpoints.append({"endpoint": endpoint, "status": response.status_code})
            except:
                pass
        
        return endpoints

    async def process_with_smart_llm(self, message: str, context: Dict = None) -> str:
        """스마트 LLM 선택: 무료 LLM 우선 → Gemini 폴백"""
        try:
            # 1. 무료 LLM 시도 (우선순위)
            if self.free_llm_manager:
                try:
                    self.logger.info("🆓 무료 LLM으로 처리 시도")
                    response = await self.free_llm_manager.generate_response(message, context)
                    
                    # 무료 LLM 응답이 유효한지 확인
                    if response and not response.startswith("❌") and len(response) > 10:
                        usage_stats = self.free_llm_manager.get_usage_stats()
                        self.logger.info(f"✅ 무료 LLM 처리 완료 (절약: ${usage_stats['cost_saved']:.6f})")
                        return f"🆓 {usage_stats['current_llm']}에서 응답:\n{response}"
                    else:
                        self.logger.warning("⚠️ 무료 LLM 응답 품질 부족, Gemini로 폴백")
                except Exception as e:
                    self.logger.warning(f"⚠️ 무료 LLM 처리 실패: {e}, Gemini로 폴백")
            
            # 2. Gemini 폴백 (유료)
            self.logger.info("💰 Gemini API 사용 (비용 발생)")
            return await self.process_with_gemini(message, context)
            
        except Exception as e:
            self.logger.error(f"❌ 스마트 LLM 처리 오류: {e}")
            return f"처리 중 오류가 발생했습니다: {str(e)}"

# 전역 인스턴스
mcp_gemini_integration = None

def get_mcp_gemini_integration():
    """MCP Gemini 통합 인스턴스 가져오기"""
    global mcp_gemini_integration
    if mcp_gemini_integration is None:
        mcp_gemini_integration = ShrimpMCPGeminiIntegration()
    return mcp_gemini_integration

async def process_with_mcp_gemini(message: str, context: Dict = None) -> str:
    """MCP Gemini를 통한 메시지 처리 (외부 인터페이스)"""
    integration = get_mcp_gemini_integration()
    return await integration.process_with_gemini(message, context)
