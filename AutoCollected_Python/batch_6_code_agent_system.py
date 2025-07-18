#!/usr/bin/env python3
"""
Advanced Code Agent System
채팅창 명령으로 코드 생성, 실행, 적용을 자동화하는 시스템
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from pathlib import Path
import re
import ast

class CodeExecutionEnvironment:
    """안전한 코드 실행 환경"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ai_code_")
        self.allowed_imports = {
            'os', 'sys', 'json', 'datetime', 'time', 'math', 'random',
            'requests', 'numpy', 'pandas', 'matplotlib', 'sqlite3',
            'asyncio', 'pathlib', 'typing', 're', 'collections'
        }
        self.logger = logging.getLogger(__name__)
    
    def is_safe_code(self, code: str) -> tuple[bool, str]:
        """코드 안전성 검사"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"문법 오류: {e}"
        
        dangerous_patterns = [
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\([^)]*["\']w["\']',  # 쓰기 모드 파일 열기
            r'subprocess\.',
            r'os\.system',
            r'os\.popen',
            r'shutil\.rmtree',
            r'rm\s+-rf',
            r'format\s*\(',  # 포맷 스트링 공격 방지
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"위험한 패턴 감지: {pattern}"
        
        return True, "안전함"
    
    async def execute_python_code(self, code: str) -> Dict:
        """Python 코드 실행"""
        is_safe, safety_msg = self.is_safe_code(code)
        if not is_safe:
            return {
                "success": False,
                "error": f"보안 검사 실패: {safety_msg}",
                "output": ""
            }
        
        # 임시 파일에 코드 저장
        code_file = os.path.join(self.temp_dir, f"ai_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        
        try:
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 코드 실행
            process = await asyncio.create_subprocess_exec(
                'python', code_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=30  # 30초 타임아웃
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8') if stdout else "",
                "error": stderr.decode('utf-8') if stderr else "",
                "return_code": process.returncode,
                "file_path": code_file
            }
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "코드 실행 시간 초과 (30초)",
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"코드 실행 오류: {str(e)}",
                "output": ""
            }
    
    def cleanup(self):
        """임시 파일 정리"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

class CodeAgent:
    """코드 생성, 실행, 적용을 담당하는 AI 에이전트"""
    
    def __init__(self, gemini_model):
        self.gemini_model = gemini_model
        self.execution_env = CodeExecutionEnvironment()
        self.logger = logging.getLogger(__name__)
        self.project_files = {}  # 프로젝트 파일 추적
    
    async def process_code_request(self, user_request: str, context: Dict = None) -> Dict:
        """사용자 코드 요청 처리"""
        try:
            # 1. 요청 분석 및 코드 생성
            code_analysis = await self._analyze_code_request(user_request, context)
            
            if not code_analysis["success"]:
                return code_analysis
            
            # 2. 코드 실행 (필요한 경우)
            execution_result = None
            if code_analysis.get("should_execute", False):
                execution_result = await self._execute_generated_code(code_analysis["code"])
            
            # 3. 파일 적용 (필요한 경우)
            application_result = None
            if code_analysis.get("should_apply", False):
                application_result = await self._apply_code_to_files(code_analysis)
            
            return {
                "success": True,
                "request": user_request,
                "analysis": code_analysis,
                "execution": execution_result,
                "application": application_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"코드 요청 처리 오류: {e}")
            return {
                "success": False,
                "error": f"처리 중 오류 발생: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    async def _analyze_code_request(self, request: str, context: Dict = None) -> Dict:
        """요청 분석 및 코드 생성"""
        analysis_prompt = f"""
다음 사용자 요청을 분석하고 적절한 코드를 생성해주세요:

사용자 요청: {request}

다음 형식으로 응답해주세요:
1. 요청 분석
2. 생성할 코드 (Python)
3. 실행 필요 여부
4. 파일 적용 필요 여부
5. 예상 결과

코드는 다음 가이드라인을 따라주세요:
- 안전하고 실행 가능한 Python 코드만 생성
- 필요한 import 문 포함
- 주석으로 코드 설명 추가
- 에러 처리 포함

응답 형식:
```json
{{
    "analysis": "요청 분석 내용",
    "code": "생성된 Python 코드",
    "should_execute": true/false,
    "should_apply": true/false,
    "file_path": "적용할 파일 경로 (적용이 필요한 경우)",
    "expected_result": "예상 결과 설명"
}}
```
"""

        try:
            response = await self.gemini_model.generate_content_async(analysis_prompt)
            response_text = response.text
            
            # JSON 응답 추출 (여러 형태 지원)
            json_data = None
            
            # 1. ```json 블록에서 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 오류: {e}")
            
            # 2. { } 블록에서 추출
            if not json_data:
                brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                if brace_match:
                    try:
                        json_data = json.loads(brace_match.group(0))
                    except json.JSONDecodeError:
                        pass
            
            # 3. 성공한 경우
            if json_data:
                json_data["success"] = True
                json_data["raw_response"] = response_text
                return json_data
            
            # 4. JSON 파싱 실패시 텍스트 기반 처리
            return self._fallback_text_analysis(response_text, request)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"코드 분석 실패: {str(e)}"
            }
    
    async def _execute_generated_code(self, code: str) -> Dict:
        """생성된 코드 실행"""
        return await self.execution_env.execute_python_code(code)
    
    async def _apply_code_to_files(self, code_analysis: Dict) -> Dict:
        """코드를 파일에 적용"""
        try:
            file_path = code_analysis.get("file_path")
            code = code_analysis.get("code")
            
            if not file_path or not code:
                return {
                    "success": False,
                    "error": "파일 경로 또는 코드가 없습니다"
                }
            
            # 절대 경로로 변환
            abs_path = os.path.abspath(file_path)
            
            # 디렉토리 생성 (필요한 경우)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # 파일에 코드 작성
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 프로젝트 파일 추적에 추가
            self.project_files[file_path] = {
                "path": abs_path,
                "created_at": datetime.now().isoformat(),
                "size": len(code)
            }
            
            return {
                "success": True,
                "file_path": abs_path,
                "message": f"코드가 {abs_path}에 성공적으로 적용되었습니다",
                "file_size": len(code)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"파일 적용 실패: {str(e)}"
            }
    
    def get_project_status(self) -> Dict:
        """프로젝트 상태 조회"""
        return {
            "created_files": self.project_files,
            "temp_directory": self.execution_env.temp_dir,
            "total_files": len(self.project_files)
        }
    
    def cleanup(self):
        """리소스 정리"""
        self.execution_env.cleanup()

