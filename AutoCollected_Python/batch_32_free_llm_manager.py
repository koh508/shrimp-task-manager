#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🆓 Free LLM Manager
===================
무료 LLM 서비스들을 통합 관리하는 시스템
- Ollama (로컬 실행)
- Hugging Face Transformers (로컬 실행)
- OpenAI 호환 무료 API들
- Gemini Fallback (최소 사용)
"""

import asyncio
import json
import logging
import os
import time
import requests
import subprocess
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
import threading

# 설정 클래스
@dataclass
class LLMConfig:
    name: str
    type: str  # 'local', 'api', 'huggingface'
    endpoint: str = None
    model_name: str = None
    api_key: str = None
    max_tokens: int = 2048
    temperature: float = 0.7
    available: bool = False
    cost_per_token: float = 0.0  # 무료는 0

class LLMType(Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    FREE_API = "free_api"
    GEMINI_FALLBACK = "gemini_fallback"

class FreeLLMManager:
    """무료 LLM 통합 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_configs = []
        self.current_llm = None
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cost_saved': 0.0
        }
        self.setup_free_llms()
    
    def setup_free_llms(self):
        """무료 LLM 설정 초기화"""
        
        # 1. Ollama (로컬 LLM - 완전 무료)
        ollama_config = LLMConfig(
            name="Ollama Llama3",
            type="ollama",
            endpoint="http://localhost:11434/api/generate",
            model_name="llama3",
            cost_per_token=0.0
        )
        
        # 2. Hugging Face 로컬 모델들
        hf_configs = [
            LLMConfig(
                name="Microsoft DialoGPT",
                type="huggingface",
                model_name="microsoft/DialoGPT-large",
                cost_per_token=0.0
            ),
            LLMConfig(
                name="GPT-2 Large",
                type="huggingface", 
                model_name="gpt2-large",
                cost_per_token=0.0
            ),
            LLMConfig(
                name="DistilBERT Base",
                type="huggingface",
                model_name="distilbert-base-uncased",
                cost_per_token=0.0
            )
        ]
        
        # 3. 무료 API 서비스들
        free_api_configs = [
            LLMConfig(
                name="Together AI Free",
                type="free_api",
                endpoint="https://api.together.xyz/inference",
                model_name="togethercomputer/llama-2-7b-chat",
                api_key=os.getenv('TOGETHER_API_KEY', ''),
                cost_per_token=0.0
            ),
            LLMConfig(
                name="Cohere Free Tier",
                type="free_api", 
                endpoint="https://api.cohere.ai/v1/generate",
                model_name="command-light",
                api_key=os.getenv('COHERE_API_KEY', ''),
                cost_per_token=0.0
            )
        ]
        
        # 4. Gemini Fallback (최소 사용)
        gemini_fallback = LLMConfig(
            name="Gemini Fallback",
            type="gemini_fallback",
            endpoint="gemini",
            model_name="gemini-1.5-flash",
            api_key=os.getenv('GEMINI_API_KEY', ''),
            cost_per_token=0.000001  # 매우 적은 비용
        )
        
        self.llm_configs = [ollama_config] + hf_configs + free_api_configs + [gemini_fallback]
        
        # 사용 가능한 LLM들 확인
        self.check_llm_availability()
    
    def check_llm_availability(self):
        """각 LLM의 사용 가능 여부 확인"""
        self.logger.info("🔍 무료 LLM 가용성 확인 중...")
        
        for config in self.llm_configs:
            try:
                if config.type == "ollama":
                    config.available = self._check_ollama_available(config)
                elif config.type == "huggingface":
                    config.available = self._check_huggingface_available(config)
                elif config.type == "free_api":
                    config.available = self._check_free_api_available(config)
                elif config.type == "gemini_fallback":
                    config.available = bool(config.api_key)
                
                if config.available:
                    self.logger.info(f"✅ {config.name} 사용 가능")
                else:
                    self.logger.warning(f"❌ {config.name} 사용 불가")
                    
            except Exception as e:
                self.logger.warning(f"❌ {config.name} 확인 실패: {e}")
                config.available = False
        
        # 우선순위에 따라 현재 LLM 선택
        self.select_best_available_llm()
    
    def _check_ollama_available(self, config: LLMConfig) -> bool:
        """Ollama 가용성 확인"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model.get('name', '').startswith(config.model_name) for model in models)
            return False
        except:
            return False
    
    def _check_huggingface_available(self, config: LLMConfig) -> bool:
        """Hugging Face 로컬 모델 가용성 확인 (가벼운 방식)"""
        try:
            # 가벼운 토크나이저만 확인 (모델 로드 없이)
            import requests
            response = requests.get(f"https://huggingface.co/{config.model_name}", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _check_free_api_available(self, config: LLMConfig) -> bool:
        """무료 API 서비스 가용성 확인"""
        if not config.api_key:
            return False
        
        try:
            # 간단한 ping 테스트
            response = requests.get(config.endpoint.replace('/generate', '/health'), timeout=5)
            return response.status_code < 500
        except:
            return False
    
    def select_best_available_llm(self):
        """사용 가능한 최적의 LLM 선택 (우선순위: 로컬 > 무료 API > Gemini)"""
        available_llms = [llm for llm in self.llm_configs if llm.available]
        
        if not available_llms:
            self.logger.error("❌ 사용 가능한 LLM이 없습니다!")
            return
        
        # 우선순위: Ollama > HuggingFace > Free API > Gemini
        priority_order = ["ollama", "huggingface", "free_api", "gemini_fallback"]
        
        for llm_type in priority_order:
            for llm in available_llms:
                if llm.type == llm_type:
                    self.current_llm = llm
                    self.logger.info(f"🎯 선택된 LLM: {llm.name} ({llm.type})")
                    return
        
        # 폴백: 첫 번째 사용 가능한 LLM
        self.current_llm = available_llms[0]
        self.logger.info(f"🎯 폴백 LLM: {self.current_llm.name}")
    
    async def generate_response(self, prompt: str, context: Dict = None) -> str:
        """무료 LLM으로 응답 생성"""
        if not self.current_llm:
            return "❌ 사용 가능한 LLM이 없습니다."
        
        self.usage_stats['total_requests'] += 1
        
        try:
            if self.current_llm.type == "ollama":
                response = await self._generate_ollama_response(prompt)
            elif self.current_llm.type == "huggingface":
                response = await self._generate_huggingface_response(prompt)
            elif self.current_llm.type == "free_api":
                response = await self._generate_free_api_response(prompt)
            elif self.current_llm.type == "gemini_fallback":
                response = await self._generate_gemini_fallback_response(prompt)
            else:
                response = "❌ 지원하지 않는 LLM 타입입니다."
            
            self.usage_stats['successful_requests'] += 1
            
            # 비용 절약 계산 (Gemini와 비교)
            if self.current_llm.cost_per_token == 0:
                estimated_tokens = len(prompt.split()) + len(response.split())
                self.usage_stats['cost_saved'] += estimated_tokens * 0.000001  # Gemini 추정 비용
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ {self.current_llm.name} 응답 생성 실패: {e}")
            self.usage_stats['failed_requests'] += 1
            
            # 다른 LLM으로 폴백 시도
            return await self._try_fallback_llm(prompt)
    
    async def _generate_ollama_response(self, prompt: str) -> str:
        """Ollama로 응답 생성"""
        try:
            payload = {
                "model": self.current_llm.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.current_llm.temperature,
                    "max_tokens": self.current_llm.max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.current_llm.endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '응답을 받지 못했습니다.')
                    else:
                        raise Exception(f"Ollama API 오류: {response.status}")
                        
        except Exception as e:
            raise Exception(f"Ollama 처리 실패: {e}")
    
    async def _generate_huggingface_response(self, prompt: str) -> str:
        """Hugging Face 로컬 모델로 응답 생성 (가벼운 방식)"""
        try:
            # HuggingFace Inference API 사용 (로컬 설치 없이)
            api_url = f"https://api-inference.huggingface.co/models/{self.current_llm.model_name}"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN', '')}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": self.current_llm.temperature,
                    "return_full_text": False
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and result:
                            return result[0].get('generated_text', '응답을 받지 못했습니다.')
                        return str(result)
                    else:
                        raise Exception(f"HuggingFace API 오류: {response.status}")
                        
        except Exception as e:
            raise Exception(f"HuggingFace API 처리 실패: {e}")
    
    async def _generate_free_api_response(self, prompt: str) -> str:
        """무료 API 서비스로 응답 생성"""
        try:
            headers = {
                "Authorization": f"Bearer {self.current_llm.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.current_llm.model_name,
                "prompt": prompt,
                "max_tokens": self.current_llm.max_tokens,
                "temperature": self.current_llm.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.current_llm.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('choices', [{}])[0].get('text', '응답을 받지 못했습니다.')
                    else:
                        raise Exception(f"Free API 오류: {response.status}")
                        
        except Exception as e:
            raise Exception(f"Free API 처리 실패: {e}")
    
    async def _generate_gemini_fallback_response(self, prompt: str) -> str:
        """Gemini 폴백 응답 (최후의 수단)"""
        try:
            import google.generativeai as genai
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(prompt)
            
            self.logger.warning("💰 Gemini API 사용됨 (비용 발생)")
            return response.text
            
        except Exception as e:
            return f"❌ 모든 LLM 서비스를 사용할 수 없습니다: {e}"
    
    async def _try_fallback_llm(self, prompt: str) -> str:
        """현재 LLM 실패시 다른 LLM으로 폴백"""
        available_llms = [llm for llm in self.llm_configs if llm.available and llm != self.current_llm]
        
        for fallback_llm in available_llms:
            try:
                self.logger.info(f"🔄 {fallback_llm.name}으로 폴백 시도")
                original_llm = self.current_llm
                self.current_llm = fallback_llm
                
                response = await self.generate_response(prompt)
                return f"🔄 {fallback_llm.name}에서 응답:\n{response}"
                
            except Exception as e:
                self.logger.warning(f"❌ {fallback_llm.name} 폴백 실패: {e}")
                continue
            finally:
                self.current_llm = original_llm
        
        return "❌ 모든 무료 LLM 서비스를 사용할 수 없습니다."
    
    def get_usage_stats(self) -> Dict:
        """사용 통계 반환"""
        return {
            **self.usage_stats,
            'current_llm': self.current_llm.name if self.current_llm else None,
            'available_llms': [llm.name for llm in self.llm_configs if llm.available],
            'total_llms': len(self.llm_configs)
        }
    
    def install_ollama_model(self, model_name: str = "llama3") -> bool:
        """Ollama 모델 설치"""
        try:
            self.logger.info(f"📥 Ollama {model_name} 모델 설치 중...")
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ {model_name} 설치 완료")
                return True
            else:
                self.logger.error(f"❌ {model_name} 설치 실패: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Ollama 설치 오류: {e}")
            return False
    
    def get_installation_guide(self) -> str:
        """무료 LLM 설치 가이드"""
        return """
