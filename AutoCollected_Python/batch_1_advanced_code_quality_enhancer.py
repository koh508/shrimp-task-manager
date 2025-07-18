#!/usr/bin/env python3
"""
🎯 고급 코드 품질 향상 시스템
자동화된 코드 리팩토링, 최적화, 품질 검증 도구
"""

import ast
import os
import re
import sys
import json
import time
import sqlite3
import logging
import hashlib
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import shutil
from collections import defaultdict

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """코드 품질 메트릭"""
    complexity_score: float
    maintainability_score: float
    readability_score: float
    performance_score: float
    security_score: float
    documentation_score: float
    test_coverage_score: float
    overall_score: float

@dataclass
class OptimizationSuggestion:
    """최적화 제안"""
    type: str
    description: str
    priority: str
    code_snippet: str
    expected_improvement: float

class AdvancedCodeQualityEnhancer:
    """🎯 고급 코드 품질 향상 시스템"""
    
    def __init__(self):
        self.quality_metrics_history = []
        self.optimization_suggestions = []
        self.refactoring_history = []
        self.performance_improvements = {}
        
        # 데이터베이스 초기화
        self.init_quality_db()
        
        # 비동기 작업을 위한 스레드 풀
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        logger.info("🎯 고급 코드 품질 향상 시스템 초기화 완료")
    
    def init_quality_db(self):
        """품질 관리 데이터베이스 초기화"""
        try:
            self.db_connection = sqlite3.connect('code_quality_enhancement.db', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    file_path TEXT,
                    complexity_score REAL,
                    maintainability_score REAL,
                    readability_score REAL,
                    performance_score REAL,
                    security_score REAL,
                    documentation_score REAL,
                    test_coverage_score REAL,
                    overall_score REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    file_path TEXT,
                    optimization_type TEXT,
                    description TEXT,
                    before_score REAL,
                    after_score REAL,
                    improvement_percentage REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS refactoring_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    file_path TEXT,
                    refactor_type TEXT,
                    changes_made TEXT,
                    quality_improvement REAL
                )
            ''')
            
            self.db_connection.commit()
            logger.info("✅ 품질 관리 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"DB 초기화 오류: {e}")
    
    async def analyze_code_quality(self, file_path: str) -> QualityMetrics:
        """코드 품질 종합 분석"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 병렬로 다양한 메트릭 계산
            tasks = [
                asyncio.create_task(self._calculate_complexity_async(code)),
                asyncio.create_task(self._calculate_maintainability_async(code)),
                asyncio.create_task(self._calculate_readability_async(code)),
                asyncio.create_task(self._calculate_performance_async(code)),
                asyncio.create_task(self._calculate_security_async(code)),
                asyncio.create_task(self._calculate_documentation_async(code)),
                asyncio.create_task(self._calculate_test_coverage_async(file_path))
            ]
            
            results = await asyncio.gather(*tasks)
            
            metrics = QualityMetrics(
                complexity_score=results[0],
                maintainability_score=results[1],
                readability_score=results[2],
                performance_score=results[3],
                security_score=results[4],
                documentation_score=results[5],
                test_coverage_score=results[6],
                overall_score=sum(results) / len(results)
            )
            
            # 결과를 데이터베이스에 저장
            self.save_quality_metrics(file_path, metrics)
            
            logger.info(f"📊 품질 분석 완료: {file_path} - 종합점수: {metrics.overall_score:.1f}")
            return metrics
            
        except Exception as e:
            logger.error(f"품질 분석 오류: {e}")
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    async def _calculate_complexity_async(self, code: str) -> float:
        """복잡도 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_complexity, code)
    
    def _calculate_complexity(self, code: str) -> float:
        """순환 복잡도 및 인지적 복잡도 계산"""
        try:
            tree = ast.parse(code)
            complexity_score = 100.0
            
            class ComplexityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.complexity = 0
                    self.nesting_level = 0
                    self.function_count = 0
                    self.class_count = 0
                
                def visit_FunctionDef(self, node):
                    self.function_count += 1
                    old_nesting = self.nesting_level
                    self.nesting_level += 1
                    
                    # 함수 내 복잡도 계산
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                            self.complexity += self.nesting_level
                        elif isinstance(child, ast.Try):
                            self.complexity += 2
                        elif isinstance(child, ast.comprehension):
                            self.complexity += 1
                    
                    self.generic_visit(node)
                    self.nesting_level = old_nesting
                
                def visit_ClassDef(self, node):
                    self.class_count += 1
                    self.generic_visit(node)
            
            visitor = ComplexityVisitor()
            visitor.visit(tree)
            
            # 복잡도 점수 계산 (낮을수록 좋음)
            total_complexity = visitor.complexity + (visitor.function_count * 2) + (visitor.class_count * 1)
            
            if total_complexity > 50:
                complexity_score = max(20, 100 - (total_complexity - 50) * 2)
            elif total_complexity > 100:
                complexity_score = max(10, 100 - (total_complexity - 100) * 3)
            
            return complexity_score
            
        except Exception as e:
            logger.warning(f"복잡도 계산 오류: {e}")
            return 50.0
    
    async def _calculate_maintainability_async(self, code: str) -> float:
        """유지보수성 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_maintainability, code)
    
    def _calculate_maintainability(self, code: str) -> float:
        """코드 유지보수성 평가"""
        try:
            lines = code.splitlines()
            score = 100.0
            
            # 함수 길이 체크
            current_function_lines = 0
            in_function = False
            long_functions = 0
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('def '):
                    if in_function and current_function_lines > 20:
                        long_functions += 1
                    in_function = True
                    current_function_lines = 0
                elif in_function:
                    if stripped and not stripped.startswith('#'):
                        current_function_lines += 1
                    if stripped.startswith('def ') or stripped.startswith('class '):
                        if current_function_lines > 20:
                            long_functions += 1
                        current_function_lines = 0
            
            # 긴 함수 패널티
            if long_functions > 0:
                score -= long_functions * 15
            
            # 중복 코드 탐지
            line_hashes = defaultdict(int)
            for line in lines:
                if len(line.strip()) > 10:  # 의미있는 라인만
                    line_hash = hashlib.md5(line.strip().encode()).hexdigest()
                    line_hashes[line_hash] += 1
            
            duplicates = sum(1 for count in line_hashes.values() if count > 1)
            if duplicates > 5:
                score -= duplicates * 2
            
            # 매직 넘버 체크
            magic_numbers = len(re.findall(r'\b\d{2,}\b', code))
            if magic_numbers > 5:
                score -= magic_numbers * 3
            
            # 깊은 중첩 체크
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = (len(line) - len(line.lstrip())) // 4
                    max_indent = max(max_indent, indent)
            
            if max_indent > 4:
                score -= (max_indent - 4) * 10
            
            return max(0, score)
            
        except Exception as e:
            logger.warning(f"유지보수성 계산 오류: {e}")
            return 50.0
    
    async def _calculate_readability_async(self, code: str) -> float:
        """가독성 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_readability, code)
    
    def _calculate_readability(self, code: str) -> float:
        """코드 가독성 평가"""
        try:
            lines = code.splitlines()
            score = 100.0
            
            # 명명 규칙 체크
            good_names = 0
            bad_names = 0
            
            # 변수명, 함수명, 클래스명 추출
            names = re.findall(r'(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            names += re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', code)
            
            for name in names:
                if len(name) < 3 or name in ['i', 'j', 'k', 'x', 'y', 'z']:
                    bad_names += 1
                elif '_' in name or name.islower() or name[0].isupper():
                    good_names += 1
                else:
                    bad_names += 1
            
            if bad_names > 0:
                naming_ratio = good_names / (good_names + bad_names)
                score *= naming_ratio
            
            # 주석 밀도
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            if code_lines > 0:
                comment_ratio = comment_lines / code_lines
                if comment_ratio < 0.1:  # 주석이 10% 미만
                    score *= 0.8
                elif comment_ratio > 0.3:  # 주석이 30% 이상
                    score *= 1.1
            
            # 빈 줄 사용
            empty_lines = len([line for line in lines if not line.strip()])
            if code_lines > 0:
                empty_ratio = empty_lines / len(lines)
                if empty_ratio < 0.05:  # 빈 줄이 너무 적음
                    score *= 0.9
            
            # 라인 길이
            long_lines = len([line for line in lines if len(line) > 120])
            if long_lines > 0:
                score -= long_lines * 2
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"가독성 계산 오류: {e}")
            return 50.0
    
    async def _calculate_performance_async(self, code: str) -> float:
        """성능 점수 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_performance, code)
    
    def _calculate_performance(self, code: str) -> float:
        """성능 최적화 평가"""
        try:
            score = 100.0
            
            # 성능 향상 패턴 체크
            performance_patterns = {
                'list_comprehension': 10,
                'generator': 15,
                'async def': 20,
                'await': 15,
                'multiprocessing': 25,
                'threading': 15,
                'cache': 20,
                'lru_cache': 25,
                'set(': 10,
                'dict.get(': 5,
                'enumerate(': 5,
                'zip(': 5
            }
            
            for pattern, bonus in performance_patterns.items():
                if pattern in code:
                    score += bonus * min(5, code.count(pattern))
            
            # 성능 저하 패턴 체크
            anti_patterns = {
                'global ': -10,
                'import *': -15,
                'for.*for.*for': -20,  # 삼중 중첩 루프
                'while.*while': -15,
                '+ "': -5,  # 문자열 연결
                'append.*for': -10  # 리스트에 반복 추가
            }
            
            for pattern, penalty in anti_patterns.items():
                matches = len(re.findall(pattern, code))
                if matches > 0:
                    score += penalty * matches
            
            # 메모리 사용 패턴
            if 'del ' in code:
                score += 5
            if 'gc.collect()' in code:
                score += 10
            
            return max(0, min(150, score))  # 보너스로 150점까지 가능
            
        except Exception as e:
            logger.warning(f"성능 계산 오류: {e}")
            return 50.0
    
    async def _calculate_security_async(self, code: str) -> float:
        """보안 점수 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_security, code)
    
    def _calculate_security(self, code: str) -> float:
        """보안 취약점 평가"""
        try:
            score = 100.0
            
            # 보안 취약점 패턴
            security_issues = {
                'eval(': -30,
                'exec(': -30,
                'os.system(': -25,
                'subprocess.call(.*shell=True': -20,
                'pickle.loads(': -15,
                'input(': -10,
                'raw_input(': -10
            }
            
            for pattern, penalty in security_issues.items():
                if re.search(pattern, code):
                    score += penalty
            
            # 보안 좋은 패턴
            security_patterns = {
                'try:.*except': 10,
                'logging': 5,
                'hashlib': 10,
                'secrets': 15,
                'ssl': 15,
                'cryptography': 20
            }
            
            for pattern, bonus in security_patterns.items():
                if re.search(pattern, code):
                    score += bonus
            
            return max(0, score)
            
        except Exception as e:
            logger.warning(f"보안 계산 오류: {e}")
            return 50.0
    
    async def _calculate_documentation_async(self, code: str) -> float:
        """문서화 점수 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_documentation, code)
    
    def _calculate_documentation(self, code: str) -> float:
        """문서화 품질 평가"""
        try:
            lines = code.splitlines()
            score = 0.0
            
            # 독스트링 체크
            docstring_count = code.count('"""') + code.count("'''")
            score += min(30, docstring_count * 15)
            
            # 함수별 독스트링
            functions = re.findall(r'def\s+\w+\([^)]*\):', code)
            function_docs = len(re.findall(r'def\s+\w+\([^)]*\):\s*\n\s*"""', code, re.MULTILINE))
            
            if len(functions) > 0:
                doc_ratio = function_docs / len(functions)
                score += doc_ratio * 40
            
            # 주석 품질
            comments = [line for line in lines if line.strip().startswith('#')]
            meaningful_comments = [c for c in comments if len(c.strip()) > 10]
            
            if len(comments) > 0:
                comment_quality = len(meaningful_comments) / len(comments)
                score += comment_quality * 20
            
            # 타입 힌트
            type_hints = len(re.findall(r':\s*[A-Za-z]', code))
            score += min(10, type_hints * 2)
            
            return min(100, score)
            
        except Exception as e:
            logger.warning(f"문서화 계산 오류: {e}")
            return 50.0
    
    async def _calculate_test_coverage_async(self, file_path: str) -> float:
        """테스트 커버리지 계산 (비동기)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._calculate_test_coverage, file_path)
    
    def _calculate_test_coverage(self, file_path: str) -> float:
        """테스트 커버리지 추정"""
        try:
            # 테스트 파일 존재 여부 확인
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            test_patterns = [
                f"test_{base_name}.py",
                f"{base_name}_test.py",
                f"tests/test_{base_name}.py",
                f"test/test_{base_name}.py"
            ]
            
            test_file_exists = any(os.path.exists(pattern) for pattern in test_patterns)
            
            if test_file_exists:
                return 80.0  # 테스트 파일이 있으면 기본 80점
            
            # 코드 내 테스트 관련 패턴 체크
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            test_indicators = [
                'import unittest',
                'import pytest',
                'def test_',
                'class Test',
                'assert ',
                'assertEqual',
                'assertTrue',
                'assertFalse'
            ]
            
            test_score = 0
            for indicator in test_indicators:
                if indicator in code:
                    test_score += 10
            
            return min(60, test_score)  # 최대 60점
            
        except Exception as e:
            logger.warning(f"테스트 커버리지 계산 오류: {e}")
            return 0.0
    
    def save_quality_metrics(self, file_path: str, metrics: QualityMetrics):
        """품질 메트릭 저장"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO quality_metrics 
                (timestamp, file_path, complexity_score, maintainability_score, 
                 readability_score, performance_score, security_score, 
                 documentation_score, test_coverage_score, overall_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                file_path,
                metrics.complexity_score,
                metrics.maintainability_score,
                metrics.readability_score,
                metrics.performance_score,
                metrics.security_score,
                metrics.documentation_score,
                metrics.test_coverage_score,
                metrics.overall_score
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"품질 메트릭 저장 오류: {e}")
    
    def generate_optimization_suggestions(self, file_path: str, metrics: QualityMetrics) -> List[OptimizationSuggestion]:
        """최적화 제안 생성"""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 복잡도 개선 제안
            if metrics.complexity_score < 70:
                suggestions.append(OptimizationSuggestion(
                    type="complexity",
                    description="함수를 더 작은 단위로 분할하여 복잡도를 줄이세요",
                    priority="high",
                    code_snippet=self._generate_refactoring_example("function_split"),
                    expected_improvement=15.0
                ))
            
            # 성능 개선 제안
            if metrics.performance_score < 80:
                if 'for ' in code and 'append(' in code:
                    suggestions.append(OptimizationSuggestion(
                        type="performance",
                        description="list comprehension을 사용하여 성능을 향상시키세요",
                        priority="medium",
                        code_snippet="# 대신에: [item for item in items if condition]",
                        expected_improvement=10.0
                    ))
                
                if not any(pattern in code for pattern in ['async', 'threading', 'multiprocessing']):
                    suggestions.append(OptimizationSuggestion(
                        type="performance",
                        description="비동기 처리나 병렬 처리를 고려해보세요",
                        priority="medium",
                        code_snippet="import asyncio\n\nasync def async_function():\n    await some_async_operation()",
                        expected_improvement=20.0
                    ))
            
            # 가독성 개선 제안
            if metrics.readability_score < 75:
                suggestions.append(OptimizationSuggestion(
                    type="readability",
                    description="더 의미있는 변수명과 함수명을 사용하세요",
                    priority="medium",
                    code_snippet="# 좋은 예: calculate_user_score() 대신 calc() 사용 피하기",
                    expected_improvement=12.0
                ))
            
            # 문서화 개선 제안
            if metrics.documentation_score < 60:
                suggestions.append(OptimizationSuggestion(
                    type="documentation",
                    description="함수와 클래스에 독스트링을 추가하세요",
                    priority="low",
                    code_snippet='def function_name(param1: str) -> int:\n    """함수 설명\n    \n    Args:\n        param1: 매개변수 설명\n    \n    Returns:\n        반환값 설명\n    """',
                    expected_improvement=15.0
                ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"최적화 제안 생성 오류: {e}")
            return []
    
    def _generate_refactoring_example(self, refactor_type: str) -> str:
        """리팩토링 예제 생성"""
        examples = {
            "function_split": """
# Before: 긴 함수
def long_function():
    # 50+ lines of code
    pass

# After: 분할된 함수
def main_function():
    result1 = helper_function_1()
    result2 = helper_function_2(result1)
    return process_results(result2)

def helper_function_1():
    # 구체적인 작업 1
    pass

def helper_function_2(input_data):
    # 구체적인 작업 2
    pass
""",
            "performance": """
# Before: 느린 코드
result = []
for item in items:
    if condition(item):
        result.append(transform(item))

# After: 빠른 코드
result = [transform(item) for item in items if condition(item)]
"""
        }
        
        return examples.get(refactor_type, "# 리팩토링 예제")
    
    async def apply_automatic_improvements(self, file_path: str) -> Dict[str, Any]:
        """자동 개선 적용"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            improved_code = original_code
            improvements_made = []
            
            # 1. 자동 포맷팅 (간단한 개선)
            improved_code = self._apply_auto_formatting(improved_code)
            if improved_code != original_code:
                improvements_made.append("auto_formatting")
            
            # 2. 간단한 성능 최적화
            optimized_code = self._apply_performance_optimizations(improved_code)
            if optimized_code != improved_code:
                improvements_made.append("performance_optimization")
                improved_code = optimized_code
            
            # 3. 보안 개선
            secured_code = self._apply_security_improvements(improved_code)
            if secured_code != improved_code:
                improvements_made.append("security_improvements")
                improved_code = secured_code
            
            # 개선된 코드를 새 파일로 저장
            if improvements_made:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                improved_filename = f"improved_{os.path.basename(file_path).replace('.py', '')}_{timestamp}.py"
                
                with open(improved_filename, 'w', encoding='utf-8') as f:
                    f.write(improved_code)
                
                logger.info(f"🛠️ 자동 개선 완료: {improved_filename}")
                
                return {
                    'success': True,
                    'improved_file': improved_filename,
                    'improvements_made': improvements_made,
                    'original_size': len(original_code),
                    'improved_size': len(improved_code)
                }
            
            return {'success': False, 'reason': 'no_improvements_needed'}
            
        except Exception as e:
            logger.error(f"자동 개선 적용 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_auto_formatting(self, code: str) -> str:
        """자동 포맷팅 적용"""
        try:
            lines = code.splitlines()
            formatted_lines = []
            
            for line in lines:
                # 불필요한 공백 제거
                formatted_line = line.rstrip()
                
                # 연산자 주변 공백 정리
                formatted_line = re.sub(r'([=+\-*/])\s*([=+\-*/])', r'\1\2', formatted_line)
                formatted_line = re.sub(r'([^=!<>])[=]([^=])', r'\1 = \2', formatted_line)
                
                formatted_lines.append(formatted_line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"자동 포맷팅 오류: {e}")
            return code
    
    def _apply_performance_optimizations(self, code: str) -> str:
        """성능 최적화 적용"""
        try:
            # 간단한 최적화 패턴 적용
            optimized = code
            
            # range(len()) -> enumerate() 변환
            optimized = re.sub(
                r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):',
                r'for \1, item in enumerate(\2):',
                optimized
            )
            
            # 문자열 연결 최적화 제안 (주석으로)
            if '+ "' in optimized or "+ '" in optimized:
                optimized = "# 성능 팁: 문자열 연결 시 f-string 또는 join() 사용 권장\n" + optimized
            
            return optimized
            
        except Exception as e:
            logger.warning(f"성능 최적화 오류: {e}")
            return code
    
    def _apply_security_improvements(self, code: str) -> str:
        """보안 개선 적용"""
        try:
            secured = code
            
            # 위험한 함수 사용 경고 추가
            if 'eval(' in secured:
                secured = "# 보안 경고: eval() 사용을 피하고 ast.literal_eval() 고려\n" + secured
            
            if 'exec(' in secured:
                secured = "# 보안 경고: exec() 사용은 보안 위험이 있습니다\n" + secured
            
            return secured
            
        except Exception as e:
            logger.warning(f"보안 개선 오류: {e}")
            return code
    
    async def generate_quality_report(self, file_paths: List[str]) -> Dict[str, Any]:
        """종합 품질 리포트 생성"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_files_analyzed': len(file_paths),
                'overall_metrics': {},
                'file_details': [],
                'recommendations': [],
                'trends': {}
            }
            
            all_metrics = []
            
            # 각 파일 분석
            for file_path in file_paths:
                if os.path.exists(file_path) and file_path.endswith('.py'):
                    metrics = await self.analyze_code_quality(file_path)
                    suggestions = self.generate_optimization_suggestions(file_path, metrics)
                    
                    file_detail = {
                        'file_path': file_path,
                        'metrics': metrics.__dict__,
                        'suggestions_count': len(suggestions),
                        'priority_suggestions': len([s for s in suggestions if s.priority == 'high'])
                    }
                    
                    report['file_details'].append(file_detail)
                    all_metrics.append(metrics)
                    report['recommendations'].extend(suggestions)
            
            # 전체 평균 계산
            if all_metrics:
                report['overall_metrics'] = {
                    'avg_complexity': sum(m.complexity_score for m in all_metrics) / len(all_metrics),
                    'avg_maintainability': sum(m.maintainability_score for m in all_metrics) / len(all_metrics),
                    'avg_readability': sum(m.readability_score for m in all_metrics) / len(all_metrics),
                    'avg_performance': sum(m.performance_score for m in all_metrics) / len(all_metrics),
                    'avg_security': sum(m.security_score for m in all_metrics) / len(all_metrics),
                    'avg_documentation': sum(m.documentation_score for m in all_metrics) / len(all_metrics),
                    'avg_test_coverage': sum(m.test_coverage_score for m in all_metrics) / len(all_metrics),
                    'overall_average': sum(m.overall_score for m in all_metrics) / len(all_metrics)
                }
            
            # 리포트 저장
            report_filename = f"code_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 품질 리포트 생성 완료: {report_filename}")
            return report
            
        except Exception as e:
            logger.error(f"품질 리포트 생성 오류: {e}")
            return {}

