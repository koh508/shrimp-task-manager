#!/usr/bin/env python3
"""
WindSurf API 연동 및 에이전트/로그 생성 시스템
"""
import requests
import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WindSurfIntegration:
    """WindSurf API 연동 및 코드/로그 생성 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: str = "https://api.windsurf.ai/v1/generate"):
        self.api_key = api_key or os.getenv("WINDSURF_API_KEY")
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def analyze_clipping_data(self, clipping_data: Dict[str, Any]) -> Dict[str, Any]:
        """클리핑 데이터 분석 및 생성 요청 데이터 구성"""
        try:
            extracted_text = clipping_data.get("extracted_text", "")
            
            # 텍스트 복잡도 분석 (간단한 예시)
            complexity = len(extracted_text.split()) / 100.0  # 단어 수 기반
            
            # 에이전트 액션 제안
            if "python" in extracted_text.lower() or "def " in extracted_text:
                action_suggestion = "Create a Python agent to automate this task."
                generation_type = "python_agent"
            elif "#" in extracted_text or "-" in extracted_text:
                action_suggestion = "Summarize this content into a Markdown log."
                generation_type = "markdown_log"
            else:
                action_suggestion = "No specific action suggested."
                generation_type = "none"
                
            analysis_result = {
                "complexity": complexity,
                "action_suggestion": action_suggestion,
                "generation_type": generation_type,
                "source_text": extracted_text,
                "metadata": {
                    "clipping_id": clipping_data.get("id"),
                    "timestamp": clipping_data.get("timestamp")
                }
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"클리핑 데이터 분석 실패: {e}")
            return {}

    def generate_python_agent_template(self, analysis_result: Dict[str, Any]) -> str:
        """Python 에이전트 코드 템플릿 생성"""
        return f"""\
# Auto-generated Python Agent by WindSurf
# Generated at: {datetime.now().isoformat()}
# Source Clipping ID: {analysis_result['metadata']['clipping_id']}

import os
import sys

class GeneratedAgent:
    \"\"\"자동 생성된 에이전트 클래스\"\"\"
    
    def __init__(self, source_text):
        self.source_text = source_text
        print("GeneratedAgent 초기화됨")

    def run(self):
        \"\"\"에이전트 실행 로직\"\"\"
        print("에이전트 실행 시작")
        # TODO: Implement agent logic based on the source text
        print("소스 텍스트 기반으로 로직을 구현해야 합니다.")
        print(self.source_text)
        print("에이전트 실행 완료")

if __name__ == "__main__":
    source_content = """{analysis_result['source_text']}"""
    agent = GeneratedAgent(source_content)
    agent.run()
"""

    def generate_markdown_log_template(self, analysis_result: Dict[str, Any]) -> str:
        """Markdown 로그 템플릿 생성"""
        return f"""\
# WindSurf Auto-Generated Log

- **Generated at**: {datetime.now().isoformat()}
- **Source Clipping ID**: {analysis_result['metadata']['clipping_id']}
- **Complexity**: {analysis_result['complexity']:.2f}

## Summary

{analysis_result['action_suggestion']}

## Source Text

```
{analysis_result['source_text']}
```
"""

    def generate_file_from_clipping(self, clipping_data: Dict[str, Any], simulate: bool = False) -> Optional[Dict[str, str]]:
        """클리핑 데이터로부터 파일 생성"""
        try:
            analysis_result = self.analyze_clipping_data(clipping_data)
            if not analysis_result:
                return None

            generation_type = analysis_result.get("generation_type")
            content_to_generate = ""
            file_extension = ""

            if generation_type == "python_agent":
                content_to_generate = self.generate_python_agent_template(analysis_result)
                file_extension = ".py"
            elif generation_type == "markdown_log":
                content_to_generate = self.generate_markdown_log_template(analysis_result)
                file_extension = ".md"
            else:
                logger.info("생성할 파일 타입이 지정되지 않았습니다.")
                return None

            if simulate:
                logger.info("시뮬레이션 모드: API 호출 없이 템플릿만 생성합니다.")
                return {
                    "file_content": content_to_generate,
                    "file_type": generation_type,
                    "file_extension": file_extension
                }

            if not self.api_key:
                logger.error("API 키가 설정되지 않았습니다.")
                return None

            payload = {
                "prompt": content_to_generate,
                "max_tokens": 1024,
                "temperature": 0.7
            }

            logger.info(f"WindSurf API 호출: {self.api_url}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            generated_content = response.json().get("choices", [{}])[0].get("text", "")
            
            return {
                "file_content": generated_content,
                "file_type": generation_type,
                "file_extension": file_extension
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"파일 생성 실패: {e}")
            return None

def main():
    """메인 테스트 함수"""
    print("WindSurf 연동 시스템 테스트")
    print("=" * 50)

    # 테스트용 클리핑 데이터
    sample_clipping_data = {
        'id': 1,
        'timestamp': datetime.now().isoformat(),
        'screenshot_path': 'screenshots/test.png',
        'change_amount': 0.85,
        'extracted_text': 'def process_data(data):\n    # Process the data here\n    print("Processing...")\n    return data',
        'image_hash': 'd41d8cd98f00b204e9800998ecf8427e',
        'detection_method': 'histogram',
        'window_info': (0, 0, 800, 600)
    }

    # WindSurf 연동 인스턴스 생성 (API 키 없이 시뮬레이션 모드로)
    windsurf = WindSurfIntegration()

    print("클리핑 데이터 분석 중...")
    analysis = windsurf.analyze_clipping_data(sample_clipping_data)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

    print("\n파일 생성 테스트 (시뮬레이션 모드)...")
    generated_file = windsurf.generate_file_from_clipping(sample_clipping_data, simulate=True)

    if generated_file:
        print(f"파일 타입: {generated_file['file_type']}")
        print(f"파일 확장자: {generated_file['file_extension']}")
        print("-" * 20 + " 생성된 파일 내용 " + "-" * 20)
        print(generated_file['file_content'])
        print("-" * 58)
    else:
        print("파일 생성 실패")

if __name__ == "__main__":
    main()
