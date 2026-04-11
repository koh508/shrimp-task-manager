import asyncio
from typing import Dict, Any, Optional

class LLMStrategy:
    def __init__(self, monthly_budget: float = 100.0):
        self.monthly_budget = monthly_budget  # 월간 예산 (예: 100,000원 -> 100.0 USD 가정)
        self.current_cost = 0.0
        self.llm_costs = {
            "Gemini-Flash": 0.000007,  # 예시: 저비용 LLM 토큰당 비용 (USD)
            "Claude-3-Opus": 0.000075, # 예시: 고비용 LLM 토큰당 비용 (USD)
        }
        self.logger = print # 간단한 로깅을 위해 print 사용

    async def _simulate_llm_call(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """LLM 호출을 시뮬레이션하고 비용을 계산합니다."""
        token_count = len(prompt.split()) # 간단한 토큰 계산
        cost_per_token = self.llm_costs.get(model_name, 0.0)
        estimated_cost = token_count * cost_per_token

        if self.current_cost + estimated_cost > self.monthly_budget:
            self.logger(f"⚠️ 경고: 월간 예산 초과 예상! 현재 비용: ${self.current_cost:.2f}, 예상 추가 비용: ${estimated_cost:.2f}")
            # 실제 환경에서는 여기서 호출을 중단하거나 사용자에게 알림

        self.current_cost += estimated_cost
        self.logger(f"💸 {model_name} 호출 - 토큰: {token_count}, 예상 비용: ${estimated_cost:.6f}, 누적 비용: ${self.current_cost:.2f}")

        # 스로틀링 (간단한 지연)
        await asyncio.sleep(0.1) # 100ms 지연

        # 시뮬레이션 응답
        if "fail" in prompt.lower():
            return {"status": "failed", "message": f"Simulated failure for {model_name}"}
        return {"status": "success", "response": f"Response from {model_name} for: {prompt}"}

    async def execute_llm_call(self, prompt: str, preferred_model: str = "Gemini-Flash") -> Dict[str, Any]:
        """
        계층적 LLM 선택 및 실행 로직.
        저비용 LLM을 우선 사용하고, 실패 시 고비용 LLM으로 전환합니다.
        """
        self.logger(f"🚀 LLM 호출 시도 (선호 모델: {preferred_model})")

        # 1단계: 저비용 LLM 시도
        result = await self._simulate_llm_call(preferred_model, prompt)
        if result["status"] == "success":
            return result
        else:
            self.logger(f"❌ {preferred_model} 실패. Claude-3-Opus로 전환 시도...")
            # 2단계: 고비용 LLM으로 전환
            fallback_model = "Claude-3-Opus"
            result = await self._simulate_llm_call(fallback_model, prompt)
            if result["status"] == "success":
                return result
            else:
                self.logger(f"🚨 {fallback_model}도 실패했습니다. 사용자에게 보고합니다.")
                return {"status": "final_failed", "message": f"Both models failed: {result['message']}"}

    def get_current_cost(self) -> float:
        return self.current_cost

    def reset_monthly_cost(self):
        self.current_cost = 0.0
        self.logger("💰 월간 비용이 초기화되었습니다.")

