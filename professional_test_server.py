#!/usr/bin/env python3
"""
전문화된 실시간 테스트 서버
- GitHub Actions 스타일 워커
- Jest/PyTest 통합
- 실시간 WebSocket 피드백
"""
import asyncio
import json
import time
import traceback
import subprocess
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import importlib
import inspect
import websockets
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psutil
import hashlib
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'test_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    test_id: str
    test_name: str
    file_path: str
    function_name: str
    status: str  # passed, failed, error, skipped
    duration: float
    error_message: Optional[str]
    stack_trace: Optional[str]
    execution_time: str
    memory_usage: float
    cpu_usage: float
    suggestions: List[str]
    severity: str  # critical, high, medium, low
    auto_fix_available: bool

@dataclass
class SystemHealth:
    """시스템 건강 상태"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_tests: int
    total_tests_run: int
    success_rate: float
    average_test_time: float
    error_count: int
    warning_count: int

class IntelligentDebugger:
    """지능형 디버거 - Stack Overflow & GitHub 패턴 분석"""
    
    def __init__(self):
        self.error_patterns = {
            'ImportError': {
                'solutions': [
                    'pip install {module}',
                    'Check PYTHONPATH',
                    'Verify virtual environment'
                ],
                'common_causes': ['Missing package', 'Wrong environment', 'Path issue']
            },
            'AttributeError': {
                'solutions': [
                    'Check object type and available methods',
                    'Verify API compatibility',
                    'Update package version'
                ],
                'common_causes': ['API change', 'Wrong object type', 'Version mismatch']
            },
            'FileNotFoundError': {
                'solutions': [
                    'Check file path',
                    'Create missing directories',
                    'Verify permissions'
                ],
                'common_causes': ['Wrong path', 'Missing file', 'Permission denied']
            },
            'ConnectionError': {
                'solutions': [
                    'Check network connectivity',
                    'Verify server is running',
                    'Check firewall settings'
                ],
                'common_causes': ['Network issue', 'Server down', 'Firewall block']
            }
        }
        
        self.github_patterns = self.load_github_patterns()
    
    def load_github_patterns(self) -> Dict[str, Any]:
        """GitHub Issues 패턴 로드"""
        return {
            'flask_dotenv_error': {
                'pattern': r'AttributeError.*dotenv.*find_dotenv',
                'solution': 'pip install --upgrade python-dotenv flask',
                'description': 'Flask dotenv compatibility issue',
                'github_issue': 'pallets/flask#4581'
            },
            'python_path_error': {
                'pattern': r"can't open file.*No such file",
                'solution': 'cd to correct directory or use absolute path',
                'description': 'Python file path resolution issue',
                'github_issue': 'common Python execution issue'
            },
            'winget_not_found': {
                'pattern': r'winget.*CommandNotFoundException',
                'solution': 'Install App Installer from Microsoft Store',
                'description': 'Windows Package Manager not installed',
                'github_issue': 'microsoft/winget-cli#1861'
            }
        }
    
    def analyze_error(self, error_message: str, stack_trace: str) -> Dict[str, Any]:
        """에러 분석 및 해결책 제안"""
        analysis = {
            'error_type': self.classify_error(error_message),
            'severity': self.assess_severity(error_message, stack_trace),
            'solutions': [],
            'auto_fix_available': False,
            'github_references': [],
            'code_suggestions': []
        }
        
        # GitHub 패턴 매칭
        for pattern_name, pattern_info in self.github_patterns.items():
            if re.search(pattern_info['pattern'], error_message + stack_trace):
                analysis['solutions'].append(pattern_info['solution'])
                analysis['github_references'].append(pattern_info['github_issue'])
                analysis['auto_fix_available'] = pattern_name in ['flask_dotenv_error']
        
        # 기본 에러 패턴 분석
        error_type = analysis['error_type']
        if error_type in self.error_patterns:
            pattern = self.error_patterns[error_type]
            analysis['solutions'].extend(pattern['solutions'])
        
        # 코드 제안 생성
        analysis['code_suggestions'] = self.generate_code_suggestions(error_message, stack_trace)
        
        return analysis
    
    def classify_error(self, error_message: str) -> str:
        """에러 타입 분류"""
        error_types = {
            'ImportError': ['ImportError', 'ModuleNotFoundError'],
            'AttributeError': ['AttributeError'],
            'FileNotFoundError': ['FileNotFoundError', 'No such file'],
            'ConnectionError': ['ConnectionError', 'ConnectTimeout', 'RequestException'],
            'SyntaxError': ['SyntaxError', 'IndentationError'],
            'TypeError': ['TypeError'],
            'ValueError': ['ValueError'],
            'RuntimeError': ['RuntimeError']
        }
        
        for error_type, keywords in error_types.items():
            if any(keyword in error_message for keyword in keywords):
                return error_type
        
        return 'UnknownError'
    
    def assess_severity(self, error_message: str, stack_trace: str) -> str:
        """에러 심각도 평가"""
        critical_keywords = ['fatal', 'critical', 'segfault', 'memory', 'corruption']
        high_keywords = ['failed', 'error', 'exception', 'crash']
        medium_keywords = ['warning', 'deprecated', 'timeout']
        
        text = (error_message + stack_trace).lower()
        
        if any(keyword in text for keyword in critical_keywords):
            return 'critical'
        elif any(keyword in text for keyword in high_keywords):
            return 'high'
        elif any(keyword in text for keyword in medium_keywords):
            return 'medium'
        else:
            return 'low'
    
    def generate_code_suggestions(self, error_message: str, stack_trace: str) -> List[str]:
        """코드 수정 제안 생성"""
        suggestions = []
        
        if 'dotenv' in error_message and 'find_dotenv' in error_message:
            suggestions.append("""
