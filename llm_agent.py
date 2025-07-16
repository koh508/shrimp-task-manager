#!/usr/bin/env python3
"""
LLM 통합 AI 에이전트 시스템
"""
import openai
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os


class LLMAgent:
    """LLM 기반 지능형 에이전트"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.conversation_history = []
        self.system_context = {
            "role": "advanced_development_assistant",
            "capabilities": [
                "code_analysis",
                "debugging",
                "optimization",
                "architecture_design",
                "testing",
                "documentation",
            ],
            "tools": ["github", "railway", "monitoring", "backup"],
        }

        if self.api_key:
            openai.api_key = self.api_key
            self.llm_available = True
        else:
            self.llm_available = False
            print("⚠️ OpenAI API 키가 설정되지 않음 - 로컬 모드로 동작")

    async def analyze_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """코드 분석 및 개선 제안"""
        if not self.llm_available:
            return self.local_code_analysis(code, context)

        try:
            prompt = f"""
            다음 코드를 분석하고 개선 제안을 해주세요:

            컨텍스트: {context}

            코드:
            ```
            {code}
            ```

            다음 관점에서 분석해주세요:
            1. 코드 품질 및 가독성
            2. 성능 최적화 방안
            3. 보안 이슈
            4. 버그 가능성
            5. 리팩토링 제안

            JSON 형식으로 응답해주세요.
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 숙련된 Python 개발자입니다."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            return {
                "analysis": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4",
                "success": True,
            }

        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat(), "success": False}

    def local_code_analysis(self, code: str, context: str = "") -> Dict[str, Any]:
        """로컬 코드 분석 (LLM 없이)"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "model": "local_analyzer",
            "success": True,
            "analysis": {
                "code_quality": self.check_code_quality(code),
                "performance": self.check_performance_issues(code),
                "security": self.check_security_issues(code),
                "bugs": self.check_potential_bugs(code),
                "suggestions": self.generate_suggestions(code),
            },
        }
        return analysis

    def check_code_quality(self, code: str) -> Dict[str, Any]:
        """코드 품질 검사"""
        issues = []

        # 기본적인 품질 체크
        if "import *" in code:
            issues.append("avoid_wildcard_imports")

        if len([line for line in code.split("\n") if line.strip()]) > 50:
            issues.append("function_too_long")

        if "except:" in code:
            issues.append("bare_except_clause")

        return {
            "score": max(0, 100 - len(issues) * 10),
            "issues": issues,
            "suggestions": ["함수를 더 작은 단위로 분할 고려", "명확한 예외 처리 추가", "코드 주석 및 문서화 개선"],
        }

    def check_performance_issues(self, code: str) -> Dict[str, Any]:
        """성능 이슈 검사"""
        issues = []

        if "for" in code and "append" in code:
            issues.append("list_comprehension_opportunity")

        if "time.sleep" in code:
            issues.append("blocking_sleep_call")

        return {"issues": issues, "suggestions": ["리스트 컴프리헨션 사용 고려", "비동기 처리 검토", "캐싱 메커니즘 추가"]}

    def check_security_issues(self, code: str) -> Dict[str, Any]:
        """보안 이슈 검사"""
        issues = []

        if "eval(" in code:
            issues.append("dangerous_eval_usage")

        if "subprocess" in code:
            issues.append("subprocess_security_risk")

        return {"issues": issues, "suggestions": ["입력 검증 강화", "SQL 인젝션 방지", "안전한 파일 처리"]}

    def check_potential_bugs(self, code: str) -> Dict[str, Any]:
        """잠재적 버그 검사"""
        issues = []

        if "mutable" in code.lower() and "default" in code.lower():
            issues.append("mutable_default_argument")

        return {"issues": issues, "suggestions": ["변수 초기화 확인", "타입 힌트 추가", "단위 테스트 작성"]}

    def generate_suggestions(self, code: str) -> List[str]:
        """개선 제안 생성"""
        return ["코드 리뷰 프로세스 적용", "자동화된 테스트 추가", "성능 프로파일링 실행", "보안 스캔 도구 사용", "코드 포맷터 적용"]

    async def generate_test_code(self, function_code: str) -> str:
        """테스트 코드 자동 생성"""
        if not self.llm_available:
            return self.generate_basic_test(function_code)

        try:
            prompt = f"""
            다음 함수에 대한 pytest 테스트 코드를 생성해주세요:

            ```
            {function_code}
            ```

            포함할 요소:
            1. 정상 케이스 테스트
            2. 에지 케이스 테스트
            3. 예외 상황 테스트
            4. 파라미터 검증 테스트

            완전한 테스트 코드만 반환해주세요.
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 테스트 코드 작성 전문가입니다."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.2,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"# 테스트 코드 생성 실패: {str(e)}\n{self.generate_basic_test(function_code)}"

    def generate_basic_test(self, function_code: str) -> str:
        """기본 테스트 코드 생성"""
        return f"""
import pytest
from unittest.mock import Mock, patch

def test_basic_functionality():
    '''기본 기능 테스트'''
    # TODO: 실제 테스트 로직 구현
    assert True

def test_edge_cases():
    '''에지 케이스 테스트'''
    # TODO: 경계값 테스트 구현
    assert True

def test_error_handling():
    '''에러 처리 테스트'''
    # TODO: 예외 상황 테스트 구현
    with pytest.raises(Exception):
        pass

# 생성된 테스트 코드 - 실제 구현 필요
# 함수: {function_code[:100]}...
"""
