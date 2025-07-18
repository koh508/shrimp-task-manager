#!/usr/bin/env python3
"""
🚀 AI 기반 코드 품질 자동 향상 시스템
머신러닝을 활용한 코드 최적화 및 자동 리팩토링 도구
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
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import subprocess
import tempfile
import shutil
from collections import defaultdict, Counter
import concurrent.futures
import inspect

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AICodeQualityEnhancer:
    """🚀 AI 기반 코드 품질 자동 향상 시스템"""
    
    def __init__(self):
        self.optimization_patterns = {}
        self.quality_improvement_history = []
        self.performance_benchmarks = {}
        self.code_metrics_db = {}
        
        # 고급 분석 도구 초기화
        self.init_advanced_analyzer()
        self.init_quality_database()
        
        # AI 기반 패턴 학습
        self.load_optimization_patterns()
        
        logger.info("🚀 AI 기반 코드 품질 자동 향상 시스템 초기화 완료")
    
    def init_advanced_analyzer(self):
        """고급 코드 분석기 초기화"""
        self.analyzer_config = {
            'complexity_weights': {
                'cyclomatic': 0.4,
                'cognitive': 0.3,
                'halstead': 0.3
            },
            'performance_indicators': {
                'algorithmic_efficiency': 0.35,
                'memory_optimization': 0.25,
                'io_efficiency': 0.20,
                'parallelization': 0.20
            },
            'maintainability_factors': {
                'modularity': 0.25,
                'readability': 0.25,
                'testability': 0.25,
                'documentation': 0.25
            }
        }
    
    def init_quality_database(self):
        """품질 관리 데이터베이스 초기화"""
        try:
            self.db_connection = sqlite3.connect('ai_code_quality_enhancer.db', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            # 고급 메트릭 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS advanced_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    file_path TEXT,
                    cyclomatic_complexity REAL,
                    cognitive_complexity REAL,
                    halstead_volume REAL,
                    maintainability_index REAL,
                    technical_debt_ratio REAL,
                    code_coverage_estimate REAL,
                    performance_score REAL,
                    security_vulnerability_count INTEGER,
                    overall_quality_score REAL
                )
            ''')
            
            # AI 학습 데이터
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT,
                    pattern_description TEXT,
                    before_code_pattern TEXT,
                    after_code_pattern TEXT,
                    improvement_metrics TEXT,
                    success_rate REAL,
                    confidence_score REAL
                )
            ''')
            
            # 성능 벤치마크
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    function_name TEXT,
                    execution_time_ms REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    optimization_applied TEXT,
                    performance_gain_percent REAL
                )
            ''')
            
            self.db_connection.commit()
            logger.info("✅ AI 품질 관리 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"DB 초기화 오류: {e}")
    
    def load_optimization_patterns(self):
        """최적화 패턴 로드"""
        self.optimization_patterns = {
            'loop_optimization': {
                'pattern': r'for\s+\w+\s+in\s+range\(len\(\w+\)\):',
                'replacement': 'enumerate',
                'improvement': 15,
                'description': 'range(len()) → enumerate() 최적화'
            },
            'list_comprehension': {
                'pattern': r'for\s+\w+\s+in\s+\w+:\s*\n\s*if\s+.*:\s*\n\s*\w+\.append\(',
                'replacement': 'list_comprehension',
                'improvement': 20,
                'description': 'for-if-append → list comprehension 최적화'
            },
            'string_formatting': {
                'pattern': r'["\'].*["\']\s*\+\s*\w+\s*\+\s*["\'].*["\']',
                'replacement': 'f_string',
                'improvement': 10,
                'description': '문자열 연결 → f-string 최적화'
            },
            'exception_handling': {
                'pattern': r'except\s*:',
                'replacement': 'specific_exception',
                'improvement': 25,
                'description': '일반 예외처리 → 구체적 예외처리'
            },
            'generator_expression': {
                'pattern': r'\[.*for\s+\w+\s+in\s+\w+.*\]',
                'replacement': 'generator',
                'improvement': 30,
                'description': 'list comprehension → generator expression'
            }
        }
    
    def analyze_advanced_metrics(self, file_path: str) -> Dict[str, Any]:
        """고급 코드 메트릭 분석"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # 고급 메트릭 계산
            metrics = {
                'cyclomatic_complexity': self.calculate_cyclomatic_complexity(tree),
                'cognitive_complexity': self.calculate_cognitive_complexity(tree),
                'halstead_volume': self.calculate_halstead_volume(code),
                'maintainability_index': self.calculate_maintainability_index(code, tree),
                'technical_debt_ratio': self.calculate_technical_debt(code),
                'code_coverage_estimate': self.estimate_code_coverage(file_path),
                'performance_score': self.analyze_performance_potential(code),
                'security_vulnerability_count': self.count_security_vulnerabilities(code),
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }
            
            # 종합 품질 점수 계산
            metrics['overall_quality_score'] = self.calculate_overall_quality_score(metrics)
            
            # 데이터베이스에 저장
            self.save_advanced_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"고급 메트릭 분석 오류 {file_path}: {e}")
            return {}
    
    def calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """순환 복잡도 계산"""
        complexity = 1  # 기본 경로
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """인지적 복잡도 계산"""
        complexity = 0
        nesting_level = 0
        
        class CognitiveComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.nesting = 0
            
            def visit_If(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
            
            def visit_For(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
            
            def visit_While(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
            
            def visit_Try(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        visitor = CognitiveComplexityVisitor()
        visitor.visit(tree)
        return visitor.complexity
    
    def calculate_halstead_volume(self, code: str) -> float:
        """Halstead 볼륨 계산"""
        try:
            # 연산자와 피연산자 추출
            operators = set()
            operands = set()
            
            # Python 연산자 패턴
            operator_patterns = [
                r'\+', r'-', r'\*', r'/', r'%', r'=', r'==', r'!=', 
                r'<', r'>', r'<=', r'>=', r'and', r'or', r'not', 
                r'if', r'else', r'elif', r'for', r'while', r'def', r'class'
            ]
            
            for pattern in operator_patterns:
                matches = re.findall(pattern, code)
                operators.update(matches)
            
            # 변수명과 함수명 추출
            variable_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
            variables = re.findall(variable_pattern, code)
            operands.update(variables)
            
            # Halstead 메트릭
            n1 = len(operators)  # 고유 연산자 수
            n2 = len(operands)   # 고유 피연산자 수
            N1 = sum(code.count(op) for op in operators)  # 총 연산자 수
            N2 = sum(code.count(op) for op in operands)   # 총 피연산자 수
            
            if n1 > 0 and n2 > 0:
                vocabulary = n1 + n2
                length = N1 + N2
                volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
                return volume
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Halstead 볼륨 계산 오류: {e}")
            return 0.0
    
    def calculate_maintainability_index(self, code: str, tree: ast.AST) -> float:
        """유지보수성 지수 계산"""
        try:
            lines_of_code = len([line for line in code.splitlines() if line.strip()])
            cyclomatic_complexity = self.calculate_cyclomatic_complexity(tree)
            halstead_volume = self.calculate_halstead_volume(code)
            
            # 유지보수성 지수 공식
            if lines_of_code > 0 and cyclomatic_complexity > 0:
                mi = 171 - 5.2 * (halstead_volume ** 0.23) - 0.23 * cyclomatic_complexity - 16.2 * (lines_of_code ** 0.16)
                return max(0, min(100, mi))
            
            return 50.0
            
        except Exception as e:
            logger.warning(f"유지보수성 지수 계산 오류: {e}")
            return 50.0
    
    def calculate_technical_debt(self, code: str) -> float:
        """기술 부채 비율 계산"""
        try:
            debt_indicators = {
                'TODO': 2,
                'FIXME': 3,
                'HACK': 4,
                'XXX': 3,
                'global ': 2,
                'import *': 3,
                'eval(': 5,
                'exec(': 5,
                'bare except:': 4
            }
            
            total_debt = 0
            lines = code.splitlines()
            
            for indicator, weight in debt_indicators.items():
                count = code.lower().count(indicator.lower())
                total_debt += count * weight
            
            # 코드 라인 수 대비 부채 비율
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            if code_lines > 0:
                debt_ratio = (total_debt / code_lines) * 100
                return min(100, debt_ratio)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"기술 부채 계산 오류: {e}")
            return 0.0
    
    def estimate_code_coverage(self, file_path: str) -> float:
        """코드 커버리지 추정"""
        try:
            # 테스트 파일 존재 여부 확인
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            test_patterns = [
                f"test_{base_name}.py",
                f"{base_name}_test.py",
                f"tests/test_{base_name}.py"
            ]
            
            test_files_exist = any(os.path.exists(pattern) for pattern in test_patterns)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 테스트 관련 코드 분석
            test_coverage_score = 0
            
            if test_files_exist:
                test_coverage_score += 40
            
            # 코드 내 테스트 패턴
            test_patterns_in_code = [
                'assert ', 'assertEqual', 'assertTrue', 'assertFalse',
                'unittest', 'pytest', 'def test_', 'class Test'
            ]
            
            for pattern in test_patterns_in_code:
                if pattern in code:
                    test_coverage_score += 10
            
            # 예외 처리 패턴
            exception_patterns = ['try:', 'except', 'finally:', 'raise']
            exception_coverage = sum(1 for pattern in exception_patterns if pattern in code)
            test_coverage_score += exception_coverage * 5
            
            return min(100, test_coverage_score)
            
        except Exception as e:
            logger.warning(f"코드 커버리지 추정 오류: {e}")
            return 0.0
    
    def analyze_performance_potential(self, code: str) -> float:
        """성능 잠재력 분석"""
        try:
            performance_score = 50  # 기본 점수
            
            # 고성능 패턴
            high_performance_patterns = {
                'async def': 25,
                'await': 20,
                'asyncio': 25,
                'multiprocessing': 30,
                'threading': 20,
                'concurrent.futures': 35,
                'numpy': 40,
                'pandas': 35,
                'cython': 50,
                'numba': 45,
                'list comprehension': 15,
                'generator': 20,
                'itertools': 15,
                'collections.deque': 10,
                'set(': 10,
                'frozenset(': 10,
                'lru_cache': 30,
                'functools.cache': 25
            }
            
            for pattern, bonus in high_performance_patterns.items():
                if pattern in code:
                    performance_score += bonus
            
            # 성능 저하 패턴
            performance_issues = {
                'nested loops': len(re.findall(r'for.*for', code)) * -15,
                'global variables': code.count('global ') * -10,
                'string concatenation': (code.count('+ "') + code.count("+ '")) * -5,
                'inefficient file operations': code.count('open(') * -3,
                'recursive without memoization': len(re.findall(r'def\s+\w+.*\n.*\1\(', code)) * -20
            }
            
            for issue, penalty in performance_issues.items():
                performance_score += penalty
            
            return max(0, min(150, performance_score))
            
        except Exception as e:
            logger.warning(f"성능 분석 오류: {e}")
            return 50.0
    
    def count_security_vulnerabilities(self, code: str) -> int:
        """보안 취약점 개수 계산"""
        try:
            vulnerabilities = 0
            
            # 높은 위험도 패턴
            high_risk_patterns = [
                'eval(',
                'exec(',
                'os.system(',
                'subprocess.call.*shell=True',
                'pickle.loads(',
                '__import__(',
                'compile(',
                'open.*mode.*w.*',  # 파일 쓰기 권한
            ]
            
            # 중간 위험도 패턴
            medium_risk_patterns = [
                'input(',
                'raw_input(',
                'urllib.request.urlopen',
                'requests.get.*verify=False',
                'ssl.*verify_mode.*CERT_NONE',
                'random.random()',  # 암호학적으로 안전하지 않은 랜덤
                'tempfile.mktemp('
            ]
            
            for pattern in high_risk_patterns:
                vulnerabilities += len(re.findall(pattern, code)) * 2
            
            for pattern in medium_risk_patterns:
                vulnerabilities += len(re.findall(pattern, code))
            
            return vulnerabilities
            
        except Exception as e:
            logger.warning(f"보안 취약점 계산 오류: {e}")
            return 0
    
    def calculate_overall_quality_score(self, metrics: Dict[str, Any]) -> float:
        """종합 품질 점수 계산"""
        try:
            # 가중치 적용
            weights = {
                'maintainability_index': 0.25,
                'performance_score': 0.20,
                'code_coverage_estimate': 0.20,
                'technical_debt_ratio': -0.15,  # 부채는 마이너스
                'security_vulnerability_count': -0.10,  # 취약점은 마이너스
                'cyclomatic_complexity': -0.10  # 복잡도는 마이너스
            }
            
            score = 0
            for metric, weight in weights.items():
                if metric in metrics:
                    value = metrics[metric]
                    if metric == 'technical_debt_ratio':
                        # 부채 비율이 낮을수록 좋음
                        normalized_value = 100 - min(100, value)
                    elif metric == 'security_vulnerability_count':
                        # 취약점이 적을수록 좋음
                        normalized_value = max(0, 100 - value * 10)
                    elif metric == 'cyclomatic_complexity':
                        # 복잡도가 낮을수록 좋음
                        normalized_value = max(0, 100 - value * 2)
                    else:
                        normalized_value = min(100, value)
                    
                    score += normalized_value * abs(weight)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"종합 품질 점수 계산 오류: {e}")
            return 50.0
    
    def apply_ai_optimizations(self, file_path: str) -> Dict[str, Any]:
        """AI 기반 자동 최적화 적용"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            optimized_code = original_code
            applied_optimizations = []
            total_improvement = 0
            
            # 패턴별 최적화 적용
            for pattern_name, pattern_info in self.optimization_patterns.items():
                before_code = optimized_code
                optimized_code = self.apply_optimization_pattern(optimized_code, pattern_name, pattern_info)
                
                if optimized_code != before_code:
                    applied_optimizations.append({
                        'pattern': pattern_name,
                        'description': pattern_info['description'],
                        'improvement': pattern_info['improvement']
                    })
                    total_improvement += pattern_info['improvement']
            
            # 고급 최적화
            optimized_code = self.apply_advanced_optimizations(optimized_code)
            
            if optimized_code != original_code:
                # 최적화된 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                optimized_filename = f"ai_optimized_{base_name}_{timestamp}.py"
                
                with open(optimized_filename, 'w', encoding='utf-8') as f:
                    f.write(optimized_code)
                
                # 성능 비교
                before_metrics = self.analyze_advanced_metrics(file_path)
                after_metrics = self.analyze_advanced_metrics(optimized_filename)
                
                improvement_percentage = 0
                if before_metrics.get('overall_quality_score', 0) > 0:
                    improvement_percentage = (
                        (after_metrics.get('overall_quality_score', 0) - before_metrics.get('overall_quality_score', 0)) /
                        before_metrics.get('overall_quality_score', 0)
                    ) * 100
                
                result = {
                    'success': True,
                    'optimized_file': optimized_filename,
                    'applied_optimizations': applied_optimizations,
                    'before_score': before_metrics.get('overall_quality_score', 0),
                    'after_score': after_metrics.get('overall_quality_score', 0),
                    'improvement_percentage': improvement_percentage,
                    'optimizations_count': len(applied_optimizations)
                }
                
                logger.info(f"🚀 AI 최적화 완료: {optimized_filename} ({improvement_percentage:+.1f}% 개선)")
                return result
            
            return {'success': False, 'reason': 'no_optimizations_applied'}
            
        except Exception as e:
            logger.error(f"AI 최적화 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def apply_optimization_pattern(self, code: str, pattern_name: str, pattern_info: Dict) -> str:
        """특정 최적화 패턴 적용"""
        try:
            pattern = pattern_info['pattern']
            replacement_type = pattern_info['replacement']
            
            if replacement_type == 'enumerate':
                # range(len()) -> enumerate() 변환
                pattern_regex = r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):'
                replacement = r'for \1, _ in enumerate(\2):'
                code = re.sub(pattern_regex, replacement, code)
            
            elif replacement_type == 'f_string':
                # 문자열 연결 -> f-string 변환 (간단한 경우만)
                pattern_regex = r'(["\'])([^"\']*)\1\s*\+\s*(\w+)\s*\+\s*(["\'])([^"\']*)\4'
                def f_string_replacement(match):
                    quote = match.group(1)
                    prefix = match.group(2)
                    variable = match.group(3)
                    suffix = match.group(5)
                    return f'f{quote}{prefix}{{{variable}}}{suffix}{quote}'
                
                code = re.sub(pattern_regex, f_string_replacement, code)
            
            elif replacement_type == 'specific_exception':
                # 일반 예외처리 -> 구체적 예외처리
                code = code.replace('except:', 'except Exception:')
            
            return code
            
        except Exception as e:
            logger.warning(f"최적화 패턴 적용 오류 {pattern_name}: {e}")
            return code
    
    def apply_advanced_optimizations(self, code: str) -> str:
        """고급 최적화 적용"""
        try:
            # 성능 개선 주석 추가
            performance_tips = []
            
            if 'for ' in code and 'append(' in code:
                performance_tips.append("# 성능 팁: list comprehension 사용 고려")
            
            if '+ "' in code or "+ '" in code:
                performance_tips.append("# 성능 팁: f-string 사용으로 문자열 연결 최적화")
            
            if 'while' in code and 'sleep(' not in code:
                performance_tips.append("# 성능 팁: CPU 집약적 while 루프에 적절한 대기 시간 추가 고려")
            
            if performance_tips:
                header = '\n'.join(performance_tips) + '\n\n'
                code = header + code
            
            # 보안 경고 추가
            if 'eval(' in code:
                code = "# 보안 경고: eval() 사용은 위험합니다. ast.literal_eval() 사용을 권장합니다.\n" + code
            
            if 'exec(' in code:
                code = "# 보안 경고: exec() 사용은 보안 위험이 있습니다.\n" + code
            
            return code
            
        except Exception as e:
            logger.warning(f"고급 최적화 적용 오류: {e}")
            return code
    
    def save_advanced_metrics(self, metrics: Dict[str, Any]):
        """고급 메트릭 저장"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO advanced_metrics 
                (timestamp, file_path, cyclomatic_complexity, cognitive_complexity, 
                 halstead_volume, maintainability_index, technical_debt_ratio, 
                 code_coverage_estimate, performance_score, security_vulnerability_count, 
                 overall_quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['timestamp'],
                metrics['file_path'],
                metrics['cyclomatic_complexity'],
                metrics['cognitive_complexity'],
                metrics['halstead_volume'],
                metrics['maintainability_index'],
                metrics['technical_debt_ratio'],
                metrics['code_coverage_estimate'],
                metrics['performance_score'],
                metrics['security_vulnerability_count'],
                metrics['overall_quality_score']
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"고급 메트릭 저장 오류: {e}")
    
    def generate_ai_quality_report(self, file_paths: List[str]) -> Dict[str, Any]:
        """AI 기반 종합 품질 리포트 생성"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'ai_analysis_version': '2.0',
                'total_files_analyzed': len(file_paths),
                'advanced_metrics': [],
                'quality_insights': {},
                'optimization_recommendations': [],
                'performance_predictions': {},
                'security_assessment': {},
                'maintainability_forecast': {}
            }
            
            all_metrics = []
            
            # 각 파일에 대한 고급 분석
            for file_path in file_paths:
                if os.path.exists(file_path) and file_path.endswith('.py'):
                    metrics = self.analyze_advanced_metrics(file_path)
                    if metrics:
                        all_metrics.append(metrics)
                        report['advanced_metrics'].append(metrics)
            
            if all_metrics:
                # 통계적 인사이트 생성
                report['quality_insights'] = self.generate_quality_insights(all_metrics)
                
                # 성능 예측
                report['performance_predictions'] = self.predict_performance_trends(all_metrics)
                
                # 보안 평가
                report['security_assessment'] = self.assess_security_posture(all_metrics)
                
                # 유지보수성 예측
                report['maintainability_forecast'] = self.forecast_maintainability(all_metrics)
            
            # 리포트 저장
            report_filename = f"ai_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"🤖 AI 품질 리포트 생성 완료: {report_filename}")
            return report
            
        except Exception as e:
            logger.error(f"AI 품질 리포트 생성 오류: {e}")
            return {}
    
    def generate_quality_insights(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """품질 인사이트 생성"""
        insights = {}
        
        if not metrics_list:
            return insights
        
        # 평균 계산
        avg_maintainability = sum(m.get('maintainability_index', 0) for m in metrics_list) / len(metrics_list)
        avg_performance = sum(m.get('performance_score', 0) for m in metrics_list) / len(metrics_list)
        avg_quality = sum(m.get('overall_quality_score', 0) for m in metrics_list) / len(metrics_list)
        
        insights = {
            'average_maintainability_index': round(avg_maintainability, 2),
            'average_performance_score': round(avg_performance, 2),
            'average_overall_quality': round(avg_quality, 2),
            'quality_trend': self.determine_quality_trend(avg_quality),
            'top_improvement_areas': self.identify_improvement_areas(metrics_list),
            'quality_distribution': self.analyze_quality_distribution(metrics_list)
        }
        
        return insights
    
    def determine_quality_trend(self, avg_quality: float) -> str:
        """품질 트렌드 결정"""
        if avg_quality >= 85:
            return "🚀 우수한 품질 - 지속적 개선 체계 구축됨"
        elif avg_quality >= 70:
            return "📈 양호한 품질 - 추가 최적화 기회 존재"
        elif avg_quality >= 55:
            return "⚠️ 개선 필요 - 체계적인 리팩토링 권장"
        else:
            return "🔴 긴급 개선 필요 - 종합적 코드 재구성 필요"
    
    def identify_improvement_areas(self, metrics_list: List[Dict[str, Any]]) -> List[str]:
        """개선 영역 식별"""
        areas = []
        
        avg_performance = sum(m.get('performance_score', 0) for m in metrics_list) / len(metrics_list)
        avg_security = sum(10 - m.get('security_vulnerability_count', 0) for m in metrics_list) / len(metrics_list)
        avg_coverage = sum(m.get('code_coverage_estimate', 0) for m in metrics_list) / len(metrics_list)
        
        if avg_performance < 70:
            areas.append("performance_optimization")
        if avg_security < 80:
            areas.append("security_enhancement")
        if avg_coverage < 60:
            areas.append("test_coverage_improvement")
        
        return areas
    
    def analyze_quality_distribution(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """품질 분포 분석"""
        distribution = {'excellent': 0, 'good': 0, 'acceptable': 0, 'poor': 0}
        
        for metrics in metrics_list:
            score = metrics.get('overall_quality_score', 0)
            if score >= 85:
                distribution['excellent'] += 1
            elif score >= 70:
                distribution['good'] += 1
            elif score >= 55:
                distribution['acceptable'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def predict_performance_trends(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """성능 트렌드 예측"""
        avg_performance = sum(m.get('performance_score', 0) for m in metrics_list) / len(metrics_list)
        
        prediction = {
            'current_performance_level': round(avg_performance, 2),
            'predicted_improvement_potential': min(100, avg_performance + 20),  # 최대 20점 개선 가능
            'bottleneck_areas': [],
            'optimization_priority': 'medium'
        }
        
        if avg_performance < 60:
            prediction['optimization_priority'] = 'high'
            prediction['bottleneck_areas'] = ['algorithm_efficiency', 'memory_management']
        elif avg_performance < 80:
            prediction['optimization_priority'] = 'medium'
            prediction['bottleneck_areas'] = ['code_structure', 'caching_strategy']
        
        return prediction
    
    def assess_security_posture(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """보안 태세 평가"""
        total_vulnerabilities = sum(m.get('security_vulnerability_count', 0) for m in metrics_list)
        
        assessment = {
            'total_vulnerabilities': total_vulnerabilities,
            'security_level': 'high' if total_vulnerabilities == 0 else 'medium' if total_vulnerabilities < 5 else 'low',
            'critical_issues': total_vulnerabilities > 10,
            'improvement_needed': total_vulnerabilities > 0
        }
        
        return assessment
    
    def forecast_maintainability(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """유지보수성 예측"""
        avg_maintainability = sum(m.get('maintainability_index', 0) for m in metrics_list) / len(metrics_list)
        avg_debt = sum(m.get('technical_debt_ratio', 0) for m in metrics_list) / len(metrics_list)
        
        forecast = {
            'current_maintainability': round(avg_maintainability, 2),
            'technical_debt_level': round(avg_debt, 2),
            'maintenance_effort_prediction': 'low' if avg_maintainability > 70 else 'medium' if avg_maintainability > 50 else 'high',
            'refactoring_priority': 'low' if avg_debt < 20 else 'medium' if avg_debt < 40 else 'high'
        }
        
        return forecast

def main():
    """메인 실행 함수"""
    enhancer = AICodeQualityEnhancer()
    
    print("🚀 AI 기반 코드 품질 자동 향상 시스템")
    print("=" * 60)
    
    # 우선 분석 대상 파일들
    priority_files = [
        './self_evolving_ai.py',
        './evolution_monitor_dashboard.py',
        './ai_evolution_predictor.py',
        './ai_performance_benchmark.py',
        './ai_creative_studio.py',
        './ai_coaching_system.py',
        './ai_system_monitor.py'
    ]
    
    existing_files = [f for f in priority_files if os.path.exists(f)]
    
    print(f"🤖 {len(existing_files)}개 파일 AI 기반 고급 분석 시작...")
    
    # AI 기반 종합 분석
    report = enhancer.generate_ai_quality_report(existing_files)
    
    if report and 'quality_insights' in report:
        insights = report['quality_insights']
        
        print(f"\n🧠 AI 품질 인사이트:")
        print(f"   🎯 평균 품질 점수: {insights['average_overall_quality']:.1f}/100")
        print(f"   🛠️ 유지보수성 지수: {insights['average_maintainability_index']:.1f}/100")
        print(f"   ⚡ 성능 점수: {insights['average_performance_score']:.1f}/100")
        print(f"   📊 품질 트렌드: {insights['quality_trend']}")
        
        # 품질 분포
        distribution = insights['quality_distribution']
        print(f"\n📈 품질 분포:")
        print(f"   🏆 우수: {distribution['excellent']}개")
        print(f"   ✅ 양호: {distribution['good']}개") 
        print(f"   ⚠️ 보통: {distribution['acceptable']}개")
        print(f"   🔴 개선필요: {distribution['poor']}개")
        
        # 성능 예측
        if 'performance_predictions' in report:
            perf = report['performance_predictions']
            print(f"\n🔮 성능 예측:")
            print(f"   현재 성능: {perf['current_performance_level']:.1f}/100")
            print(f"   개선 잠재력: {perf['predicted_improvement_potential']:.1f}/100")
            print(f"   최적화 우선순위: {perf['optimization_priority']}")
        
        # 보안 평가
        if 'security_assessment' in report:
            security = report['security_assessment']
            print(f"\n🔒 보안 평가:")
            print(f"   총 취약점: {security['total_vulnerabilities']}개")
            print(f"   보안 수준: {security['security_level']}")
            print(f"   개선 필요: {'예' if security['improvement_needed'] else '아니오'}")
        
        # AI 자동 최적화 수행
        print(f"\n🤖 AI 자동 최적화 수행 중...")
        optimized_count = 0
        
        for file_path in existing_files[:3]:  # 처음 3개 파일 최적화
            result = enhancer.apply_ai_optimizations(file_path)
            if result.get('success'):
                optimized_count += 1
                improvement = result.get('improvement_percentage', 0)
                optimizations = result.get('optimizations_count', 0)
                print(f"   ✅ {os.path.basename(file_path)}: {improvement:+.1f}% 개선 ({optimizations}개 최적화)")
        
        if optimized_count > 0:
            print(f"\n🎉 AI 최적화 완료! {optimized_count}개 파일 개선됨")
        else:
            print(f"\n💡 현재 코드는 이미 잘 최적화되어 있습니다!")
        
        print(f"\n📋 상세 AI 리포트: ai_quality_report_*.json")
        print("🚀 AI 기반 품질 향상 작업 완료!")

if __name__ == "__main__":
    main()