class CodeAgentManager:
    """코드 에이전트 관리자"""
    
    def __init__(self, gemini_model):
        self.gemini_model = gemini_model
        self.code_agent = CodeAgent(gemini_model)
        self.logger = logging.getLogger(__name__)
        self.command_history = []
    
    async def execute_command(self, command: str, context: Dict = None) -> Dict:
        """채팅 명령 실행"""
        try:
            # 명령어 패턴 분석
            command_type = self._analyze_command_type(command)
            
            result = {
                "command": command,
                "command_type": command_type,
                "timestamp": datetime.now().isoformat()
            }
            
            if command_type == "code_request":
                # 코드 생성/실행/적용 요청
                code_result = await self.code_agent.process_code_request(command, context)
                result.update(code_result)
                
            elif command_type == "project_status":
                # 프로젝트 상태 조회
                result["project_status"] = self.code_agent.get_project_status()
                result["success"] = True
                
            elif command_type == "help":
                # 도움말
                result["help"] = self._get_help_text()
                result["success"] = True
                
            else:
                # 일반 대화
                result["success"] = False
                result["message"] = "코드 관련 명령이 아닙니다. 'help'를 입력하면 사용 가능한 명령을 확인할 수 있습니다."
            
            # 명령 히스토리에 추가
            self.command_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"명령 실행 오류: {e}")
            return {
                "success": False,
                "error": f"명령 실행 중 오류 발생: {str(e)}",
                "command": command
            }
    
    def _analyze_command_type(self, command: str) -> str:
        """명령어 타입 분석"""
        command_lower = command.lower()
        
        if any(keyword in command_lower for keyword in ['코드', 'code', '프로그램', 'program', '스크립트', 'script', '만들어', 'create', '생성']):
            return "code_request"
        elif any(keyword in command_lower for keyword in ['상태', 'status', '프로젝트', 'project']):
            return "project_status"
        elif any(keyword in command_lower for keyword in ['도움', 'help', '명령어', 'command']):
            return "help"
        else:
            return "general"
    
    def _get_help_text(self) -> str:
        """도움말 텍스트"""
        return """
🤖 코드 에이전트 사용법:

📝 코드 생성 및 실행:
- "간단한 계산기 프로그램 만들어줘"
- "JSON 파일을 읽는 코드 작성해줘"
- "API 요청하는 스크립트 생성해줘"

🔧 파일 적용:
- "calculator.py 파일로 저장해줘"
- "utils.py에 유틸리티 함수 추가해줘"

📊 프로젝트 관리:
- "프로젝트 상태" - 생성된 파일들 확인
- "상태" - 현재 작업 상황 보기

💡 팁:
- 구체적으로 요청할수록 더 정확한 코드를 생성합니다
- 파일명을 지정하면 자동으로 해당 파일에 저장됩니다
- 생성된 코드는 안전성 검사를 거쳐 실행됩니다
"""
    
    def get_command_history(self) -> List[Dict]:
        """명령 히스토리 조회"""
        return self.command_history[-10:]  # 최근 10개 명령만 반환

    def _fallback_text_analysis(self, response_text: str, request: str) -> Dict:
        """JSON 파싱 실패시 텍스트 기반 분석"""
        try:
            # 코드 블록 추출
            code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', response_text, re.DOTALL)
            code = code_match.group(1).strip() if code_match else None
            
            # 파일 경로 추출
            file_path_match = re.search(r'파일[:\s]*([^\s\n]+\.py)', response_text)
            file_path = file_path_match.group(1) if file_path_match else None
            
            # 실행 여부 판단
            should_execute = any(keyword in request.lower() for keyword in ['실행', 'run', '테스트', 'test'])
            should_apply = any(keyword in request.lower() for keyword in ['저장', 'save', '적용', 'apply', '파일'])
            
            return {
                "success": True,
                "analysis": f"요청 분석: {request[:100]}...",
                "code": code or "# 코드 추출 실패",
                "should_execute": should_execute,
                "should_apply": should_apply,
                "file_path": file_path or "generated_code.py",
                "expected_result": "코드 생성 및 처리 완료",
                "raw_response": response_text
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback 분석 실패: {str(e)}",
                "raw_response": response_text
            }

# 전역 인스턴스
code_agent_manager = None

def get_code_agent_manager(gemini_model):
    """코드 에이전트 매니저 인스턴스 가져오기"""
    global code_agent_manager
    if code_agent_manager is None:
        code_agent_manager = CodeAgentManager(gemini_model)
    return code_agent_manager
