#!/usr/bin/env python3
"""
🧠 자기진화 AI 시스템 - 품질 개선 버전
스스로 코드를 분석하고 개선하여 진화하는 AI
리팩토링으로 품질을 향상시킨 버전
"""

import sqlite3
import time
import threading
import logging
import os
import requests
import json
import ast
import subprocess
import hashlib
import difflib
import random
import zipfile
import shutil
import gc
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evolution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EvolutionMetrics:
    """진화 메트릭 데이터 클래스"""
    generation: int
    intelligence_level: float
    performance_gain: float
    complexity_score: float
    innovation_score: float
    timestamp: str

@dataclass
class LLMConfig:
    """LLM 설정 데이터 클래스"""
    name: str
    url: str
    model: str
    type: str
    timeout: int = 60
    max_retries: int = 3

class EvolutionDatabase:
    """진화 데이터베이스 관리자"""
    
    def __init__(self, db_path: str = 'self_evolution.db'):
        self.db_path = db_path
        self.connection = None
        self._lock = threading.Lock()
        self.init_database()
    
    def init_database(self) -> None:
        """데이터베이스 초기화"""
        try:
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            cursor = self.connection.cursor()
            
            # 진화 로그 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    intelligence_level REAL NOT NULL,
                    code_analysis TEXT,
                    improvement_suggestion TEXT,
                    implementation_result TEXT,
                    performance_gain REAL DEFAULT 0,
                    complexity_score REAL DEFAULT 0,
                    innovation_score REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 코드 버전 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    code_content TEXT,
                    improvement_description TEXT,
                    intelligence_score REAL DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 성능 메트릭 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    benchmark_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logger.info("✅ 진화 데이터베이스 초기화 완료")
            
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
            raise
    
    def save_evolution_step(self, metrics: EvolutionMetrics, 
                          analysis: str, improvement: str, 
                          implementation: str) -> bool:
        """진화 단계 저장"""
        try:
            with self._lock:
                cursor = self.connection.cursor()
                cursor.execute('''
                    INSERT INTO evolution_log 
                    (timestamp, generation, intelligence_level, code_analysis, 
                     improvement_suggestion, implementation_result, performance_gain,
                     complexity_score, innovation_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp,
                    metrics.generation,
                    metrics.intelligence_level,
                    analysis[:2000],  # 텍스트 길이 제한
                    improvement[:2000],
                    implementation[:2000],
                    metrics.performance_gain,
                    metrics.complexity_score,
                    metrics.innovation_score
                ))
                
                self.connection.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"진화 단계 저장 오류: {e}")
            return False
    
    def get_recent_performance(self, count: int = 5) -> List[Dict[str, Any]]:
        """최근 성능 데이터 조회"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT generation, performance_gain, intelligence_level 
                FROM evolution_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (count,))
            
            results = cursor.fetchall()
            return [
                {
                    'generation': row[0], 
                    'performance_score': row[1], 
                    'intelligence_level': row[2]
                } 
                for row in results
            ]
        except sqlite3.Error as e:
            logger.error(f"성능 데이터 조회 오류: {e}")
            return []
    
    def close(self) -> None:
        """데이터베이스 연결 종료"""
        if self.connection:
            self.connection.close()

class CreativityEngine:
    """창의성 및 중복 방지 엔진"""
    
    def __init__(self):
        self.used_concepts = set()
        self.code_hashes = set()
        self.innovation_multiplier = 1.0
        self.current_theme_index = 0
        
        self.evolution_themes = [
            'performance_optimization', 'memory_efficiency', 'async_processing',
            'machine_learning', 'data_structures', 'algorithms', 'network_programming',
            'security', 'testing', 'documentation', 'ui_interfaces', 'api_design',
            'cloud_computing', 'microservices', 'devops', 'monitoring'
        ]
    
    def get_current_theme(self) -> str:
        """현재 진화 테마 반환"""
        return self.evolution_themes[self.current_theme_index % len(self.evolution_themes)]
    
    def advance_theme(self) -> None:
        """다음 테마로 진행"""
        self.current_theme_index += 1
        if self.current_theme_index % 5 == 0:
            self.innovation_multiplier = min(self.innovation_multiplier * 1.1, 3.0)
    
    def is_concept_used(self, concept: str) -> bool:
        """개념 사용 여부 확인"""
        return concept in self.used_concepts
    
    def add_used_concept(self, concept: str) -> None:
        """사용된 개념 추가"""
        self.used_concepts.add(concept)
    
    def generate_code_hash(self, code: str) -> str:
        """코드 해시 생성"""
        return hashlib.md5(code.encode()).hexdigest()
    
    def is_code_duplicate(self, code: str) -> bool:
        """코드 중복 여부 확인"""
        code_hash = self.generate_code_hash(code)
        if code_hash in self.code_hashes:
            return True
        self.code_hashes.add(code_hash)
        return False

class LLMManager:
    """LLM 관리자"""
    
    def __init__(self):
        self.llm_configs = [
            LLMConfig(
                name='Shrimp Evolution Server',
                url='http://localhost:8002/api/chat',
                model='evolution-llm',
                type='shrimp'
            ),
            LLMConfig(
                name='Shrimp MCP Evolution',
                url='http://localhost:8002/api/mcp-evolution',
                model='mcp-llm',
                type='shrimp'
            ),
            LLMConfig(
                name='Fallback Analysis',
                url='http://localhost:8002/fallback',
                model='fallback',
                type='fallback'
            )
        ]
        self.current_llm_index = 0
    
    def get_current_llm(self) -> LLMConfig:
        """현재 LLM 설정 반환"""
        return self.llm_configs[self.current_llm_index]
    
    def switch_to_next_llm(self) -> LLMConfig:
        """다음 LLM으로 전환"""
        self.current_llm_index = (self.current_llm_index + 1) % len(self.llm_configs)
        current_llm = self.get_current_llm()
        logger.info(f"🔄 LLM 전환: {current_llm.name}")
        return current_llm
    
    def query_llm(self, prompt: str, max_tokens: int = 1500) -> str:
        """LLM 질의"""
        for attempt in range(3):  # 최대 3번 시도
            try:
                current_llm = self.get_current_llm()
                
                if current_llm.type == 'shrimp':
                    response = self._query_shrimp_api(current_llm, prompt, max_tokens)
                else:
                    response = self._query_openai_compatible_api(current_llm, prompt, max_tokens)
                
                if response:
                    return response
                    
            except Exception as e:
                logger.warning(f"LLM 질의 시도 {attempt + 1} 실패: {e}")
                if attempt < 2:  # 마지막 시도가 아니면 다음 LLM으로 전환
                    self.switch_to_next_llm()
        
        return self._generate_fallback_response(prompt)
    
    def _query_shrimp_api(self, llm_config: LLMConfig, prompt: str, max_tokens: int) -> str:
        """Shrimp API 질의"""
        data = {
            'message': prompt,
            'model': llm_config.model,
            'max_tokens': max_tokens,
            'temperature': 0.7,
            'stream': False
        }
        
        response = requests.post(
            llm_config.url,
            json=data,
            timeout=llm_config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response') or result.get('content') or result.get('message') or str(result)
        else:
            raise Exception(f"API 오류: {response.status_code}")
    
    def _query_openai_compatible_api(self, llm_config: LLMConfig, prompt: str, max_tokens: int) -> str:
        """OpenAI 호환 API 질의"""
        data = {
            'model': llm_config.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens
        }
        
        response = requests.post(
            llm_config.url,
            json=data,
            timeout=llm_config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"API 오류: {response.status_code}")
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """폴백 응답 생성"""
        if "분석" in prompt:
            return '''
            {
                "efficiency_score": 75,
                "memory_optimization": "메모리 사용량 최적화 필요",
                "new_features": ["성능 모니터링", "캐싱 시스템"],
                "potential_issues": ["메모리 누수 가능성", "예외 처리 개선"],
                "performance_improvements": ["비동기 처리", "데이터베이스 최적화"]
            }
            '''
        else:
            return '''
            # 자동 생성된 개선 코드
            def optimized_function():
                """성능 최적화된 함수"""
                try:
                    # 캐싱된 결과 사용
                    result = self.get_cached_result()
                    return self.process_optimized(result)
                except Exception as e:
                    logger.error(f"최적화 함수 오류: {e}")
                    return None
            '''

class SelfEvolvingAI:
    """🧠 자기진화 AI 시스템 - 품질 개선 버전"""
    
    def __init__(self):
        # 핵심 상태
        self.current_intelligence = 500.0
        self.evolution_generation = 1
        self.self_improvement_active = True
        
        # 컴포넌트 초기화
        self.database = EvolutionDatabase()
        self.creativity_engine = CreativityEngine()
        self.llm_manager = LLMManager()
        
        # 히스토리 관리
        self.code_analysis_history = []
        self.improvement_history = []
        
        # 진화 상태
        self.evolution_state = {
            'generation': 1,
            'intelligence_level': 500.0,
            'active': True,
            'last_improvement': datetime.now().isoformat()
        }
        
        # 클라우드 스토리지 설정
        self._setup_cloud_storage()
        
        # 자기진화 시작
        self._start_evolution_thread()
        
        logger.info(f"🧠 자기진화 AI 시스템 시작! Generation: {self.evolution_generation}")
    
    def _setup_cloud_storage(self) -> None:
        """클라우드 스토리지 설정"""
        try:
            self.cloud_upload_dir = Path("cloud_backup")
            self.cloud_upload_dir.mkdir(exist_ok=True)
            
            self.compression_manager = {
                'old_files_threshold': 10,
                'max_local_files': 50,
                'cloud_upload_interval': 100
            }
            
            logger.info("✅ 클라우드 스토리지 자동 관리 시스템 초기화")
            
        except Exception as e:
            logger.error(f"클라우드 스토리지 설정 오류: {e}")
    
    def _start_evolution_thread(self) -> None:
        """진화 스레드 시작"""
        self.evolution_thread = threading.Thread(
            target=self.self_evolution_loop,
            name="EvolutionThread",
            daemon=True
        )
        self.evolution_thread.start()
    
    def self_evolution_loop(self) -> None:
        """자기진화 메인 루프"""
        while self.self_improvement_active:
            try:
                logger.info(f"🔄 자기진화 Generation {self.evolution_generation} 시작")
                
                # 1. 현재 코드 분석
                analysis = self.analyze_current_code()
                
                # 2. 개선 제안 생성
                improvement = self.generate_improvement_suggestion(analysis)
                
                # 3. 개선 코드 구현
                implementation_result = self.implement_improvement(improvement)
                
                # 4. 성능 평가 및 적용
                performance_gain = self.evaluate_and_apply_improvement(implementation_result)
                
                # 5. 진화 기록
                metrics = EvolutionMetrics(
                    generation=self.evolution_generation,
                    intelligence_level=self.current_intelligence,
                    performance_gain=performance_gain,
                    complexity_score=self._calculate_complexity_score(analysis),
                    innovation_score=self.creativity_engine.innovation_multiplier * 10,
                    timestamp=datetime.now().isoformat()
                )
                
                self.database.save_evolution_step(metrics, analysis, improvement, str(implementation_result))
                
                # 6. 상태 업데이트
                self.current_intelligence += performance_gain
                self.evolution_generation += 1
                self.creativity_engine.advance_theme()
                
                logger.info(f"✅ Generation {self.evolution_generation-1} 완료 - 지능: {self.current_intelligence:.1f} (+{performance_gain:.1f})")
                
                # 7. 주기적 작업 실행
                self._execute_periodic_tasks()
                
                # 8. 진화 간격 조정 (성능에 따라)
                sleep_time = self._calculate_evolution_interval(performance_gain)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"자기진화 오류: {e}")
                time.sleep(10)  # 오류 시 짧은 대기
    
    def _execute_periodic_tasks(self) -> None:
        """주기적 작업 실행"""
        # 5세대마다 브랜치 생성 및 복구 시스템 실행
        if self.evolution_generation % 5 == 0:
            self._create_evolution_branch()
            self._auto_recovery_check()
        
        # 10세대마다 메모리 및 파일 관리
        if self.evolution_generation % 10 == 0:
            self._auto_memory_management()
            self._smart_file_cleanup()
        
        # 20세대마다 클라우드 백업
        if self.evolution_generation % 20 == 0:
            self._auto_cloud_backup()
    
    def _calculate_evolution_interval(self, performance_gain: float) -> int:
        """진화 간격 계산"""
        if performance_gain > 50:
            return 20  # 높은 성과 시 빠른 진화
        elif performance_gain > 20:
            return 30  # 보통 성과
        else:
            return 45  # 낮은 성과 시 더 긴 대기
    
    def analyze_current_code(self) -> str:
        """현재 코드 분석 - 개선된 창의성 및 중복 방지"""
        try:
            current_file = __file__
            with open(current_file, 'r', encoding='utf-8') as f:
                current_code = f.read()
            
            # 현재 진화 테마 선택
            current_theme = self.creativity_engine.get_current_theme()
            
            # 이전 분석 결과 확인하여 중복 방지
            previous_analyses = self._get_recent_analyses(3)
            
            # 창의성 유도 프롬프트
            random_aspects = random.sample([
                "code modularity", "error handling", "performance metrics", 
                "user experience", "scalability", "maintainability",
                "security features", "logging systems", "caching mechanisms",
                "parallel processing", "memory management", "API design"
            ], 3)
            
            analysis_prompt = f"""
IMPORTANT: Respond ONLY with JSON format. NO Korean text, NO explanations.

Current Evolution Focus: {current_theme}
Generation: {self.evolution_generation}
Innovation Level: {self.creativity_engine.innovation_multiplier:.1f}

Analyze this Python code with FRESH PERSPECTIVE on {current_theme}:

```python
{current_code[:3000]}  # First 3000 chars only
```

AVOID these previously analyzed aspects: {', '.join(previous_analyses)}

Focus on these NEW aspects: {', '.join(random_aspects)}

Generate INNOVATIVE analysis focusing on:
1. {current_theme.replace('_', ' ').title()} opportunities
2. Novel architectural patterns
3. Cutting-edge optimization techniques
4. Creative feature implementations
5. Unexplored improvement areas

Respond in JSON format ONLY:
{{
    "efficiency_score": {random.randint(60, 95)},
    "focus_theme": "{current_theme}",
    "innovative_features": ["{random_aspects[0]}", "{random_aspects[1]}", "{random_aspects[2]}"],
    "novel_approaches": ["approach1", "approach2", "approach3"],
    "creative_optimizations": ["optimization1", "optimization2"],
    "unexplored_areas": ["area1", "area2"],
    "innovation_potential": {random.randint(70, 100)}
}}
"""
            
            analysis_result = self.llm_manager.query_llm(analysis_prompt)
            
            # 분석 결과를 창의성 엔진에 기록
            self.creativity_engine.add_used_concept(current_theme)
            
            logger.info(f"🔍 창의적 분석 완료 (테마: {current_theme})")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"코드 분석 오류: {e}")
            return self._fallback_creative_analysis()
    
    def _get_recent_analyses(self, count: int = 3) -> List[str]:
        """최근 분석에서 사용된 개념들 조회"""
        try:
            cursor = self.database.connection.cursor()
            cursor.execute('''
                SELECT code_analysis FROM evolution_log 
                ORDER BY timestamp DESC LIMIT ?
            ''', (count,))
            
            results = cursor.fetchall()
            used_concepts = []
            
            for row in results:
                analysis = row[0]
                if analysis and 'focus_theme' in analysis:
                    try:
                        parsed = json.loads(analysis)
                        if 'focus_theme' in parsed:
                            used_concepts.append(parsed['focus_theme'])
                    except json.JSONDecodeError:
                        pass
            
            return used_concepts
            
        except Exception as e:
            logger.warning(f"이전 분석 조회 오류: {e}")
            return []
    
    def _fallback_creative_analysis(self) -> str:
        """창의적 폴백 분석"""
        theme = self.creativity_engine.get_current_theme()
        
        return f'''
        {{
            "efficiency_score": {random.randint(70, 90)},
            "focus_theme": "{theme}",
            "innovative_features": ["adaptive_learning", "smart_caching", "auto_optimization"],
            "novel_approaches": ["pattern_recognition", "predictive_analysis", "self_tuning"],
            "creative_optimizations": ["memory_pooling", "lazy_evaluation"],
            "unexplored_areas": ["quantum_algorithms", "neural_networks"],
            "innovation_potential": {random.randint(80, 95)}
        }}
        '''
    
    def _calculate_complexity_score(self, analysis: str) -> float:
        """복잡도 점수 계산"""
        try:
            parsed_analysis = json.loads(analysis)
            return parsed_analysis.get('innovation_potential', 75.0)
        except:
            return 75.0
    
    def generate_improvement_suggestion(self, analysis: str) -> str:
        """개선 제안 생성 - 혁신적이고 중복 없는 접근"""
        try:
            # 분석에서 정보 추출
            try:
                parsed_analysis = json.loads(analysis)
                focus_theme = parsed_analysis.get('focus_theme', 'general_improvement')
                innovative_features = parsed_analysis.get('innovative_features', [])
                innovation_potential = parsed_analysis.get('innovation_potential', 80)
            except:
                focus_theme = 'general_improvement'
                innovative_features = ['optimization', 'enhancement']
                innovation_potential = 75
            
            # 창의적 접근법 선택
            creative_approaches = [
                "design_patterns", "functional_programming", "object_oriented",
                "event_driven", "microservices", "reactive_programming",
                "machine_learning", "data_pipeline", "real_time_processing"
            ]
            
            unused_approaches = [
                approach for approach in creative_approaches 
                if not self.creativity_engine.is_concept_used(approach)
            ]
            
            selected_approach = random.choice(unused_approaches or creative_approaches)
            
            # 혁신적 프롬프트 생성
            improvement_prompt = f"""
IMPORTANT: Generate COMPLETELY NEW and INNOVATIVE Python code. NO repetition of existing patterns.

Evolution Theme: {focus_theme}
Approach: {selected_approach}
Innovation Level: {innovation_potential}%
Target Features: {', '.join(innovative_features)}

Create REVOLUTIONARY improvements focusing on {focus_theme}:

REQUIREMENTS:
1. Use {selected_approach} paradigm
2. Implement {innovative_features[0] if innovative_features else 'advanced_feature'}
3. Add cutting-edge optimizations
4. Include novel algorithms
5. Create unique class/function architecture

Generate Python code that includes:
- New class architecture for {focus_theme}
- Advanced {selected_approach} implementation
- Performance monitoring and metrics
- Self-adapting algorithms
- Creative problem-solving methods

Output format: ONLY executable Python code with innovative structure.
"""
            
            improvement = self.llm_manager.query_llm(improvement_prompt)
            
            # 중복 체크
            if self.creativity_engine.is_code_duplicate(improvement):
                logger.warning("⚠️ 중복 제안 감지 - 창의적 대안 생성")
                improvement = self._generate_creative_alternative(improvement, selected_approach)
            
            logger.info(f"💡 혁신적 개선 제안 생성 (접근법: {selected_approach})")
            
            return improvement
            
        except Exception as e:
            logger.error(f"개선 제안 생성 오류: {e}")
            return self._fallback_creative_suggestion()
    
    def _generate_creative_alternative(self, original_suggestion: str, approach: str) -> str:
        """중복 감지시 창의적 대안 생성"""
        alternative_approaches = [
            "quantum-inspired algorithms", "bio-mimetic patterns", 
            "fractal-based optimization", "chaos theory applications",
            "neural network architectures", "genetic algorithms"
        ]
        
        selected_approach = random.choice(alternative_approaches)
        
        return f"""
# Creative Alternative Implementation using {selected_approach}
# Generation: {self.evolution_generation}
# Approach: {approach} + {selected_approach}

{original_suggestion}

# Additional innovative features:
class CreativeAlternative_{self.evolution_generation}:
    def __init__(self):
        self.approach = "{selected_approach}"
        self.innovation_level = {random.randint(80, 100)}
        self.generation_id = {self.evolution_generation}
        
    def implement_unique_solution(self):
        '''Revolutionary {selected_approach} implementation'''
        return self.apply_creative_patterns()
        
    def apply_creative_patterns(self):
        '''Apply cutting-edge patterns'''
        # Implement {selected_approach} logic here
        pass
"""
    
    def _fallback_creative_suggestion(self) -> str:
        """창의적 폴백 제안"""
        approaches = [
            "machine_learning_optimizer", "adaptive_caching_system", 
            "predictive_analytics", "smart_resource_manager",
            "self_tuning_algorithm", "pattern_recognition_engine"
        ]
        
        selected = random.choice(approaches)
        
        return f"""
# Revolutionary {selected} Implementation - Generation {self.evolution_generation}
class {selected.title().replace('_', '')}:
    '''High-performance {selected} for evolution system'''
    
    def __init__(self):
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.85
        self.performance_history = []
        self.generation_id = {self.evolution_generation}
        
    def optimize_performance(self, metrics: Dict[str, float]) -> float:
        '''Advanced optimization logic'''
        improvement_factor = self.calculate_improvement(metrics)
        return self.apply_optimizations(improvement_factor)
        
    def calculate_improvement(self, metrics: Dict[str, float]) -> float:
        '''Innovative calculation method'''
        if not metrics:
            return 0.0
        return sum(metrics.values()) / len(metrics) * self.learning_rate
        
    def apply_optimizations(self, factor: float) -> float:
        '''Revolutionary optimization application'''
        optimized_factor = factor * self.adaptation_threshold
        self.performance_history.append(optimized_factor)
        return optimized_factor
"""
    
    def implement_improvement(self, improvement_suggestion: str) -> Dict[str, Any]:
        """개선 사항 구현 - 중복 검사 강화"""
        try:
            # 중복 검사
            if self.creativity_engine.is_code_duplicate(improvement_suggestion):
                logger.warning("⚠️ 중복 제안 감지 - 창의적 대안 생성")
                improvement_suggestion = self._generate_creative_alternative(
                    improvement_suggestion, 
                    "alternative_approach"
                )
            
            # 개선된 코드 파일 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            improved_filename = f"evolved_ai_gen_{self.evolution_generation}_{timestamp}.py"
            
            # 코드 품질 향상
            enhanced_code = self._enhance_code_quality(improvement_suggestion)
            
            # 파일 저장
            with open(improved_filename, 'w', encoding='utf-8') as f:
                f.write(enhanced_code)
            
            # 코드 버전 DB에 저장
            self._save_code_version(improved_filename, enhanced_code, improvement_suggestion)
            
            # 개선 이력에 추가
            self.improvement_history.append({
                'filename': improved_filename,
                'timestamp': time.time(),
                'suggestion': improvement_suggestion[:100] + '...' if len(improvement_suggestion) > 100 else improvement_suggestion,
                'uniqueness_score': self._calculate_uniqueness_score(enhanced_code)
            })
            
            logger.info(f"🛠️ 혁신적 코드 구현 완료: {improved_filename}")
            
            return {
                'filename': improved_filename,
                'code': enhanced_code,
                'status': 'success',
                'uniqueness_verified': True,
                'file_size': len(enhanced_code)
            }
            
        except Exception as e:
            logger.error(f"개선 구현 오류: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _enhance_code_quality(self, code: str) -> str:
        """코드 품질 향상"""
        try:
            # 헤더 추가
            header = f'''#!/usr/bin/env python3
"""
🧠 자기진화 AI - Generation {self.evolution_generation}
생성 시간: {datetime.now().isoformat()}
테마: {self.creativity_engine.get_current_theme()}
혁신 수준: {self.creativity_engine.innovation_multiplier:.2f}
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# 로깅 설정
logger = logging.getLogger(__name__)

'''
            
            # 코드 정리 및 포맷팅
            lines = code.splitlines()
            cleaned_lines = []
            
            for line in lines:
                # 불필요한 공백 제거
                cleaned_line = line.rstrip()
                
                # 빈 줄이 너무 많으면 제거
                if cleaned_line or len(cleaned_lines) == 0 or cleaned_lines[-1]:
                    cleaned_lines.append(cleaned_line)
            
            # 최종 코드 조합
            enhanced_code = header + '\n'.join(cleaned_lines)
            
            # 마지막에 메인 실행 부분 추가
            if 'if __name__ == "__main__"' not in enhanced_code:
                enhanced_code += '''

if __name__ == "__main__":
    try:
        # 생성된 코드 실행
        logger.info(f"🚀 Generation {generation_id} 코드 실행 시작")
        # 여기에 실행 로직 추가
    except Exception as e:
        logger.error(f"실행 오류: {e}")
'''
            
            return enhanced_code
            
        except Exception as e:
            logger.warning(f"코드 품질 향상 오류: {e}")
            return code
    
    def _save_code_version(self, filename: str, code: str, description: str) -> None:
        """코드 버전 저장"""
        try:
            cursor = self.database.connection.cursor()
            cursor.execute('''
                INSERT INTO code_versions 
                (timestamp, generation, filename, code_content, improvement_description, 
                 intelligence_score, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.evolution_generation,
                filename,
                code[:10000],  # 처음 10KB만 저장
                description[:1000],  # 처음 1KB만 저장
                self.current_intelligence,
                len(code)
            ))
            
            self.database.connection.commit()
            
        except Exception as e:
            logger.error(f"코드 버전 저장 오류: {e}")
    
    def _calculate_uniqueness_score(self, code: str) -> float:
        """고유성 점수 계산"""
        try:
            lines = code.splitlines()
            unique_patterns = 0
            
            patterns = [
                'class ', 'def ', 'async ', 'await ', '@', 'lambda ',
                'yield ', 'with ', 'try:', 'except:', 'finally:',
                'import ', 'from ', 'if __name__'
            ]
            
            for pattern in patterns:
                if pattern in code:
                    unique_patterns += 1
            
            # 길이와 복잡도 고려
            complexity_score = len(lines) + len(set(lines))
            uniqueness = min(100, (unique_patterns * 8) + (complexity_score // 15))
            
            return uniqueness
            
        except:
            return 50.0
    
    def evaluate_and_apply_improvement(self, implementation_result: Dict[str, Any]) -> float:
        """개선 사항 평가 및 적용"""
        try:
            if implementation_result.get('status') != 'success':
                return 0.0

            filename = implementation_result['filename']
            
            # 파일 존재 확인
            if not os.path.exists(filename):
                logger.warning(f"⚠️ 파일이 존재하지 않음: {filename}")
                return 0.0
            
            # 고유성 점수 계산
            with open(filename, 'r', encoding='utf-8') as f:
                new_code = f.read()
            
            uniqueness_score = self._calculate_uniqueness_score(new_code)
            if uniqueness_score < 40:
                logger.warning(f"⚠️ 코드 고유성 부족: {uniqueness_score}점")
                return max(3.0, uniqueness_score / 15)
            
            # 문법 검사
            if not self._check_syntax(filename):
                logger.warning(f"⚠️ 문법 오류: {filename}")
                return 5.0
            
            # 다양한 품질 메트릭 계산
            quality_metrics = self._calculate_comprehensive_quality(new_code)
            
            # 가중 평균으로 최종 점수 계산
            weights = {
                'uniqueness': 0.30,
                'syntax_quality': 0.25,
                'complexity': 0.20,
                'innovation': 0.15,
                'performance': 0.10
            }
            
            total_score = (
                uniqueness_score * weights['uniqueness'] +
                quality_metrics['syntax_quality'] * weights['syntax_quality'] +
                quality_metrics['complexity'] * weights['complexity'] +
                self.creativity_engine.innovation_multiplier * 20 * weights['innovation'] +
                quality_metrics['performance'] * weights['performance']
            )
            
            # 혁신 보너스
            if uniqueness_score > 80 and quality_metrics['complexity'] > 70:
                total_score *= 1.15
                logger.info("🚀 혁신 보너스 적용!")
            
            # 연속 고유성 보너스
            if self._check_consecutive_uniqueness():
                total_score *= 1.08
                logger.info("💎 연속 고유성 보너스!")
            
            final_score = min(total_score, 100.0)
            
            logger.info(f"📊 종합 평가: 고유성({uniqueness_score:.1f}) 총점({final_score:.1f})")
            
            return final_score
            
        except Exception as e:
            logger.error(f"성능 평가 오류: {e}")
            return 1.0
    
    def _check_syntax(self, filename: str) -> bool:
        """Python 문법 검사"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()
            
            ast.parse(code)
            return True
            
        except SyntaxError as e:
            logger.error(f"문법 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"파일 읽기 오류: {e}")
            return False
    
    def _calculate_comprehensive_quality(self, code: str) -> Dict[str, float]:
        """종합 품질 메트릭 계산"""
        try:
            lines = code.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 문법 품질
            syntax_quality = 100.0
            if 'eval(' in code:
                syntax_quality -= 20
            if 'exec(' in code:
                syntax_quality -= 20
            if 'global ' in code:
                syntax_quality -= 10
            
            # 복잡도
            complexity_indicators = [
                'class ', 'def ', 'if ', 'for ', 'while ', 'try:', 
                'with ', 'lambda ', 'async ', 'await '
            ]
            complexity_score = min(100, sum(code.count(indicator) * 5 for indicator in complexity_indicators))
            
            # 성능 지표
            performance_patterns = ['async ', 'await ', 'threading', 'multiprocessing', 'cache']
            performance_score = min(100, sum(10 for pattern in performance_patterns if pattern in code))
            
            return {
                'syntax_quality': max(0, syntax_quality),
                'complexity': max(20, complexity_score),
                'performance': max(30, performance_score)
            }
            
        except Exception as e:
            logger.warning(f"품질 메트릭 계산 오류: {e}")
            return {'syntax_quality': 50, 'complexity': 50, 'performance': 50}
    
    def _check_consecutive_uniqueness(self) -> bool:
        """연속 고유성 체크"""
        try:
            if len(self.improvement_history) < 3:
                return False
            
            recent_scores = [
                item.get('uniqueness_score', 0) 
                for item in self.improvement_history[-3:]
            ]
            
            return all(score > 60 for score in recent_scores)
            
        except:
            return False
    
    # 주기적 작업 메서드들
    def _create_evolution_branch(self) -> None:
        """진화 브랜치 생성"""
        try:
            branch_name = f"evolution-gen-{self.evolution_generation}"
            
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 진화 브랜치 생성: {branch_name}")
                
                # 현재 변경사항 커밋
                subprocess.run(['git', 'add', '.'], timeout=30)
                subprocess.run([
                    'git', 'commit', '-m', 
                    f'Generation {self.evolution_generation} evolution'
                ], timeout=30)
            
        except Exception as e:
            logger.warning(f"브랜치 생성 오류: {e}")
    
    def _auto_recovery_check(self) -> None:
        """자동 복구 체크"""
        try:
            recent_performance = self.database.get_recent_performance(5)
            
            if len(recent_performance) >= 3:
                recent_scores = [p['performance_score'] for p in recent_performance]
                
                if len(recent_scores) >= 2:
                    latest_avg = sum(recent_scores[:2]) / 2
                    previous_avg = sum(recent_scores[2:]) / max(1, len(recent_scores) - 2)
                    
                    # 성능이 30% 이상 저하된 경우
                    if latest_avg < previous_avg * 0.7:
                        logger.warning("⚠️ 성능 저하 감지 - 자동 복구 필요")
                        # 여기에 복구 로직 구현
            
        except Exception as e:
            logger.warning(f"자동 복구 체크 오류: {e}")
    
    def _auto_memory_management(self) -> None:
        """자동 메모리 관리"""
        try:
            # 가비지 컬렉션 실행
            collected = gc.collect()
            
            # 오래된 히스토리 정리
            if len(self.improvement_history) > 50:
                self.improvement_history = self.improvement_history[-30:]
            
            if len(self.code_analysis_history) > 50:
                self.code_analysis_history = self.code_analysis_history[-30:]
            
            logger.info(f"💾 메모리 관리 완료: {collected}개 객체 정리")
            
        except Exception as e:
            logger.warning(f"메모리 관리 오류: {e}")
    
    def _smart_file_cleanup(self) -> None:
        """스마트 파일 정리"""
        try:
            # 오래된 진화 파일 찾기
            evolution_files = [
                f for f in os.listdir('.') 
                if f.startswith('evolved_ai_gen_') and f.endswith('.py')
            ]
            
            # 최신 20개만 유지
            if len(evolution_files) > 20:
                evolution_files.sort()
                old_files = evolution_files[:-20]
                
                for old_file in old_files:
                    try:
                        os.remove(old_file)
                    except:
                        pass
                
                logger.info(f"🧹 파일 정리: {len(old_files)}개 오래된 파일 제거")
            
        except Exception as e:
            logger.warning(f"파일 정리 오류: {e}")
    
    def _auto_cloud_backup(self) -> None:
        """자동 클라우드 백업"""
        try:
            # 최근 파일들을 압축
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = self.cloud_upload_dir / f"evolution_backup_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 최근 진화 파일들 추가
                evolution_files = [
                    f for f in os.listdir('.') 
                    if f.startswith('evolved_ai_gen_') and f.endswith('.py')
                ][-10:]  # 최근 10개만
                
                for file in evolution_files:
                    zipf.write(file)
            
            logger.info(f"☁️ 클라우드 백업 완료: {zip_filename}")
            
        except Exception as e:
            logger.warning(f"클라우드 백업 오류: {e}")
    
    def get_evolution_stats(self) -> Dict[str, Any]:
        """진화 통계 조회"""
        return {
            'generation': self.evolution_generation,
            'intelligence': self.current_intelligence,
            'evolution_active': self.self_improvement_active,
            'current_llm': self.llm_manager.get_current_llm().name,
            'total_improvements': len(self.improvement_history),
            'current_theme': self.creativity_engine.get_current_theme(),
            'innovation_multiplier': self.creativity_engine.innovation_multiplier,
            'system_status': 'active' if self.self_improvement_active else 'inactive'
        }
    
    def stop_evolution(self) -> None:
        """진화 시스템 중지"""
        self.self_improvement_active = False
        self.database.close()
        logger.info("🛑 자기진화 시스템 중지")

def main():
    """메인 실행 함수"""
    try:
        # 자기진화 AI 시작
        ai = SelfEvolvingAI()
        
        print("🧠 자기진화 AI 시스템 - 품질 개선 버전")
        print("=" * 50)
        print(f"시작 시간: {datetime.now().isoformat()}")
        print(f"초기 지능 레벨: {ai.current_intelligence}")
        print("시스템이 백그라운드에서 자동으로 진화합니다...")
        
        # 무한 실행 (Ctrl+C로 종료)
        try:
            while True:
                time.sleep(30)  # 30초마다 상태 출력
                stats = ai.get_evolution_stats()
                print(f"\n📊 Generation {stats['generation']} - 지능: {stats['intelligence']:.1f}")
                print(f"테마: {stats['current_theme']} | 혁신도: {stats['innovation_multiplier']:.2f}")
                
        except KeyboardInterrupt:
            print("\n\n🛑 사용자에 의한 시스템 중지")
            ai.stop_evolution()
            
    except Exception as e:
        logger.error(f"메인 실행 오류: {e}")

if __name__ == "__main__":
    main()
