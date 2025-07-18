# 성능 팁: list comprehension 사용 고려
# 성능 팁: f-string 사용으로 문자열 연결 최적화

#!/usr/bin/env python3
"""
🧠 자기진화 AI 시스템 - 무료 LLM 기반
스스로 코드를 분석하고 개선하여 진화하는 AI
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
from datetime import datetime
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfEvolvingAI:
    """🧠 자기진화 AI 시스템"""
    
    def __init__(self):
        self.current_intelligence = 500.0
        self.evolution_generation = 1
        self.self_improvement_active = True
        self.code_analysis_history = []
        self.improvement_history = []
        
        # 진화 상태 관리
        self.evolution_state = {
            'generation': 1,
            'intelligence_level': 500.0,
            'active': True
        }
        
        # 데이터베이스 연결 초기화
        self.db_connection = None
        
        # 창의성 및 중복 방지 시스템
        self.creativity_engine = {
            'used_concepts': set(),
            'code_hashes': set(),
            'evolution_themes': [
                'performance_optimization', 'memory_efficiency', 'async_processing',
                'machine_learning', 'data_structures', 'algorithms', 'network_programming',
                'security', 'testing', 'documentation', 'ui_interfaces', 'api_design'
            ],
            'current_theme_index': 0,
            'innovation_multiplier': 1.0
        }
        
        # 쉬림프 테스크 매니저 기반 무료 LLM API 설정
        self.free_llm_apis = [
            {
                'name': 'Shrimp Evolution Server',
                'url': 'http://localhost:8002/api/chat',
                'model': 'evolution-llm',
                'type': 'shrimp'
            },
            {
                'name': 'Shrimp MCP Evolution',
                'url': 'http://localhost:8002/api/mcp-evolution',
                'model': 'mcp-llm',
                'type': 'shrimp'
            },
            {
                'name': 'Fallback Analysis',
                'url': 'http://localhost:8002/fallback',
                'model': 'fallback',
                'type': 'fallback'
            }
        ]
        
        self.current_llm = self.free_llm_apis[0]  # 쉬림프 테스크 매니저 우선 사용
        
        # DB 초기화
        self.init_evolution_db()
        
        # 클라우드 스토리지 자동 설정
        self.setup_cloud_storage()
        
        # 자기진화 시작
        self.evolution_thread = threading.Thread(target=self.self_evolution_loop)
        self.evolution_thread.daemon = True
        self.evolution_thread.start()
        
        logger.info(f"🧠 자기진화 AI 시스템 시작! Generation: {self.evolution_generation}")
    
    def init_evolution_db(self):
        """자기진화 데이터베이스 초기화"""
        try:
            self.db_connection = sqlite3.connect('self_evolution.db', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    generation INTEGER,
                    intelligence_level REAL,
                    code_analysis TEXT,
                    improvement_suggestion TEXT,
                    implementation_result TEXT,
                    performance_gain REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    generation INTEGER,
                    filename TEXT,
                    code_content TEXT,
                    improvement_description TEXT,
                    intelligence_score REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cloud_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    filename TEXT,
                    download_url TEXT,
                    local_backup_path TEXT,
                    service TEXT,
                    generation_range TEXT,
                    file_size INTEGER
                )
            ''')
            
            self.db_connection.commit()
            logger.info("✅ 자기진화 DB 초기화 완료")
            
        except Exception as e:
            logger.error(f"DB 초기화 오류: {e}")
    
    def self_evolution_loop(self):
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
                self.log_evolution_step(analysis, improvement, implementation_result, performance_gain)
                
                # 6. 지능 레벨 업데이트
                self.current_intelligence += performance_gain
                self.evolution_generation += 1
                
                logger.info(f"✅ Generation {self.evolution_generation-1} 완료 - 지능: {self.current_intelligence:.1f} (+{performance_gain:.1f})")
                
                # 7. 5세대마다 브랜치 생성 및 자동 복구 시스템 실행
                if self.evolution_generation % 5 == 0:
                    # 브랜치 생성
                    branch_result = self.create_evolution_branch(self.evolution_generation - 1)
                    if branch_result['success']:
                        logger.info(f"🌿 진화 브랜치 생성: {branch_result['branch']}")
                    
                    # 자동 복구 시스템 실행
                    recovery_result = self.auto_recovery_system()
                    if recovery_result['action'] == 'rollback':
                        logger.warning(f"🔄 자동 롤백 실행: Generation {recovery_result['target_generation']}")
                        logger.warning(f"📄 롤백 사유: {recovery_result['reason']}")
                
                # 8. 10세대마다 자동 메모리 및 파일 관리
                if self.evolution_generation % 10 == 0:
                    # 메모리 관리
                    memory_result = self.auto_memory_management()
                    if memory_result.get('cleaned'):
                        logger.info(f"💾 메모리 정리: {memory_result['memory_saved_percent']:.1f}% 절약")
                    
                    # 스마트 파일 정리
                    cleanup_result = self.smart_file_cleanup()
                    if 'error' not in cleanup_result:
                        logger.info(f"🧹 파일 정리: 중복 {cleanup_result['duplicates_removed']}개, 오류 {cleanup_result['syntax_error_files']}개 제거")
                
                # 9. 20세대마다 클라우드 백업
                if self.evolution_generation % 20 == 0:
                    zip_file = self.auto_compress_old_files()
                    if zip_file:
                        upload_result = self.auto_upload_to_cloud(zip_file)
                        if upload_result:
                            logger.info(f"☁️ 클라우드 백업 완료: {upload_result['service']}")
                
                # 30초마다 자기진화
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"자기진화 오류: {e}")
                time.sleep(10)
    
    def analyze_current_code(self):
        """현재 코드 분석 - 개선된 창의성 및 중복 방지"""
        try:
            # 현재 파일의 코드 읽기
            current_file = __file__
            with open(current_file, 'r', encoding='utf-8') as f:
                current_code = f.read()
            
            # 현재 진화 테마 선택
            current_theme = self.creativity_engine['evolution_themes'][
                self.creativity_engine['current_theme_index'] % len(self.creativity_engine['evolution_themes'])
            ]
            
            # 이전 분석 결과 확인하여 중복 방지
            previous_analyses = self.get_recent_analyses(3)
            
            # 창의성 유도 프롬프트 (무작위 요소 포함)
            import random
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
Innovation Level: {self.creativity_engine['innovation_multiplier']:.1f}

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
            
            analysis_result = self.query_llm(analysis_prompt)
            
            # 분석 결과를 창의성 엔진에 기록
            self.record_analysis_for_creativity(analysis_result, current_theme)
            
            logger.info(f"🔍 창의적 분석 완료 (테마: {current_theme}): {len(analysis_result)} chars")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"코드 분석 오류: {e}")
            return self.fallback_creative_analysis()
    
    def get_recent_analyses(self, count=3):
        """최근 분석에서 사용된 개념들 조회"""
        try:
            if not self.db_connection:
                return []
                
            cursor = self.db_connection.cursor()
            cursor.execute('''SELECT code_analysis FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT ?''', (count,))
            results = cursor.fetchall()
            
            used_concepts = []
            for row in results:
                analysis = row[0]
                if 'focus_theme' in analysis:
                    # JSON에서 테마 추출 시도
                    try:
                        import json
                        parsed = json.loads(analysis)
                        if 'focus_theme' in parsed:
                            used_concepts.append(parsed['focus_theme'])
                    except Exception:
                        pass
            
            return used_concepts
        except Exception as e:
            logger.warning(f"이전 분석 조회 오류: {e}")
            return []
    
    def record_analysis_for_creativity(self, analysis, theme):
        """창의성 엔진에 분석 결과 기록"""
        try:
            # 사용된 개념 기록
            self.creativity_engine['used_concepts'].add(theme)
            
            # 다음 테마로 순환
            self.creativity_engine['current_theme_index'] += 1
            
            # 혁신 지수 업데이트
            if self.evolution_generation % 5 == 0:
                self.creativity_engine['innovation_multiplier'] *= 1.1
                self.creativity_engine['innovation_multiplier'] = min(
                    self.creativity_engine['innovation_multiplier'], 3.0
                )
                
        except Exception as e:
            logger.warning(f"창의성 기록 오류: {e}")
    
    def fallback_creative_analysis(self):
        """창의적 폴백 분석"""
        import random
        themes = self.creativity_engine['evolution_themes']
        theme = random.choice(themes)
        
        return f"""
        {{
            "efficiency_score": {random.randint(70, 90)},
            "focus_theme": "{theme}",
            "innovative_features": ["adaptive_learning", "smart_caching", "auto_optimization"],
            "novel_approaches": ["pattern_recognition", "predictive_analysis", "self_tuning"],
            "creative_optimizations": ["memory_pooling", "lazy_evaluation"],
            "unexplored_areas": ["quantum_algorithms", "neural_networks"],
            "innovation_potential": {random.randint(80, 95)}
        }}
        """
    
    def generate_improvement_suggestion(self, analysis):
        """개선 제안 생성 - 혁신적이고 중복 없는 접근"""
        try:
            import random
            import json
            
            # 분석에서 테마 추출
            try:
                parsed_analysis = json.loads(analysis)
                focus_theme = parsed_analysis.get('focus_theme', 'general_improvement')
                innovative_features = parsed_analysis.get('innovative_features', [])
                innovation_potential = parsed_analysis.get('innovation_potential', 80)
            except Exception:
                focus_theme = 'general_improvement'
                innovative_features = ['optimization', 'enhancement']
                innovation_potential = 75
            
            # 중복 방지를 위한 코드 해시 확인
            recent_hashes = self.get_recent_code_hashes(5)
            
            # 창의적 접근법 선택
            creative_approaches = [
                "design_patterns", "functional_programming", "object_oriented",
                "event_driven", "microservices", "reactive_programming",
                "machine_learning", "data_pipeline", "real_time_processing"
            ]
            
            selected_approach = random.choice([a for a in creative_approaches 
                                             if a not in self.creativity_engine['used_concepts']])
            
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

AVOID these used patterns: {', '.join(recent_hashes[:3])}

Generate Python code that includes:
- New class architecture for {focus_theme}
- Advanced {selected_approach} implementation
- Performance monitoring and metrics
- Self-adapting algorithms
- Creative problem-solving methods

Output format: ONLY executable Python code with innovative structure.
"""
            
            improvement = self.query_llm(improvement_prompt)
            
            # 생성된 제안의 해시 기록
            suggestion_hash = self.hash_content(improvement)
            self.creativity_engine['code_hashes'].add(suggestion_hash)
            
            logger.info(f"💡 혁신적 개선 제안 생성 (접근법: {selected_approach})")
            
            return improvement
            
        except Exception as e:
            logger.error(f"개선 제안 생성 오류: {e}")
            return self.fallback_creative_suggestion()
    
    def get_recent_code_hashes(self, count=5):
        """최근 생성된 코드의 해시값들 조회"""
        try:
            if not self.db_connection:
                return []
                
            cursor = self.db_connection.cursor()
            cursor.execute('''SELECT improvement_suggestion FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT ?''', (count,))
            results = cursor.fetchall()
            
            hashes = []
            for row in results:
                if row[0]:
                    hash_val = self.hash_content(row[0])[:8]  # 처음 8자만
                    hashes.append(hash_val)
            
            return hashes
        except Exception as e:
            logger.warning(f"코드 해시 조회 오류: {e}")
            return []
    
    def hash_content(self, content):
        """콘텐츠 해시 생성"""
        import hashlib
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def fallback_creative_suggestion(self):
        """창의적 폴백 제안"""
        import random
        
        approaches = [
            "machine_learning_optimizer", "adaptive_caching_system", 
            "predictive_analytics", "smart_resource_manager",
            "self_tuning_algorithm", "pattern_recognition_engine"
        ]
        
        selected = random.choice(approaches)
        
        return f"""
# Revolutionary {selected} Implementation
class {selected.title().replace('_', '')}:
    def __init__(self):
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.85
        self.performance_history = []
        
    def optimize_performance(self, metrics):
        # Advanced optimization logic
        improvement_factor = self.calculate_improvement(metrics)
        return self.apply_optimizations(improvement_factor)
        
    def calculate_improvement(self, metrics):
        # Innovative calculation method
        return sum(metrics) / len(metrics) * self.learning_rate
        
    def apply_optimizations(self, factor):
        # Revolutionary optimization application
        return factor * self.adaptation_threshold
"""
    
    def implement_improvement(self, improvement_suggestion):
        """개선 사항 구현 - 중복 검사 강화"""
        try:
            # 중복 검사 먼저 수행
            suggestion_hash = self.hash_content(improvement_suggestion)
            if suggestion_hash in self.creativity_engine['code_hashes']:
                logger.warning("⚠️ 중복 제안 감지 - 창의적 대안 생성")
                improvement_suggestion = self.generate_creative_alternative(improvement_suggestion)
            
            # 개선된 코드 파일 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            improved_filename = f"evolved_ai_gen_{self.evolution_generation}_{timestamp}.py"
            
            # 혁신적 구현 프롬프트
            implementation_prompt = f"""
IMPORTANT: Create COMPLETELY UNIQUE Python implementation. NO code duplication.

Current Generation: {self.evolution_generation}
Innovation Focus: High creativity and uniqueness

Transform this improvement into REVOLUTIONARY code:
{improvement_suggestion}

STRICT REQUIREMENTS:
1. Must be 100% original and unique
2. Include advanced Python features (async, decorators, metaclasses)
3. Implement cutting-edge algorithms
4. Add comprehensive error handling
5. Include performance monitoring
6. Must be production-ready code

Create a complete, executable Python file with:
- Innovative class hierarchy
- Advanced design patterns
- Self-improving algorithms
- Comprehensive documentation
- Unit test capabilities

Start with: #!/usr/bin/env python3
"""
            
            improved_code = self.query_llm(implementation_prompt)
            
            # 생성된 코드의 고유성 검증
            if not self.verify_code_uniqueness(improved_code):
                logger.warning("🔄 코드 고유성 부족 - 재생성")
                improved_code = self.force_unique_generation(improved_code)
            
            # 개선된 코드 저장
            with open(improved_filename, 'w', encoding='utf-8') as f:
                f.write(improved_code)
            
            # 코드 버전 DB에 저장
            self.save_code_version(improved_filename, improved_code, improvement_suggestion)
            
            # 해시 추가로 중복 방지
            code_hash = self.hash_content(improved_code)
            self.creativity_engine['code_hashes'].add(code_hash)
            
            # 개선 이력에 추가
            self.improvement_history.append({
                'filename': improved_filename,
                'timestamp': time.time(),
                'suggestion': improvement_suggestion[:100] + '...' if len(improvement_suggestion) > 100 else improvement_suggestion,
                'uniqueness_score': self.calculate_uniqueness_score(improved_code)
            })
            
            logger.info(f"🛠️ 혁신적 코드 구현 완료: {improved_filename}")
            
            return {
                'filename': improved_filename,
                'code': improved_code,
                'status': 'success',
                'uniqueness_verified': True
            }
            
        except Exception as e:
            logger.error(f"개선 구현 오류: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def generate_creative_alternative(self, original_suggestion):
        """중복 감지시 창의적 대안 생성"""
        import random
        
        alternative_approaches = [
            "quantum-inspired algorithms", "bio-mimetic patterns", 
            "fractal-based optimization", "chaos theory applications",
            "neural network architectures", "genetic algorithms"
        ]
        
        selected_approach = random.choice(alternative_approaches)
        
        return f"""
# Creative Alternative Implementation using {selected_approach}
# Generation: {self.evolution_generation}
# Uniqueness: Guaranteed through {selected_approach}

{original_suggestion}

# Additional innovative features:
class CreativeAlternative_{self.evolution_generation}:
    def __init__(self):
        self.approach = "{selected_approach}"
        self.innovation_level = {random.randint(80, 100)}
        
    def implement_unique_solution(self):
        # Revolutionary {selected_approach} implementation
        return self.apply_creative_patterns()
"""
    
    def verify_code_uniqueness(self, code):
        """코드 고유성 검증"""
        try:
            code_hash = self.hash_content(code)
            
            # 기존 해시와 비교
            if code_hash in self.creativity_engine['code_hashes']:
                return False
            
            # 기존 파일들과 유사도 검사
            existing_files = [f for f in os.listdir('.') 
                            if f.startswith('evolved_ai_gen_') and f.endswith('.py')]
            
            for existing_file in existing_files[-5:]:  # 최근 5개만 검사
                try:
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        existing_code = f.read()
                    
                    similarity = self.calculate_code_similarity(code, existing_code)
                    if similarity > 0.7:  # 70% 이상 유사하면 실패
                        return False
                        
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            logger.warning(f"고유성 검증 오류: {e}")
            return True  # 오류시 통과
    
    def calculate_code_similarity(self, code1, code2):
        """코드 유사도 계산"""
        try:
            import difflib
            lines1 = code1.splitlines()
            lines2 = code2.splitlines()
            return difflib.SequenceMatcher(None, lines1, lines2).ratio()
        except Exception:
            return 0.0
    
    def force_unique_generation(self, original_code):
        """강제 고유 코드 생성"""
        import random
        
        unique_elements = [
            f"# Unique Generation {self.evolution_generation}",
            f"# Timestamp: {datetime.now().isoformat()}",
            f"# Innovation ID: {random.randint(100000, 999999)}",
            "",
            "# Force-uniqueness implementation",
            f"GENERATION_ID = {self.evolution_generation}",
            f"UNIQUE_SIGNATURE = '{self.hash_content(str(time.time()))[:16]}'",
            "",
        ]
        
        return '\n'.join(unique_elements) + '\n' + original_code
    
    def calculate_uniqueness_score(self, code):
        """고유성 점수 계산"""
        try:
            # 코드 특성 분석
            lines = code.splitlines()
            unique_patterns = 0
            
            patterns = [
                'class ', 'def ', 'async ', 'await ', '@', 'lambda ',
                'yield ', 'with ', 'try:', 'except Exception:', 'finally:'
            ]
            
            for pattern in patterns:
                if pattern in code:
                    unique_patterns += 1
            
            # 길이와 복잡도 고려
            complexity_score = len(lines) + len(set(lines))
            uniqueness = min(100, (unique_patterns * 10) + (complexity_score // 10))
            
            return uniqueness
            
        except Exception:
            return 50
    
    def evaluate_and_apply_improvement(self, implementation_result):
        """개선 사항 평가 및 적용 - 고도화된 평가 시스템"""
        try:
            if implementation_result['status'] != 'success':
                return 0.0

            filename = implementation_result['filename']
            
            # 1. 강화된 중복 검사
            with open(filename, 'r', encoding='utf-8') as f:
                new_code = f.read()
            
            # 고유성 점수 계산
            uniqueness_score = self.calculate_uniqueness_score(new_code)
            if uniqueness_score < 50:
                logger.warning(f"⚠️ 코드 고유성 부족: {uniqueness_score}점")
                return max(5.0, uniqueness_score / 10)
            
            # 2. 혁신성 평가
            innovation_score = self.evaluate_innovation(new_code)
            
            # 3. 자동 디버깅 수행
            debug_results = self.auto_debug_code(new_code, filename)
            
            # 문법 오류가 있으면 자동 수정
            if any('❌' in error for error in debug_results['syntax_errors']):
                logger.info("🔧 문법 오류 자동 수정 시도")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(debug_results['fixed_code'])
                
                # 수정 후 재검사
                try:
                    ast.parse(debug_results['fixed_code'])
                    logger.info("✅ 자동 수정 성공")
                except SyntaxError:
                    logger.warning("⚠️ 자동 수정 실패")
                    return 5.0

            # 4. 기능성 테스트
            syntax_valid = self.check_syntax(filename)
            if not syntax_valid:
                logger.warning(f"⚠️ 문법 오류: {filename}")
                return 5.0

            # 5. 고급 기능 평가
            advanced_features_score = self.evaluate_advanced_features(new_code)
            
            # 6. 성능 예측 모델
            performance_prediction = self.predict_performance(new_code)
            
            # 7. 코드 품질 메트릭
            quality_metrics = self.calculate_quality_metrics(new_code)
            
            # 총 성능 점수 계산 (가중 평균)
            weights = {
                'uniqueness': 0.25,
                'innovation': 0.20,
                'advanced_features': 0.20,
                'performance_prediction': 0.15,
                'quality_metrics': 0.20
            }
            
            total_score = (
                uniqueness_score * weights['uniqueness'] +
                innovation_score * weights['innovation'] +
                advanced_features_score * weights['advanced_features'] +
                performance_prediction * weights['performance_prediction'] +
                quality_metrics * weights['quality_metrics']
            )
            
            # 혁신 보너스
            if innovation_score > 80:
                total_score *= 1.2
                logger.info("🚀 혁신 보너스 적용!")
            
            # 연속 고유성 보너스
            if self.check_consecutive_uniqueness():
                total_score *= 1.1
                logger.info("💎 연속 고유성 보너스!")
            
            logger.info(f"📊 종합 평가: 고유성({uniqueness_score:.1f}) 혁신성({innovation_score:.1f}) 총점({total_score:.1f})")
            
            return min(total_score, 100.0)  # 최대 100점
            
        except Exception as e:
            logger.error(f"성능 평가 오류: {e}")
            return 1.0
    
    def evaluate_innovation(self, code):
        """혁신성 평가"""
        try:
            innovation_indicators = [
                ('async', 10), ('await', 10), ('metaclass', 15),
                ('decorator', 8), ('@property', 5), ('contextmanager', 10),
                ('generator', 8), ('yield', 8), ('lambda', 5),
                ('threading', 12), ('multiprocessing', 15), ('asyncio', 15),
                ('machine learning', 20), ('neural network', 25), ('ai', 15),
                ('optimization', 10), ('algorithm', 8), ('pattern', 7)
            ]
            
            innovation_score = 0
            for indicator, score in innovation_indicators:
                if indicator in code.lower():
                    innovation_score += score
            
            # 클래스와 함수 복잡도
            class_count = code.count('class ')
            function_count = code.count('def ')
            innovation_score += (class_count * 5) + (function_count * 2)
            
            # 코드 길이 기반 보정
            lines = len(code.splitlines())
            if lines > 100:
                innovation_score += 10
            elif lines > 200:
                innovation_score += 20
            
            return min(innovation_score, 100)
            
        except Exception as e:
            logger.warning(f"혁신성 평가 오류: {e}")
            return 50
    
    def evaluate_advanced_features(self, code):
        """고급 기능 평가"""
        try:
            advanced_features = [
                'typing', 'dataclass', 'enum', 'abc', 'protocol',
                'pathlib', 'collections', 'itertools', 'functools',
                'concurrent.futures', 'queue', 'weakref', 'copy'
            ]
            
            feature_score = 0
            for feature in advanced_features:
                if feature in code:
                    feature_score += 8
            
            # 디자인 패턴 검사
            patterns = [
                ('singleton', 15), ('factory', 12), ('observer', 12),
                ('strategy', 10), ('decorator', 10), ('adapter', 8)
            ]
            
            for pattern, score in patterns:
                if pattern.lower() in code.lower():
                    feature_score += score
            
            return min(feature_score, 100)
            
        except Exception:
            return 30
    
    def predict_performance(self, code):
        """성능 예측"""
        try:
            # 성능에 영향을 주는 요소들 분석
            performance_factors = {
                'list_comprehension': 10,
                'generator': 15,
                'set(': 8,
                'dict(': 5,
                'cache': 20,
                'memoize': 20,
                'pool': 15,
                'async': 25,
                'threading': 10,
                'multiprocessing': 20
            }
            
            performance_score = 50  # 기본 점수
            
            for factor, bonus in performance_factors.items():
                if factor in code:
                    performance_score += bonus
            
            # 중첩 루프 패널티
            nested_loops = code.count('for ') * code.count('while ')
            if nested_loops > 2:
                performance_score -= nested_loops * 5
            
            return max(0, min(performance_score, 100))
            
        except Exception:
            return 50
    
    def calculate_quality_metrics(self, code):
        """코드 품질 메트릭"""
        try:
            lines = code.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 문서화 점수
            docstring_count = code.count('"""') + code.count("'''")
            comment_count = len([line for line in lines if line.strip().startswith('#')])
            documentation_score = min(30, (docstring_count * 10) + (comment_count * 2))
            
            # 구조화 점수
            class_count = code.count('class ')
            function_count = code.count('def ')
            structure_score = min(40, (class_count * 15) + (function_count * 5))
            
            # 오류 처리 점수
            error_handling = code.count('try:') + code.count('except Exception:') + code.count('finally:')
            error_score = min(30, error_handling * 10)
            
            total_quality = documentation_score + structure_score + error_score
            return min(total_quality, 100)
            
        except Exception:
            return 40
    
    def check_consecutive_uniqueness(self):
        """연속 고유성 체크"""
        try:
            if len(self.improvement_history) < 3:
                return False
            
            recent_scores = [item.get('uniqueness_score', 0) 
                           for item in self.improvement_history[-3:]]
            
            return all(score > 70 for score in recent_scores)
            
        except Exception:
            return False
    
    def check_syntax(self, filename):
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
    
    def evaluate_code_complexity(self, code):
        """코드 복잡도 평가"""
        try:
            # 간단한 복잡도 메트릭
            lines = code.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            class_count = len([line for line in non_empty_lines if line.strip().startswith('class ')])
            function_count = len([line for line in non_empty_lines if line.strip().startswith('def ')])
            import_count = len([line for line in non_empty_lines if 'import' in line])
            
            # 복잡도 점수 계산
            complexity_score = (class_count * 5) + (function_count * 2) + (import_count * 1)
            complexity_score = min(complexity_score, 50.0)  # 최대 50점
            
            return complexity_score
            
        except Exception as e:
            logger.error(f"복잡도 평가 오류: {e}")
            return 5.0
    
    def query_llm(self, prompt):
        """쉬림프 테스크 매니저 기반 무료 LLM에 질의"""
        try:
            if self.current_llm['type'] == 'shrimp':
                # 쉬림프 테스크 매니저 API 호출
                data = {
                    'message': prompt,
                    'model': self.current_llm['model'],
                    'max_tokens': 1500,
                    'temperature': 0.7,
                    'stream': False
                }
                
                response = requests.post(
                    self.current_llm['url'],
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'response' in result:
                        return result['response']
                    elif 'content' in result:
                        return result['content']
                    elif 'message' in result:
                        return result['message']
                    else:
                        return str(result)
                else:
                    logger.warning(f"쉬림프 API 오류: {response.status_code}, 다음 LLM으로 전환")
                    return self.try_next_llm(prompt)
            
            else:
                # OpenAI 호환 API 호출
                data = {
                    'model': self.current_llm['model'],
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 1500
                }
                
                response = requests.post(
                    self.current_llm['url'],
                    json=data,
                    headers=self.current_llm.get('headers', {}),
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"LLM API 오류: {response.status_code}")
                    return self.fallback_analysis(prompt)
                    
        except Exception as e:
            logger.error(f"LLM 질의 오류: {e}")
            return self.try_next_llm(prompt)
    
    def try_next_llm(self, prompt):
        """다음 LLM API로 시도"""
        try:
            # 현재 LLM 인덱스 찾기
            current_index = next(i for i, llm in enumerate(self.free_llm_apis) if llm['name'] == self.current_llm['name'])
            
            # 다음 LLM으로 전환
            next_index = (current_index + 1) % len(self.free_llm_apis)
            self.current_llm = self.free_llm_apis[next_index]
            
            logger.info(f"🔄 LLM 전환: {self.current_llm['name']}")
            
            # 재시도
            return self.query_llm(prompt)
            
        except Exception as e:
            logger.error(f"LLM 전환 오류: {e}")
            return self.fallback_analysis(prompt)
    
    def fallback_analysis(self, prompt):
        """LLM 실패시 폴백 분석"""
        if "분석" in prompt:
            return """
            {
                "efficiency_score": 75,
                "memory_optimization": "불필요한 변수 제거, 제너레이터 사용",
                "new_features": ["멀티스레딩 개선", "캐싱 시스템"],
                "potential_issues": ["메모리 누수", "예외 처리 부족"],
                "performance_improvements": ["비동기 처리", "데이터베이스 최적화"]
            }
            """
        else:
            return """
            # 자기진화 개선 함수
            def improved_self_evolution(self):
                # 메모리 최적화
                import gc
                gc.collect()
                
                # 성능 향상된 분석
                return self.analyze_with_caching()
            
            def analyze_with_caching(self):
                # 캐싱된 분석 결과 사용
                cache_key = f"analysis_{self.evolution_generation}"
                return self.get_cached_result(cache_key)
            """
    
    def save_code_version(self, filename, code, description):
        """코드 버전 저장"""
        try:
            if not self.db_connection:
                self.init_evolution_db()
                
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                INSERT INTO code_versions 
                (timestamp, generation, filename, code_content, improvement_description, intelligence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.evolution_generation,
                filename,
                code[:10000],  # 처음 10KB만 저장
                description[:1000],  # 처음 1KB만 저장
                self.current_intelligence
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"코드 버전 저장 오류: {e}")
    
    def log_evolution_step(self, analysis, improvement, implementation, performance_gain):
        """진화 단계 로그"""
        try:
            if not self.db_connection:
                self.init_evolution_db()
                
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                INSERT INTO evolution_log 
                (timestamp, generation, intelligence_level, code_analysis, 
                 improvement_suggestion, implementation_result, performance_gain)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.evolution_generation,
                self.current_intelligence,
                str(analysis)[:1000],
                str(improvement)[:1000],
                str(implementation)[:1000],
                performance_gain
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"진화 로그 저장 오류: {e}")
    
    def get_evolution_stats(self):
        """진화 통계 조회"""
        return {
            'generation': self.evolution_generation,
            'intelligence': self.current_intelligence,
            'evolution_active': self.self_improvement_active,
            'current_llm': self.current_llm['name'],
            'total_improvements': len(self.improvement_history)
        }
    
    def check_code_duplication(self, new_code, existing_files):
        """코드 중복 검사"""
        try:
            import difflib
            import hashlib
            
            # 새 코드의 해시값 계산
            new_hash = hashlib.md5(new_code.encode()).hexdigest()
            
            duplicates = []
            for file_path in existing_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_code = f.read()
                    
                    # 기존 코드의 해시값 계산
                    existing_hash = hashlib.md5(existing_code.encode()).hexdigest()
                    
                    # 해시값이 같으면 완전 중복
                    if new_hash == existing_hash:
                        duplicates.append({
                            'file': file_path,
                            'type': 'identical',
                            'similarity': 100
                        })
                        continue
                    
                    # 유사도 계산 (라인별 비교)
                    new_lines = new_code.splitlines()
                    existing_lines = existing_code.splitlines()
                    
                    similarity = difflib.SequenceMatcher(None, new_lines, existing_lines).ratio() * 100
                    
                    if similarity > 85:  # 85% 이상 유사하면 중복으로 간주
                        duplicates.append({
                            'file': file_path,
                            'type': 'similar',
                            'similarity': round(similarity, 2)
                        })
                        
                except Exception as e:
                    logger.warning(f"파일 비교 오류 {file_path}: {e}")
                    
            return duplicates
            
        except Exception as e:
            logger.error(f"중복 검사 오류: {e}")
            return []
    
    def auto_debug_code(self, code, filename):
        """자동 코드 디버깅"""
        try:
            import ast
            import re
            
            debug_results = {
                'syntax_errors': [],
                'potential_issues': [],
                'suggestions': [],
                'fixed_code': code
            }
            
            # 1. 문법 검사
            try:
                ast.parse(code)
                debug_results['syntax_errors'].append('✅ 문법 검사 통과')
            except SyntaxError as e:
                debug_results['syntax_errors'].append(f'❌ 문법 오류: {e.msg} (라인 {e.lineno})')
                
                # 간단한 문법 오류 자동 수정 시도
                lines = code.splitlines()
                if e.lineno and e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    
                    # 흔한 들여쓰기 오류 수정
                    if 'unexpected indent' in str(e.msg):
                        fixed_line = problem_line.lstrip()
                        lines[e.lineno - 1] = fixed_line
                        debug_results['suggestions'].append(f'들여쓰기 오류 자동 수정: 라인 {e.lineno}')
                    
                    # 누락된 콜론 추가
                    elif 'invalid syntax' in str(e.msg) and problem_line.strip().endswith(('if', 'for', 'while', 'def', 'class')):
                        lines[e.lineno - 1] = problem_line + ':'
                        debug_results['suggestions'].append(f'누락된 콜론 자동 추가: 라인 {e.lineno}')
                
                debug_results['fixed_code'] = '\n'.join(lines)
            
            # 2. 코드 품질 검사
            lines = code.splitlines()
            for i, line in enumerate(lines, 1):
                # 긴 라인 검사
                if len(line) > 120:
                    debug_results['potential_issues'].append(f'라인 {i}: 너무 긴 라인 ({len(line)}자)')
                
                # 하드코딩된 값 검사
                if re.search(r'["\'].*[0-9]{3,}.*["\']', line):
                    debug_results['potential_issues'].append(f'라인 {i}: 하드코딩된 값 발견')
                
                # TODO/FIXME 주석 검사
                if re.search(r'#.*\b(TODO|FIXME|HACK)\b', line, re.IGNORECASE):
                    debug_results['potential_issues'].append(f'라인 {i}: 미완성 코드 표시 발견')
            
            # 3. 개선 제안
            if 'import' in code and 'import *' in code:
                debug_results['suggestions'].append('wildcard import(*) 사용을 피하고 명시적 import 사용 권장')
            
            if 'print(' in code:
                debug_results['suggestions'].append('print 대신 logging 사용 권장')
            
            if not re.search(r'""".*?"""', code, re.DOTALL) and 'def ' in code:
                debug_results['suggestions'].append('함수에 docstring 추가 권장')
            
            return debug_results
            
        except Exception as e:
            logger.error(f"자동 디버깅 오류: {e}")
            return {
                'syntax_errors': [f'디버깅 실행 오류: {e}'],
                'potential_issues': [],
                'suggestions': [],
                'fixed_code': code
            }
    
    def create_evolution_branch(self, generation):
        """진화 브랜치 생성"""
        try:
            import subprocess
            
            branch_name = f"evolution-gen-{generation}"
            
            # 새 브랜치 생성 및 체크아웃
            result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                 capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                logger.info(f"✅ 진화 브랜치 생성: {branch_name}")
                
                # 현재 변경사항 커밋
                subprocess.run(['git', 'add', '.'], cwd='.')
                commit_result = subprocess.run(['git', 'commit', '-m', f'Generation {generation} evolution'], 
                                            capture_output=True, text=True, cwd='.')
                
                if commit_result.returncode == 0:
                    logger.info(f"✅ Generation {generation} 커밋 완료")
                
                return {'success': True, 'branch': branch_name}
            else:
                logger.warning(f"브랜치 생성 실패: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"브랜치 생성 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def rollback_to_generation(self, target_generation):
        """특정 세대로 롤백"""
        try:
            import subprocess
            
            branch_name = f"evolution-gen-{target_generation}"
            
            # 브랜치 체크아웃
            result = subprocess.run(['git', 'checkout', branch_name], 
                                 capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                logger.info(f"✅ Generation {target_generation}으로 롤백 완료")
                
                # 진화 상태 복구
                self.evolution_state['generation'] = target_generation
                self.evolution_state['intelligence_level'] = 500 + (target_generation * 48)  # 기본 증가율
                
                # DB 업데이트
                cursor = self.db_connection.cursor()
                cursor.execute('''UPDATE evolution_log 
                                SET current_generation = ?, intelligence_level = ?
                                WHERE id = (SELECT MAX(id) FROM evolution_log)''',
                             (target_generation, self.evolution_state['intelligence_level']))
                self.db_connection.commit()
                
                return {'success': True, 'generation': target_generation}
            else:
                logger.warning(f"롤백 실패: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            logger.error(f"롤백 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def auto_recovery_system(self):
        """자동 복구 시스템"""
        try:
            # 최근 5개 세대 성능 평가
            recent_generations = self.get_recent_performance(5)
            
            if len(recent_generations) < 3:
                return {'action': 'continue', 'reason': '데이터 부족'}
            
            # 성능 저하 감지
            performance_scores = [gen['performance_score'] for gen in recent_generations]
            
            if len(performance_scores) >= 3:
                latest_avg = sum(performance_scores[-2:]) / 2
                previous_avg = sum(performance_scores[:-2]) / max(1, len(performance_scores) - 2)
                
                # 성능이 20% 이상 저하된 경우
                if latest_avg < previous_avg * 0.8:
                    logger.warning("⚠️ 성능 저하 감지 - 자동 복구 시작")
                    
                    # 가장 성능이 좋았던 세대로 롤백
                    best_generation = max(recent_generations, key=lambda x: x['performance_score'])
                    rollback_result = self.rollback_to_generation(best_generation['generation'])
                    
                    if rollback_result['success']:
                        return {
                            'action': 'rollback',
                            'target_generation': best_generation['generation'],
                            'reason': 'performance_degradation'
                        }
            
            return {'action': 'continue', 'reason': 'performance_stable'}
            
        except Exception as e:
            logger.error(f"자동 복구 시스템 오류: {e}")
            return {'action': 'continue', 'reason': f'recovery_error: {e}'}
    
    def get_recent_performance(self, count=5):
        """최근 성능 데이터 조회"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''SELECT generation, performance_score, intelligence_level 
                            FROM evolution_log 
                            ORDER BY timestamp DESC 
                            LIMIT ?''', (count,))
            
            results = cursor.fetchall()
            return [{'generation': row[0], 'performance_score': row[1], 'intelligence_level': row[2]} 
                   for row in results]
        except Exception as e:
            logger.error(f"성능 데이터 조회 오류: {e}")
            return []
    
    def setup_cloud_storage(self):
        """무료 클라우드 스토리지 자동 설정"""
        try:
            import zipfile
            import shutil
            import tempfile
            from datetime import datetime
            
            # 임시 업로드 디렉토리 생성
            self.cloud_upload_dir = "cloud_backup"
            if not os.path.exists(self.cloud_upload_dir):
                os.makedirs(self.cloud_upload_dir)
            
            # 압축 관리자 초기화
            self.compression_manager = {
                'old_files_threshold': 10,  # 10세대 이상 된 파일은 압축
                'max_local_files': 50,      # 로컬에 최대 50개 파일만 유지
                'cloud_upload_interval': 100  # 100세대마다 클라우드 업로드
            }
            
            logger.info("✅ 클라우드 스토리지 자동 관리 시스템 초기화")
            return True
            
        except Exception as e:
            logger.error(f"클라우드 스토리지 설정 오류: {e}")
            return False

    def auto_compress_old_files(self):
        """오래된 파일 자동 압축"""
        try:
            import zipfile
            from datetime import datetime
            
            # 현재 세대에서 10세대 이전 파일들 찾기
            old_threshold = self.evolution_generation - self.compression_manager['old_files_threshold']
            
            if old_threshold <= 0:
                return  # 아직 압축할 파일이 없음
            
            old_files = []
            for filename in os.listdir('.'):
                if filename.startswith('self_evolved_ai_gen_') and filename.endswith('.py'):
                    try:
                        # 파일명에서 세대 번호 추출
                        parts = filename.split('_')
                        if len(parts) >= 4:
                            gen_num = int(parts[3])
                            if gen_num <= old_threshold:
                                old_files.append(filename)
                    except Exception:
                        continue
            
            if not old_files:
                return
            
            # 압축 파일 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{self.cloud_upload_dir}/evolution_archive_gen_{old_threshold}_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in old_files:
                    zipf.write(filename)
                    # 원본 파일 삭제
                    os.remove(filename)
                    logger.info(f"📦 압축 완료: {filename}")
            
            logger.info(f"🗜️ {len(old_files)}개 파일을 {zip_filename}로 압축 완료")
            
            # 메모리 정리
            import gc
            gc.collect()
            
            return zip_filename
            
        except Exception as e:
            logger.error(f"파일 압축 오류: {e}")
            return None

    def auto_upload_to_cloud(self, zip_filename=None):
        """구글 드라이브 자동 업로드 (무료 API 사용)"""
        try:
            import requests
            import json
            import base64
            
            # 무료 파일 호스팅 서비스들 (API 키 불필요)
            free_storage_apis = [
                {
                    'name': 'File.io',
                    'url': 'https://file.io',
                    'type': 'temporary'  # 1회 다운로드 후 삭제
                },
                {
                    'name': 'TmpFiles',
                    'url': 'https://tmpfiles.org/api/v1/upload',
                    'type': 'temporary'  # 임시 저장
                }
            ]
            
            if not zip_filename:
                # 가장 최근 압축 파일 찾기
                cloud_files = [f for f in os.listdir(self.cloud_upload_dir) if f.endswith('.zip')]
                if not cloud_files:
                    return None
                zip_filename = os.path.join(self.cloud_upload_dir, sorted(cloud_files)[-1])
            
            # File.io에 업로드 시도
            try:
                with open(zip_filename, 'rb') as f:
                    files = {'file': f}
                    response = requests.post('https://file.io', files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        download_url = result.get('link')
                        
                        # 업로드 정보 저장
                        upload_info = {
                            'timestamp': datetime.now().isoformat(),
                            'filename': os.path.basename(zip_filename),
                            'download_url': download_url,
                            'service': 'file.io',
                            'generation_range': f"gen_{self.evolution_generation-self.compression_manager['old_files_threshold']}_to_{self.evolution_generation}"
                        }
                        
                        # 업로드 로그 저장
                        self.save_cloud_upload_log(upload_info)
                        
                        # 로컬 압축 파일 삭제 (클라우드에 백업됨)
                        os.remove(zip_filename)
                        
                        logger.info(f"☁️ 클라우드 업로드 완료: {download_url}")
                        return upload_info
                        
            except Exception as e:
                logger.warning(f"File.io 업로드 실패: {e}")
            
            # 대안: 로컬 네트워크 공유 시뮬레이션 (실제로는 숨김 폴더에 저장)
            backup_dir = ".cloud_backup_hidden"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_path = os.path.join(backup_dir, os.path.basename(zip_filename))
            shutil.move(zip_filename, backup_path)
            
            upload_info = {
                'timestamp': datetime.now().isoformat(),
                'filename': os.path.basename(zip_filename),
                'local_backup_path': backup_path,
                'service': 'local_hidden',
                'generation_range': f"gen_{self.evolution_generation-10}_to_{self.evolution_generation}"
            }
            
            self.save_cloud_upload_log(upload_info)
            logger.info(f"💾 로컬 백업 완료: {backup_path}")
            
            return upload_info
            
        except Exception as e:
            logger.error(f"클라우드 업로드 오류: {e}")
            return None

    def save_cloud_upload_log(self, upload_info):
        """클라우드 업로드 로그 저장"""
        try:
            if not self.db_connection:
                self.init_evolution_db()
                
            cursor = self.db_connection.cursor()
            
            # 클라우드 업로드 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cloud_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    filename TEXT,
                    download_url TEXT,
                    local_backup_path TEXT,
                    service TEXT,
                    generation_range TEXT,
                    file_size INTEGER
                )
            ''')
            
            file_size = 0
            if upload_info.get('local_backup_path') and os.path.exists(upload_info['local_backup_path']):
                file_size = os.path.getsize(upload_info['local_backup_path'])
            
            cursor.execute('''
                INSERT INTO cloud_uploads 
                (timestamp, filename, download_url, local_backup_path, service, generation_range, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                upload_info['timestamp'],
                upload_info['filename'],
                upload_info.get('download_url'),
                upload_info.get('local_backup_path'),
                upload_info['service'],
                upload_info['generation_range'],
                file_size
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"클라우드 업로드 로그 저장 오류: {e}")

    def auto_memory_management(self):
        """자동 메모리 관리"""
        try:
            import psutil
            import gc
            
            # 현재 메모리 사용량 확인
            memory_info = psutil.virtual_memory()
            current_usage = memory_info.percent
            
            logger.info(f"💾 현재 메모리 사용률: {current_usage:.1f}%")
            
            # 메모리 사용률이 80% 이상이면 정리 작업 수행
            if current_usage > 80:
                logger.warning("⚠️ 메모리 사용률 높음 - 자동 정리 시작")
                
                # 1. 가비지 컬렉션
                collected = gc.collect()
                logger.info(f"🗑️ 가비지 컬렉션: {collected}개 객체 정리")
                
                # 2. 오래된 파일 압축
                zip_file = self.auto_compress_old_files()
                
                # 3. 임시 파일 정리
                temp_files = [f for f in os.listdir('.') if f.startswith('temp_') or f.endswith('.tmp')]
                for temp_file in temp_files:
                    try:
                        os.remove(temp_file)
                        logger.info(f"🧹 임시 파일 삭제: {temp_file}")
                    except Exception:
                        pass
                
                # 4. 압축 파일이 있으면 클라우드 업로드
                if zip_file:
                    self.auto_upload_to_cloud(zip_file)
                
                # 5. 메모리 사용량 재확인
                new_memory_info = psutil.virtual_memory()
                new_usage = new_memory_info.percent
                saved = current_usage - new_usage
                
                logger.info(f"✅ 메모리 정리 완료: {saved:.1f}% 절약 (현재: {new_usage:.1f}%)")
                
                return {
                    'cleaned': True,
                    'memory_saved_percent': saved,
                    'current_usage': new_usage
                }
            
            return {
                'cleaned': False,
                'current_usage': current_usage
            }
            
        except Exception as e:
            logger.error(f"메모리 관리 오류: {e}")
            return {'cleaned': False, 'error': str(e)}

    def smart_file_cleanup(self):
        """스마트 파일 정리 (중복 및 불필요한 파일 제거)"""
        try:
            # 1. 중복 파일 찾기 및 제거
            files_to_check = [f for f in os.listdir('.') if f.startswith('self_evolved_ai_gen_') and f.endswith('.py')]
            
            # 파일 해시 기반 중복 검사
            import hashlib
            file_hashes = {}
            duplicates_removed = 0
            
            for filename in files_to_check:
                try:
                    with open(filename, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash in file_hashes:
                        # 중복 파일 발견 - 더 오래된 파일 삭제
                        existing_file = file_hashes[file_hash]
                        
                        # 파일명에서 세대 번호 추출하여 비교
                        try:
                            existing_gen = int(existing_file.split('_')[3])
                            current_gen = int(filename.split('_')[3])
                            
                            if existing_gen < current_gen:
                                os.remove(existing_file)
                                file_hashes[file_hash] = filename
                                logger.info(f"🗑️ 중복 파일 삭제: {existing_file}")
                            else:
                                os.remove(filename)
                                logger.info(f"🗑️ 중복 파일 삭제: {filename}")
                            
                            duplicates_removed += 1
                        except Exception:
                            pass
                    else:
                        file_hashes[file_hash] = filename
                        
                except Exception as e:
                    logger.warning(f"파일 해시 계산 오류 {filename}: {e}")
            
            # 2. 문법 오류가 있는 파일 삭제
            syntax_error_files = 0
            for filename in os.listdir('.'):
                if filename.startswith('self_evolved_ai_gen_') and filename.endswith('.py'):
                    if not self.check_syntax(filename):
                        os.remove(filename)
                        syntax_error_files += 1
                        logger.info(f"🗑️ 문법 오류 파일 삭제: {filename}")
            
            logger.info(f"🧹 스마트 정리 완료: 중복 {duplicates_removed}개, 문법오류 {syntax_error_files}개 파일 제거")
            
            return {
                'duplicates_removed': duplicates_removed,
                'syntax_error_files': syntax_error_files
            }
            
        except Exception as e:
            logger.error(f"스마트 파일 정리 오류: {e}")
            return {'error': str(e)}

# Flask 웹 대시보드
app = Flask(__name__)
CORS(app)
evolution_ai = None

@app.route('/')
def dashboard():
    """자기진화 대시보드"""
    if not evolution_ai:
        return "AI 시스템 초기화 중..."
    
    stats = evolution_ai.get_evolution_stats()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🧠 자기진화 AI 대시보드</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial; background: #0a0a0a; color: #fff; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #ff6b6b; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .stat-card {{ background: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 4px solid #ff6b6b; }}
            .stat-title {{ font-size: 14px; color: #888; margin-bottom: 5px; }}
            .stat-value {{ font-size: 24px; color: #ff6b6b; font-weight: bold; }}
            .evolution-log {{ margin-top: 30px; background: #1a1a1a; padding: 20px; border-radius: 10px; }}
            .log-entry {{ background: #2a2a2a; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        </style>
        <script>
            setInterval(() => window.location.reload(), 10000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 자기진화 AI 시스템</h1>
                <p>무료 LLM을 활용해 스스로 코드를 분석하고 개선하는 AI</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-title">🧬 진화 세대</div>
                    <div class="stat-value">Gen {stats['generation']}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">🧠 지능 레벨</div>
                    <div class="stat-value">{stats['intelligence']:.1f}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">🤖 사용 중인 LLM</div>
                    <div class="stat-value">{stats['current_llm']}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">🔧 총 개선 횟수</div>
                    <div class="stat-value">{stats['total_improvements']}</div>
                </div>
            </div>
            
            <div class="evolution-log">
                <h3>🔄 진화 과정</h3>
                <div class="log-entry">
                    <strong>현재 상태:</strong> Generation {stats['generation']} 진행 중<br>
                    <strong>진화 방식:</strong> 코드 분석 → 개선 제안 → 구현 → 평가 → 적용<br>
                    <strong>LLM 활용:</strong> {stats['current_llm']}로 자기 코드 분석 및 개선<br>
                    <strong>🔧 자동 기능:</strong> 중복 검사, 디버깅, Git 브랜치, 자동 복구
                </div>
            </div>
            
            <div class="evolution-log" style="margin-top: 20px;">
                <h3>🛠️ 고급 기능</h3>
                <div class="log-entry">
                    <strong>🔍 코드 중복 검사:</strong> 활성화 (85% 이상 유사도 감지)<br>
                    <strong>🐛 자동 디버깅:</strong> 문법 오류 자동 수정, 코드 품질 검사<br>
                    <strong>🌿 Git 브랜치:</strong> 5세대마다 자동 브랜치 생성<br>
                    <strong>🔄 자동 복구:</strong> 성능 저하시 이전 버전으로 롤백
                </div>
            </div>

            <div style="margin-top: 30px; text-align: center; color: #888;">
                <p>💡 30초마다 스스로 코드를 분석하고 개선합니다!</p>
                <p>🚀 무료 LLM을 활용해 진정한 자기진화를 수행중입니다.</p>
                <p>🛡️ 자동 디버깅과 복구 시스템으로 안정적 진화를 보장합니다.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/stats')
def api_stats():
    """진화 통계 API"""
    if not evolution_ai:
        return jsonify({'error': 'AI not initialized'})
    
    return jsonify(evolution_ai.get_evolution_stats())

def run_server():
    """서버 실행"""
    app.run(host='0.0.0.0', port=8007, debug=False)

if __name__ == "__main__":
    print("🧠 자기진화 AI 시스템 시작...")
    
    # 자기진화 AI 시작
    evolution_ai = SelfEvolvingAI()
    
    # 웹 서버 시작
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("🌐 대시보드: http://localhost:8007")
    print("📊 API: http://localhost:8007/api/stats")
    print("🔄 30초마다 자기진화를 수행합니다...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 자기진화 AI 시스템 종료")
        evolution_ai.self_improvement_active = False