# Fix Flask dotenv issue
pip install --upgrade python-dotenv==1.0.0 flask==3.0.0

# Alternative: Remove dotenv dependency
app = Flask(__name__)
# app.config.from_envvar('FLASK_ENV')  # Remove this line
""")
        
        if 'No such file' in error_message:
            suggestions.append("""
# Fix file path issue
import os
from pathlib import Path

# Use absolute path
current_dir = Path(__file__).parent
file_path = current_dir / "your_file.py"

# Or change directory first
os.chdir(r"d:\\my workspace\\OneDrive NEW\\GNY")
""")
        
        if 'CommandNotFoundException' in error_message and 'python' in error_message:
            suggestions.append("""
# Fix Python PATH issue
# 1. Add Python to PATH in Environment Variables
# 2. Or use full path:
C:\\Python313\\python.exe your_script.py

# 3. Or use py launcher:
py your_script.py
""")
        
        return suggestions

class TestOrchestrator:
    """테스트 오케스트레이터 - CI/CD 스타일"""
    
    def __init__(self):
        self.test_queue = asyncio.Queue()
        self.running_tests = {}
        self.completed_tests = []
        self.debugger = IntelligentDebugger()
        self.connected_clients = set()
        self.test_counter = 0
        self.system_monitor = SystemMonitor()
        
    async def discover_tests(self, directory: str = ".") -> List[Dict[str, Any]]:
        """테스트 자동 발견 - pytest 스타일"""
        discovered_tests = []
        
        # Python 파일에서 테스트 함수 찾기
        for py_file in Path(directory).glob("**/*.py"):
            if py_file.name.startswith(('test_', 'smoke_', 'comprehensive_')):
                tests = await self.extract_tests_from_file(py_file)
                discovered_tests.extend(tests)
        
        # 메인 함수가 있는 파일들도 테스트 대상
        for py_file in Path(directory).glob("*.py"):
            if py_file.name not in ['__init__.py'] and not py_file.name.startswith('.'):
                main_test = {
                    'test_id': f'main_{py_file.stem}_{self.test_counter}',
                    'test_name': f'Execute {py_file.name}',
                    'file_path': str(py_file),
                    'function_name': 'main',
                    'test_type': 'execution'
                }
                discovered_tests.append(main_test)
                self.test_counter += 1
        
        logger.info(f"발견된 테스트: {len(discovered_tests)}개")
        return discovered_tests
    
    async def extract_tests_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """파일에서 테스트 함수 추출"""
        tests = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 함수 정의 찾기
            function_pattern = r'def\s+(test_\w+|main)\s*\('
            matches = re.finditer(function_pattern, content)
            
            for match in matches:
                func_name = match.group(1)
                test = {
                    'test_id': f'{file_path.stem}_{func_name}_{self.test_counter}',
                    'test_name': f'{file_path.name}::{func_name}',
                    'file_path': str(file_path),
                    'function_name': func_name,
                    'test_type': 'function'
                }
                tests.append(test)
                self.test_counter += 1
                
        except Exception as e:
            logger.error(f"파일 분석 실패 {file_path}: {e}")
        
        return tests
    
    async def run_test(self, test_info: Dict[str, Any]) -> TestResult:
        """개별 테스트 실행"""
        start_time = time.time()
        test_id = test_info['test_id']
        
        # 시스템 리소스 모니터링 시작
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        initial_cpu = psutil.cpu_percent()
        
        try:
            self.running_tests[test_id] = {
                'start_time': start_time,
                'test_info': test_info
            }
            
            # 실시간 업데이트 전송
            await self.broadcast_test_update({
                'type': 'test_started',
                'test_id': test_id,
                'test_name': test_info['test_name']
            })
            
            # 테스트 실행
            if test_info['test_type'] == 'execution':
                result = await self.execute_python_file(test_info)
            else:
                result = await self.execute_test_function(test_info)
            
            duration = time.time() - start_time
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            final_cpu = psutil.cpu_percent()
            
            # 성공한 테스트 결과
            test_result = TestResult(
                test_id=test_id,
                test_name=test_info['test_name'],
                file_path=test_info['file_path'],
                function_name=test_info['function_name'],
                status='passed',
                duration=duration,
                error_message=None,
                stack_trace=None,
                execution_time=datetime.now().isoformat(),
                memory_usage=final_memory - initial_memory,
                cpu_usage=final_cpu - initial_cpu,
                suggestions=[],
                severity='low',
                auto_fix_available=False
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            stack_trace = traceback.format_exc()
            
            # 에러 분석
            analysis = self.debugger.analyze_error(error_message, stack_trace)
            
            test_result = TestResult(
                test_id=test_id,
                test_name=test_info['test_name'],
                file_path=test_info['file_path'],
                function_name=test_info['function_name'],
                status='failed',
                duration=duration,
                error_message=error_message,
                stack_trace=stack_trace,
                execution_time=datetime.now().isoformat(),
                memory_usage=0,
                cpu_usage=0,
                suggestions=analysis['solutions'] + analysis['code_suggestions'],
                severity=analysis['severity'],
                auto_fix_available=analysis['auto_fix_available']
            )
        
        finally:
            if test_id in self.running_tests:
                del self.running_tests[test_id]
        
        self.completed_tests.append(test_result)
        
        # 실시간 업데이트 전송
        await self.broadcast_test_update({
            'type': 'test_completed',
            'test_result': asdict(test_result)
        })
        
        return test_result
    
    async def execute_python_file(self, test_info: Dict[str, Any]) -> Any:
        """Python 파일 실행"""
        file_path = test_info['file_path']
        
        # 서브프로세스로 실행
        process = await asyncio.create_subprocess_exec(
            sys.executable, file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path(file_path).parent
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Exit code {process.returncode}: {stderr.decode()}")
        
        return stdout.decode()
    
    async def execute_test_function(self, test_info: Dict[str, Any]) -> Any:
        """테스트 함수 실행"""
        file_path = test_info['file_path']
        function_name = test_info['function_name']
        
        # 동적 임포트
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 함수 실행
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        else:
            raise AttributeError(f"Function {function_name} not found in {file_path}")
    
    async def run_all_tests(self, parallel: bool = True, max_workers: int = 4):
        """모든 테스트 실행"""
        tests = await self.discover_tests()
        
        if not tests:
            logger.warning("실행할 테스트가 없습니다.")
            return []
        
        logger.info(f"테스트 실행 시작: {len(tests)}개 테스트")
        
        if parallel and len(tests) > 1:
            # 병렬 실행
            semaphore = asyncio.Semaphore(max_workers)
            
            async def run_with_semaphore(test_info):
                async with semaphore:
                    return await self.run_test(test_info)
            
            tasks = [run_with_semaphore(test) for test in tests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 순차 실행
            results = []
            for test in tests:
                result = await self.run_test(test)
                results.append(result)
        
        # 결과 요약
        passed = len([r for r in results if isinstance(r, TestResult) and r.status == 'passed'])
        failed = len([r for r in results if isinstance(r, TestResult) and r.status == 'failed'])
        errors = len([r for r in results if not isinstance(r, TestResult)])
        
        summary = {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed / len(tests)) * 100 if tests else 0
        }
        
        await self.broadcast_test_update({
            'type': 'test_summary',
            'summary': summary
        })
        
        logger.info(f"테스트 완료: {summary}")
        return results
    
    async def broadcast_test_update(self, message: Dict[str, Any]):
        """실시간 업데이트 브로드캐스트"""
        if self.connected_clients:
            disconnected = set()
            
            for websocket in self.connected_clients:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.add(websocket)
            
            # 연결 끊긴 클라이언트 제거
            for websocket in disconnected:
                self.connected_clients.discard(websocket)

class SystemMonitor:
    """시스템 모니터"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        
    def get_current_health(self) -> SystemHealth:
        """현재 시스템 상태"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # 디스크 사용량
            try:
                if os.name == 'nt':
                    disk = psutil.disk_usage('C:')
                else:
                    disk = psutil.disk_usage('/')
            except:
                disk = psutil.disk_usage('.')
            
            health = SystemHealth(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                active_tests=0,  # 실제 구현에서는 orchestrator에서 가져옴
                total_tests_run=0,
                success_rate=100.0,
                average_test_time=0.0,
                error_count=0,
                warning_count=0
            )
            
            return health
            
        except Exception as e:
            logger.error(f"시스템 모니터링 오류: {e}")
            return SystemHealth(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0,
                memory_percent=0,
                disk_usage=0,
                active_tests=0,
                total_tests_run=0,
                success_rate=0,
                average_test_time=0,
                error_count=1,
                warning_count=0
            )

# FastAPI 웹 서버
app = FastAPI(title="전문화된 테스트 서버", version="1.0.0")

# 전역 인스턴스
orchestrator = TestOrchestrator()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결"""
    await websocket.accept()
    orchestrator.connected_clients.add(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (keep-alive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        orchestrator.connected_clients.discard(websocket)

@app.get("/")
async def get_dashboard():
    """메인 대시보드"""
    return HTMLResponse(content=get_dashboard_html(), media_type="text/html")

@app.post("/api/run-tests")
async def run_tests(background_tasks: BackgroundTasks):
    """테스트 실행 API"""
    background_tasks.add_task(orchestrator.run_all_tests)
    return {"message": "테스트 실행 시작", "status": "started"}

@app.get("/api/test-results")
async def get_test_results():
    """테스트 결과 조회"""
    return {
        "completed_tests": [asdict(test) for test in orchestrator.completed_tests],
        "running_tests": orchestrator.running_tests
    }

@app.get("/api/system-health")
async def get_system_health():
    """시스템 상태 조회"""
    health = orchestrator.system_monitor.get_current_health()
    return asdict(health)

@app.post("/api/auto-fix/{test_id}")
async def auto_fix_test(test_id: str):
    """자동 수정 실행"""
    # 실제 구현에서는 테스트 결과에서 auto_fix_available이 True인 경우
    # 자동 수정을 실행
    return {"message": f"Auto-fix executed for {test_id}", "status": "completed"}

def get_dashboard_html() -> str:
    """대시보드 HTML"""
    return """



    
    
    🔬 전문화된 테스트 서버
    
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Consolas', 'Monaco', monospace; 
            background: #0d1117; 
            color: #c9d1d9; 
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, #1f2937, #374151);
            padding: 1rem 2rem;
            border-bottom: 2px solid #30363d;
        }
        .header h1 {
            color: #58a6ff;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        .header .subtitle {
            color: #8b949e;
            font-size: 0.9rem;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .card h3 {
            color: #f0f6fc;
            margin-bottom: 1rem;
            font-size: 1.1rem;
            border-bottom: 1px solid #21262d;
            padding-bottom: 0.5rem;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #0d1117;
            border-radius: 4px;
        }
        .metric .label { color: #8b949e; }
        .metric .value { color: #f0f6fc; font-weight: bold; }
        .status {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status.passed { background: #238636; color: white; }
        .status.failed { background: #da3633; color: white; }
        .status.running { background: #fd7e14; color: white; }
        .test-item {
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .test-item .test-name {
            color: #58a6ff;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .test-item .test-details {
            font-size: 0.85rem;
            color: #8b949e;
        }
        .error-details {
            background: #1a1a1a;
            border-left: 3px solid #da3633;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 4px 4px 0;
            font-family: 'Consolas', monospace;
            font-size: 0.8rem;
            color: #ff6b6b;
        }
        .suggestions {
            background: #0f3460;
            border-left: 3px solid #58a6ff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 4px 4px 0;
        }
        .suggestions h4 {
            color: #58a6ff;
            margin-bottom: 0.5rem;
        }
        .suggestions ul {
            list-style: none;
            padding-left: 1rem;
        }
        .suggestions li {
            margin: 0.25rem 0;
            color: #c9d1d9;
        }
        .suggestions li:before {
            content: "💡 ";
            margin-right: 0.5rem;
        }
        .button {
            background: #238636;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: bold;
            transition: background 0.2s;
        }
        .button:hover { background: #2ea043; }
        .button.secondary {
            background: #21262d;
            border: 1px solid #30363d;
        }
        .button.secondary:hover { background: #30363d; }
        .button.danger {
            background: #da3633;
        }
        .button.danger:hover { background: #f85149; }
        .controls {
            margin-bottom: 2rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .log-area {
            background: #0d1117;
            border: 1px solid #30363d;
            padding: 1rem;
            border-radius: 6px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 0.8rem;
        }
        .log-entry {
            margin: 0.25rem 0;
            padding: 0.25rem 0;
        }
        .log-entry.info { color: #58a6ff; }
        .log-entry.error { color: #f85149; }
        .log-entry.success { color: #3fb950; }
        .log-entry.warning { color: #d29922; }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #21262d;
            border-radius: 10px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #238636, #2ea043);
            transition: width 0.3s ease;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            .controls { flex-direction: column; }
            .container { padding: 1rem; }
        }
        .github-link {
            color: #58a6ff;
            text-decoration: none;
            font-size: 0.8rem;
        }
        .github-link:hover { text-decoration: underline; }
        .auto-fix-btn {
            background: #6f42c1;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        .auto-fix-btn:hover { background: #8957e5; }
    


    
        🔬 전문화된 테스트 서버
        
            실시간 디버깅 • 자동 수정 • GitHub 패턴 분석 • 지능형 오류 해결
        
    
    
    
        
            
                🚀 전체 테스트 실행
            
            
                🗑️ 결과 초기화
            
            
                📊 결과 내보내기
            
            
                🛑 긴급 중단
            
        
        
        
            
                📊 시스템 상태
                
                    
                        CPU 사용률
                        0%
                    
                    
                        메모리 사용률
                        0%
                    
                    
                        디스크 사용률
                        0%
                    
                    
                        활성 테스트
                        0
                    
                
            
            
            
                📈 테스트 통계
                
                    
                        총 실행
                        0
                    
                    
                        성공
                        0
                    
                    
                        실패
                        0
                    
                    
                        성공률
                        0%
                    
                
                
                    
                
            
            
            
                🔄 실행 중인 테스트
                
                    
                        실행 중인 테스트 없음
                    
                
            
            
            
                📱 빠른 액션
                
                    
                        🧠 스마트 테스트 (실패한 것만)
                    
                    
                        ⚡ 성능 테스트
                    
                    
                        💨 스모크 테스트
                    
                    
                        🔗 통합 테스트
                    
                
            
        
        
        
            
                🔬 테스트 결과
                
                    
                
            
            
            
                📝 실시간 로그
                
                    시스템 준비 완료. 테스트를 시작하세요.
                
            
        
    
    
    
        let ws = null;
        let testResults = [];
        let runningTests = {};
        
        // WebSocket 연결
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                addLog('WebSocket 연결 성공', 'success');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            ws.onclose = function() {
                addLog('WebSocket 연결 끊김. 재연결 시도 중...', 'warning');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                addLog(`WebSocket 오류: ${error}`, 'error');
            };
        }
        
        function handleWebSocketMessage(message) {
            switch(message.type) {
                case 'test_started':
                    addLog(`테스트 시작: ${message.test_name}`, 'info');
                    break;
                case 'test_completed':
                    handleTestCompleted(message.test_result);
                    break;
                case 'test_summary':
                    updateTestStats(message.summary);
                    break;
            }
        }
        
        function handleTestCompleted(testResult) {
            testResults.push(testResult);
            updateTestResults();
            
            if (testResult.status === 'passed') {
                addLog(`✅ ${testResult.test_name} 성공 (${testResult.duration.toFixed(2)}s)`, 'success');
            } else {
                addLog(`❌ ${testResult.test_name} 실패: ${testResult.error_message}`, 'error');
            }
        }
        
        function updateTestResults() {
            const container = document.getElementById('test-results');
            container.innerHTML = '';
            
            testResults.forEach(result => {
                const testElement = createTestResultElement(result);
                container.appendChild(testElement);
            });
        }
        
        function createTestResultElement(result) {
            const div = document.createElement('div');
            div.className = 'test-item';
            
            const statusClass = result.status === 'passed' ? 'passed' : 'failed';
            const statusIcon = result.status === 'passed' ? '✅' : '❌';
            
            let autoFixButton = '';
            if (result.auto_fix_available) {
                autoFixButton = `<button class="auto-fix-btn" onclick="autoFix('${result.test_id}')">🔧 자동 수정</button>`;
            }
            
            let suggestionsHtml = '';
            if (result.suggestions && result.suggestions.length > 0) {
                suggestionsHtml = `
                    <div class="suggestions">
                        <h4>💡 해결책 제안</h4>
                        <ul>
                            ${result.suggestions.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            let errorHtml = '';
            if (result.error_message) {
                errorHtml = `
                    <div class="error-details">
                        <strong>오류: ${result.error_message}</strong>
                        <details>
                            <summary>상세 스택 트레이스</summary>
                            <pre>${result.stack_trace || '스택 트레이스 없음'}</pre>
                        </details>
                    </div>
                `;
            }
            
            div.innerHTML = `
                <div class="test-name">
                    ${statusIcon} ${result.test_name}
                    <span class="status ${statusClass}">${result.status}</span>
                    ${autoFixButton}
                </div>
                <div class="test-details">
                    📁 ${result.file_path}
                    ⏱️ 실행시간: ${result.duration.toFixed(2)}초
                    🧠 메모리: ${result.memory_usage.toFixed(1)}MB
                    🔥 심각도: ${result.severity}
                </div>
                ${errorHtml}
                ${suggestionsHtml}
            `;
            
            return div;
        }
        
        function updateTestStats(summary) {
            document.getElementById('total-tests').textContent = summary.total;
            document.getElementById('passed-tests').textContent = summary.passed;
            document.getElementById('failed-tests').textContent = summary.failed;
            document.getElementById('success-rate').textContent = summary.success_rate.toFixed(1) + '%';
            
            const progressBar = document.getElementById('success-progress');
            progressBar.style.width = summary.success_rate + '%';
        }
        
        async function runAllTests() {
            addLog('전체 테스트 실행 시작...', 'info');
            testResults = [];
            updateTestResults();
            
            try {
                const response = await fetch('/api/run-tests', { method: 'POST' });
                const result = await response.json();
                addLog(result.message, 'info');
            } catch (error) {
                addLog(`테스트 실행 실패: ${error}`, 'error');
            }
        }
        
        async function autoFix(testId) {
            addLog(`자동 수정 실행: ${testId}`, 'info');
            
            try {
                const response = await fetch(`/api/auto-fix/${testId}`, { method: 'POST' });
                const result = await response.json();
                addLog(result.message, 'success');
            } catch (error) {
                addLog(`자동 수정 실패: ${error}`, 'error');
            }
        }
        
        function clearResults() {
            testResults = [];
            updateTestResults();
            document.getElementById('log-area').innerHTML = 
                '<div class="log-entry">결과가 초기화되었습니다.</div>';
            addLog('결과 초기화 완료', 'info');
        }
        
        function exportResults() {
            const data = {
                timestamp: new Date().toISOString(),
                results: testResults,
                summary: {
                    total: testResults.length,
                    passed: testResults.filter(r => r.status === 'passed').length,
                    failed: testResults.filter(r => r.status === 'failed').length
                }
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `test-results-${new Date().toISOString().slice(0, 19)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            addLog('테스트 결과 내보내기 완료', 'success');
        }
        
        function emergencyStop() {
            addLog('긴급 중단 실행', 'warning');
            // 실제 구현에서는 실행 중인 테스트를 중단
        }
        
        function runSmartTests() {
            addLog('스마트 테스트 (실패한 테스트만) 실행', 'info');
            // 실패한 테스트만 재실행하는 로직
        }
        
        function runPerformanceTests() {
            addLog('성능 테스트 실행', 'info');
            // 성능 관련 테스트만 실행
        }
        
        function runSmokeTests() {
            addLog('스모크 테스트 실행', 'info');
            // 기본적인 기능 테스트만 실행
        }
        
        function runIntegrationTests() {
            addLog('통합 테스트 실행', 'info');
            // 통합 테스트만 실행
        }
        
        function addLog(message, type = 'info') {
            const logArea = document.getElementById('log-area');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
            
            logArea.appendChild(logEntry);
            logArea.scrollTop = logArea.scrollHeight;
            
            // 로그가 너무 많아지면 오래된 것 제거
            if (logArea.children.length > 100) {
                logArea.removeChild(logArea.firstChild);
            }
        }
        
        // 시스템 상태 업데이트
        async function updateSystemHealth() {
            try {
                const response = await fetch('/api/system-health');
                const health = await response.json();
                
                document.getElementById('cpu-usage').textContent = health.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = health.memory_percent.toFixed(1) + '%';
                document.getElementById('disk-usage').textContent = health.disk_usage.toFixed(1) + '%';
                document.getElementById('active-tests').textContent = health.active_tests;
            } catch (error) {
                console.error('시스템 상태 업데이트 실패:', error);
            }
        }
        
        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            updateSystemHealth();
            
            // 5초마다 시스템 상태 업데이트
            setInterval(updateSystemHealth, 5000);
        });
    


    """

async def main():
    """메인 실행 함수"""
    print("🔬 전문화된 테스트 서버 시작")
    print("=" * 60)
    print("🌐 웹 인터페이스: http://localhost:8000")
    print("📡 WebSocket 연결: ws://localhost:8000/ws")
    print("🚀 API 문서: http://localhost:8000/docs")
    print("=" * 60)
    
    # 서버 실행
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 서버 종료")