async def main():
    """메인 실행 함수"""
    enhancer = AdvancedCodeQualityEnhancer()
    
    # 분석할 파일들 찾기
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    # 메인 파일들 우선 분석
    priority_files = [
        './self_evolving_ai.py',
        './evolution_monitor_dashboard.py',
        './ai_evolution_predictor.py',
        './ai_performance_benchmark.py',
        './ai_creative_studio.py',
        './ai_coaching_system.py',
        './ai_system_monitor.py'
    ]
    
    analysis_files = []
    for file in priority_files:
        if os.path.exists(file):
            analysis_files.append(file)
    
    # 최대 10개 파일만 분석 (성능상 이유)
    analysis_files.extend([f for f in python_files[:10] if f not in analysis_files])
    
    print("🎯 고급 코드 품질 향상 시스템 시작")
    print("=" * 60)
    
    # 품질 분석
    print(f"📊 {len(analysis_files)}개 파일 품질 분석 중...")
    
    quality_report = await enhancer.generate_quality_report(analysis_files)
    
    if quality_report:
        print(f"\n📈 전체 품질 점수:")
        metrics = quality_report['overall_metrics']
        print(f"   🔧 복잡도: {metrics['avg_complexity']:.1f}/100")
        print(f"   🛠️ 유지보수성: {metrics['avg_maintainability']:.1f}/100")
        print(f"   📖 가독성: {metrics['avg_readability']:.1f}/100")
        print(f"   ⚡ 성능: {metrics['avg_performance']:.1f}/100")
        print(f"   🔒 보안: {metrics['avg_security']:.1f}/100")
        print(f"   📚 문서화: {metrics['avg_documentation']:.1f}/100")
        print(f"   🧪 테스트 커버리지: {metrics['avg_test_coverage']:.1f}/100")
        print(f"   🎯 종합 점수: {metrics['overall_average']:.1f}/100")
        
        # 개선 제안
        high_priority = len([r for r in quality_report['recommendations'] if r.priority == 'high'])
        medium_priority = len([r for r in quality_report['recommendations'] if r.priority == 'medium'])
        
        print(f"\n💡 개선 제안:")
        print(f"   🔴 높은 우선순위: {high_priority}개")
        print(f"   🟡 중간 우선순위: {medium_priority}개")
        
        # 자동 개선 적용
        print(f"\n🛠️ 자동 개선 적용 중...")
        for file_path in analysis_files[:3]:  # 처음 3개 파일만
            result = await enhancer.apply_automatic_improvements(file_path)
            if result.get('success'):
                print(f"   ✅ {file_path}: {', '.join(result['improvements_made'])}")
        
        print(f"\n✅ 품질 향상 완료!")
        print(f"📋 상세 리포트: code_quality_report_*.json")

if __name__ == "__main__":
    asyncio.run(main())