🆓 무료 LLM 설치 가이드

1. **Ollama (추천)** - 완전 무료 로컬 LLM
   ```bash
   # Windows
   winget install ollama
   
   # 모델 설치
   ollama pull llama3
   ollama pull codellama
   ```

2. **Hugging Face 모델** - 로컬 실행
   ```bash
   pip install transformers torch
   ```

3. **무료 API 키 발급**
   - Together AI: https://api.together.xyz (무료 크레딧)
   - Cohere: https://cohere.ai (무료 티어)

4. **환경 변수 설정**
   ```bash
   TOGETHER_API_KEY=your_key_here
   COHERE_API_KEY=your_key_here
   ```
"""

# 전역 인스턴스
_free_llm_manager = None

def get_free_llm_manager() -> FreeLLMManager:
    """무료 LLM 매니저 싱글톤 인스턴스 반환"""
    global _free_llm_manager
    if _free_llm_manager is None:
        _free_llm_manager = FreeLLMManager()
    return _free_llm_manager

# 테스트 실행
if __name__ == "__main__":
    async def test_free_llms():
        manager = get_free_llm_manager()
        
        print("🆓 무료 LLM 테스트")
        print("=" * 50)
        
        # 사용 가능한 LLM 목록
        stats = manager.get_usage_stats()
        print(f"사용 가능한 LLM: {stats['available_llms']}")
        print(f"현재 선택된 LLM: {stats['current_llm']}")
        
        # 테스트 질문
        test_prompt = "안녕하세요! 간단한 파이썬 함수를 만들어주세요."
        
        print(f"\n질문: {test_prompt}")
        print("답변:")
        
        response = await manager.generate_response(test_prompt)
        print(response)
        
        # 사용 통계
        final_stats = manager.get_usage_stats()
        print(f"\n📊 사용 통계:")
        print(f"총 요청: {final_stats['total_requests']}")
        print(f"성공: {final_stats['successful_requests']}")
        print(f"실패: {final_stats['failed_requests']}")
        print(f"절약된 비용: ${final_stats['cost_saved']:.6f}")
    
    # 비동기 실행
    asyncio.run(test_free_llms())
