#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Advanced Agent Evolution System
===================================
AI 에이전트의 자동 발전과 최적화를 위한 포괄적인 시스템
"""

import asyncio
import json
import logging
import os
import time
import sqlite3
import numpy as np
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
import websockets

# 알림 시스템 import 추가 (에러 방지)
try:
    from advanced_notification_system import get_notification_system, send_agent_alert, send_custom_alert, AlertLevel
except ImportError:
    # 알림 시스템이 없어도 작동하도록 더미 클래스 정의
    class AlertLevel:
        CRITICAL = "CRITICAL"
        WARNING = "WARNING"
        INFO = "INFO"
    
    def send_agent_alert(title, message, level):
        pass
    
    def send_custom_alert(title, message, level):
        pass
    
    def get_notification_system():
        return None

# 에이전트 타입 정의
class AgentType(Enum):
    LEARNING = "learning"
    GOAL_ORIENTED = "goal_oriented"
    EVOLUTIONARY = "evolutionary"
    CONVERSATIONAL = "conversational"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"

# 성능 메트릭 정의
@dataclass
class PerformanceMetrics:
    accuracy: float = 0.0
    response_time: float = 0.0
    user_satisfaction: float = 0.0
    task_completion_rate: float = 0.0
    error_rate: float = 0.0
    learning_speed: float = 0.0
    adaptability: float = 0.0
    
    def overall_score(self) -> float:
        """전체 성능 점수 계산"""
        weights = {
            'accuracy': 0.25,
            'response_time': 0.15,
            'user_satisfaction': 0.20,
            'task_completion_rate': 0.20,
            'error_rate': -0.10,  # 에러율은 마이너스
            'learning_speed': 0.15,
            'adaptability': 0.15
        }
        
        score = (
            self.accuracy * weights['accuracy'] +
            (1.0 - min(self.response_time / 10.0, 1.0)) * weights['response_time'] +
            self.user_satisfaction * weights['user_satisfaction'] +
            self.task_completion_rate * weights['task_completion_rate'] +
            (1.0 - self.error_rate) * weights['error_rate'] +
            self.learning_speed * weights['learning_speed'] +
            self.adaptability * weights['adaptability']
        )
        return max(0.0, min(1.0, score))

# 에이전트 구성 정의
@dataclass
class AgentConfig:
    agent_id: str
    agent_type: AgentType
    learning_rate: float = 0.1
    memory_size: int = 1000
    exploration_rate: float = 0.1
    temperature: float = 0.7
    max_iterations: int = 1000
    specialized_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.specialized_params is None:
            self.specialized_params = {}

class AgentEvolutionSystem:
    """AI 에이전트 진화 및 최적화 시스템"""
    
    def __init__(self, db_path: str = "agent_evolution.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, AgentConfig] = {}
        self.performance_history: Dict[str, List[PerformanceMetrics]] = {}
        self.evolution_strategies = []
        self.active_experiments = {}
        
        print("🔧 에이전트 진화 시스템 초기화 중...")
        self.setup_database()
        self.initialize_evolution_strategies()
        print("✅ 에이전트 진화 시스템 초기화 완료")
    
    def setup_database(self):
        """SQLite 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 에이전트 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    config JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 성능 기록 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics JSON,
                    overall_score REAL,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            ''')
            
            # 진화 실험 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolution_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    parent_agent_id TEXT,
                    mutation_type TEXT,
                    parameters JSON,
                    success_rate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ 에이전트 진화 데이터베이스 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
    
    def initialize_evolution_strategies(self):
        """진화 전략 초기화"""
        self.evolution_strategies = [
            self.parameter_mutation,
            self.architecture_modification,
            self.learning_rate_adaptation,
            self.memory_optimization,
            self.cross_agent_knowledge_transfer,
            self.performance_based_selection
        ]
        self.logger.info("✅ 진화 전략 초기화 완료")
    
    def register_agent(self, config: AgentConfig) -> bool:
        """새 에이전트 등록"""
        try:
            self.agents[config.agent_id] = config
            self.performance_history[config.agent_id] = []
            
            # 데이터베이스에 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO agents (agent_id, agent_type, config)
                VALUES (?, ?, ?)
            ''', (config.agent_id, config.agent_type.value, json.dumps({
                'agent_id': config.agent_id,
                'agent_type': config.agent_type.value,
                'learning_rate': config.learning_rate,
                'memory_size': config.memory_size,
                'exploration_rate': config.exploration_rate,
                'temperature': config.temperature,
                'max_iterations': config.max_iterations,
                'specialized_params': config.specialized_params
            })))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ 에이전트 '{config.agent_id}' 등록 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 에이전트 등록 실패: {e}")
            return False
    
    def record_performance(self, agent_id: str, metrics: PerformanceMetrics) -> bool:
        """에이전트 성능 기록"""
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"⚠️ 등록되지 않은 에이전트: {agent_id}")
                return False
            
            self.performance_history[agent_id].append(metrics)
            
            # 최근 20개 기록만 유지 (메모리 최적화)
            if len(self.performance_history[agent_id]) > 20:
                self.performance_history[agent_id] = self.performance_history[agent_id][-20:]
            
            # 데이터베이스에 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_logs (agent_id, metrics, overall_score)
                VALUES (?, ?, ?)
            ''', (agent_id, json.dumps(asdict(metrics)), metrics.overall_score()))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 성능 기록 실패: {e}")
            return False
    
    async def evolve_agent(self, agent_id: str, target_improvement: float = 0.1) -> Optional[AgentConfig]:
        """에이전트 진화 실행"""
        try:
            if agent_id not in self.agents:
                self.logger.error(f"❌ 에이전트를 찾을 수 없음: {agent_id}")
                return None
            
            current_config = self.agents[agent_id]
            current_performance = self.get_average_performance(agent_id)
            
            self.logger.info(f"🧬 에이전트 '{agent_id}' 진화 시작 (현재 성능: {current_performance:.3f})")
            
            best_config = current_config
            best_performance = current_performance
            
            # 다양한 진화 전략 시도
            for strategy in self.evolution_strategies:
                try:
                    new_config = await strategy(current_config)
                    if new_config:
                        # 새 구성으로 성능 테스트
                        test_performance = await self.test_agent_performance(new_config)
                        
                        if test_performance > best_performance + target_improvement:
                            best_config = new_config
                            best_performance = test_performance
                            self.logger.info(f"🎯 개선된 구성 발견: {test_performance:.3f} (+{test_performance - current_performance:.3f})")
                
                except Exception as e:
                    self.logger.warning(f"⚠️ 진화 전략 실패 '{strategy.__name__}': {e}")
            
            # 개선된 구성이 있으면 적용
            if best_performance > current_performance:
                evolved_id = f"{agent_id}_evolved_{int(time.time())}"
                best_config.agent_id = evolved_id
                
                if self.register_agent(best_config):
                    self.logger.info(f"✅ 에이전트 진화 완료: {agent_id} → {evolved_id}")
                    return best_config
            
            self.logger.info(f"ℹ️ 에이전트 '{agent_id}' 진화에서 개선 사항 없음")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 에이전트 진화 실패: {e}")
            return None
    
    async def parameter_mutation(self, config: AgentConfig) -> Optional[AgentConfig]:
        """매개변수 돌연변이"""
        try:
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=max(0.001, min(1.0, config.learning_rate * random.uniform(0.5, 2.0))),
                memory_size=max(100, min(10000, int(config.memory_size * random.uniform(0.8, 1.5)))),
                exploration_rate=max(0.01, min(0.5, config.exploration_rate * random.uniform(0.5, 2.0))),
                temperature=max(0.1, min(2.0, config.temperature * random.uniform(0.8, 1.2))),
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 매개변수 돌연변이 실패: {e}")
            return None
    
    async def architecture_modification(self, config: AgentConfig) -> Optional[AgentConfig]:
        """아키텍처 수정"""
        try:
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=config.learning_rate,
                memory_size=config.memory_size,
                exploration_rate=config.exploration_rate,
                temperature=config.temperature,
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            
            # 특화 매개변수 수정
            if 'hidden_layers' in new_config.specialized_params:
                current_layers = new_config.specialized_params['hidden_layers']
                new_config.specialized_params['hidden_layers'] = max(1, current_layers + random.choice([-1, 0, 1]))
            
            if 'batch_size' in new_config.specialized_params:
                current_batch = new_config.specialized_params['batch_size']
                new_config.specialized_params['batch_size'] = max(1, int(current_batch * random.uniform(0.5, 2.0)))
            
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 아키텍처 수정 실패: {e}")
            return None
    
    async def learning_rate_adaptation(self, config: AgentConfig) -> Optional[AgentConfig]:
        """학습률 적응"""
        try:
            performance_trend = self.get_performance_trend(config.agent_id)
            
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=config.learning_rate,
                memory_size=config.memory_size,
                exploration_rate=config.exploration_rate,
                temperature=config.temperature,
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            
            if performance_trend < 0:  # 성능 감소 시 학습률 증가
                new_config.learning_rate = min(1.0, config.learning_rate * 1.5)
            elif performance_trend > 0:  # 성능 향상 시 학습률 미세 조정
                new_config.learning_rate = max(0.001, config.learning_rate * 0.9)
            
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 학습률 적응 실패: {e}")
            return None
    
    async def memory_optimization(self, config: AgentConfig) -> Optional[AgentConfig]:
        """메모리 최적화"""
        try:
            avg_performance = self.get_average_performance(config.agent_id)
            
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=config.learning_rate,
                memory_size=config.memory_size,
                exploration_rate=config.exploration_rate,
                temperature=config.temperature,
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            
            if avg_performance < 0.5:  # 성능이 낮으면 메모리 증가
                new_config.memory_size = min(10000, int(config.memory_size * 1.3))
            else:  # 성능이 좋으면 메모리 효율성 향상
                new_config.memory_size = max(100, int(config.memory_size * 0.9))
            
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 메모리 최적화 실패: {e}")
            return None
    
    async def cross_agent_knowledge_transfer(self, config: AgentConfig) -> Optional[AgentConfig]:
        """에이전트 간 지식 전이"""
        try:
            # 같은 타입의 다른 고성능 에이전트 찾기
            best_agents = self.get_top_performing_agents(config.agent_type, limit=3)
            
            if not best_agents or config.agent_id in [agent['agent_id'] for agent in best_agents]:
                return None
            
            # 최고 성능 에이전트의 매개변수 활용
            best_agent_id = best_agents[0]['agent_id']
            best_config = self.agents[best_agent_id]
            
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=(config.learning_rate + best_config.learning_rate) / 2,
                memory_size=int((config.memory_size + best_config.memory_size) / 2),
                exploration_rate=(config.exploration_rate + best_config.exploration_rate) / 2,
                temperature=(config.temperature + best_config.temperature) / 2,
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            
            # 특화 매개변수도 평균화
            for key in best_config.specialized_params:
                if key in new_config.specialized_params:
                    if isinstance(new_config.specialized_params[key], (int, float)):
                        new_config.specialized_params[key] = (
                            new_config.specialized_params[key] + best_config.specialized_params[key]
                        ) / 2
            
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 지식 전이 실패: {e}")
            return None
    
    async def performance_based_selection(self, config: AgentConfig) -> Optional[AgentConfig]:
        """성능 기반 선택적 진화"""
        try:
            recent_performance = self.get_recent_performance(config.agent_id, window=10)
            
            if not recent_performance:
                return None
            
            # 성능 변동성 분석
            performances = [p.overall_score() for p in recent_performance]
            avg_perf = np.mean(performances)
            std_perf = np.std(performances)
            
            new_config = AgentConfig(
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                learning_rate=config.learning_rate,
                memory_size=config.memory_size,
                exploration_rate=config.exploration_rate,
                temperature=config.temperature,
                max_iterations=config.max_iterations,
                specialized_params=config.specialized_params.copy()
            )
            
            # 변동성이 높으면 안정화, 낮으면 탐험 증가
            if std_perf > 0.1:  # 높은 변동성
                new_config.exploration_rate = max(0.01, config.exploration_rate * 0.8)
                new_config.temperature = max(0.1, config.temperature * 0.9)
            else:  # 낮은 변동성
                new_config.exploration_rate = min(0.5, config.exploration_rate * 1.2)
                new_config.temperature = min(2.0, config.temperature * 1.1)
            
            return new_config
        except Exception as e:
            self.logger.error(f"❌ 성능 기반 선택 실패: {e}")
            return None
    
    async def test_agent_performance(self, config: AgentConfig) -> float:
        """에이전트 성능 테스트 (시뮬레이션)"""
        try:
            # 실제 구현에서는 실제 태스크로 테스트
            # 여기서는 매개변수 기반 시뮬레이션
            base_score = 0.5
            
            # 학습률 최적화 점수
            lr_score = 1.0 - abs(config.learning_rate - 0.1) / 0.1
            
            # 메모리 크기 최적화 점수
            memory_score = min(1.0, config.memory_size / 1000.0)
            
            # 탐험률 균형 점수
            exploration_score = 1.0 - abs(config.exploration_rate - 0.1) / 0.1
            
            # 온도 매개변수 점수
            temp_score = 1.0 - abs(config.temperature - 0.7) / 0.7
            
            # 가중 평균 계산
            weighted_score = (
                base_score * 0.3 +
                lr_score * 0.2 +
                memory_score * 0.2 +
                exploration_score * 0.15 +
                temp_score * 0.15
            )
            
            # 랜덤 노이즈 추가 (실제 환경의 불확실성 시뮬레이션)
            noise = random.uniform(-0.1, 0.1)
            final_score = max(0.0, min(1.0, weighted_score + noise))
            
            await asyncio.sleep(0.1)  # 테스트 시간 시뮬레이션
            return final_score
            
        except Exception as e:
            self.logger.error(f"❌ 성능 테스트 실패: {e}")
            return 0.0
    
    def get_average_performance(self, agent_id: str, window: int = 10) -> float:
        """평균 성능 조회"""
        try:
            if agent_id not in self.performance_history:
                return 0.0
            
            recent_metrics = self.performance_history[agent_id][-window:]
            if not recent_metrics:
                return 0.0
            
            scores = [metrics.overall_score() for metrics in recent_metrics]
            return np.mean(scores)
        except Exception as e:
            self.logger.error(f"❌ 평균 성능 계산 실패: {e}")
            return 0.0
    
    def get_recent_performance(self, agent_id: str, window: int = 10) -> List[PerformanceMetrics]:
        """최근 성능 기록 조회"""
        try:
            if agent_id not in self.performance_history:
                return []
            return self.performance_history[agent_id][-window:]
        except Exception as e:
            self.logger.error(f"❌ 최근 성능 조회 실패: {e}")
            return []
    
    def get_performance_trend(self, agent_id: str, window: int = 10) -> float:
        """성능 트렌드 분석"""
        try:
            recent_metrics = self.get_recent_performance(agent_id, window)
            if len(recent_metrics) < 2:
                return 0.0
            
            scores = [metrics.overall_score() for metrics in recent_metrics]
            
            # 선형 회귀로 트렌드 계산
            x = np.arange(len(scores))
            coeffs = np.polyfit(x, scores, 1)
            return coeffs[0]  # 기울기 반환
        except Exception as e:
            self.logger.error(f"❌ 성능 트렌드 분석 실패: {e}")
            return 0.0
    
    def get_top_performing_agents(self, agent_type: AgentType, limit: int = 5) -> List[Dict]:
        """최고 성능 에이전트 목록"""
        try:
            agent_scores = []
            
            for agent_id, config in self.agents.items():
                if config.agent_type == agent_type:
                    avg_score = self.get_average_performance(agent_id)
                    agent_scores.append({
                        'agent_id': agent_id,
                        'score': avg_score,
                        'config': config
                    })
            
            # 점수 순으로 정렬
            agent_scores.sort(key=lambda x: x['score'], reverse=True)
            return agent_scores[:limit]
        except Exception as e:
            self.logger.error(f"❌ 최고 성능 에이전트 조회 실패: {e}")
            return []
    
    async def run_continuous_evolution(self, check_interval: int = 3600, max_concurrent_tasks: int = 3):
        """지속적인 진화 프로세스 실행 (메모리 최적화)"""
        self.logger.info("🔄 지속적인 에이전트 진화 프로세스 시작")
        
        try:
            while True:
                # 메모리 사용량 체크
                try:
                    import psutil
                    memory_percent = psutil.virtual_memory().percent
                    if memory_percent > 85:
                        self.logger.warning(f"⚠️ 높은 메모리 사용량 ({memory_percent}%) - 진화 프로세스 일시 중단")
                        await asyncio.sleep(check_interval * 2)  # 더 오래 대기
                        continue
                except ImportError:
                    pass
                
                # 제한된 수의 에이전트만 동시 진화
                evolution_tasks = []
                agent_list = list(self.agents.keys())
                
                for i, agent_id in enumerate(agent_list[:max_concurrent_tasks]):
                    # 최근 성능이 정체되거나 감소한 에이전트 우선
                    trend = self.get_performance_trend(agent_id)
                    avg_performance = self.get_average_performance(agent_id)
                    
                    if trend <= 0 or avg_performance < 0.7:
                        task = asyncio.create_task(self.evolve_agent(agent_id))
                        evolution_tasks.append(task)
                
                # 병렬 진화 실행 (제한된 수)
                if evolution_tasks:
                    results = await asyncio.gather(*evolution_tasks, return_exceptions=True)
                    successful_evolutions = sum(1 for r in results if r is not None and not isinstance(r, Exception))
                    self.logger.info(f"🧬 진화 라운드 완료: {successful_evolutions}/{len(evolution_tasks)} 성공")
                    
                    # 메모리 정리
                    import gc
                    gc.collect()
                
                # 다음 체크까지 대기
                await asyncio.sleep(check_interval)
                
        except asyncio.CancelledError:
            self.logger.info("🛑 지속적인 진화 프로세스 중단됨")
        except Exception as e:
            self.logger.error(f"❌ 지속적인 진화 프로세스 오류: {e}")
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """진화 시스템 상태 보고서"""
        try:
            report = {
                'total_agents': len(self.agents),
                'agent_types': {},
                'performance_summary': {},
                'evolution_statistics': {
                    'total_experiments': 0,
                    'successful_evolutions': 0,
                    'average_improvement': 0.0
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 에이전트 타입별 통계
            for agent_id, config in self.agents.items():
                agent_type = config.agent_type.value
                if agent_type not in report['agent_types']:
                    report['agent_types'][agent_type] = 0
                report['agent_types'][agent_type] += 1
                
                # 성능 요약
                avg_perf = self.get_average_performance(agent_id)
                trend = self.get_performance_trend(agent_id)
                
                report['performance_summary'][agent_id] = {
                    'average_performance': avg_perf,
                    'performance_trend': trend,
                    'total_records': len(self.performance_history.get(agent_id, []))
                }
            
            return report
        except Exception as e:
            self.logger.error(f"❌ 진화 보고서 생성 실패: {e}")
            return {'error': str(e)}

    async def intelligent_evolution_recommendation(self, agent_id: str) -> Dict[str, Any]:
        """지능형 진화 전략 추천 시스템"""
        try:
            if agent_id not in self.agents:
                return {"error": "에이전트를 찾을 수 없습니다"}
            
            config = self.agents[agent_id]
            performance_history = self.get_recent_performance(agent_id, window=20)
            
            recommendations = {
                "agent_id": agent_id,
                "current_performance": self.get_average_performance(agent_id),
                "performance_trend": self.get_performance_trend(agent_id),
                "recommended_strategies": [],
                "priority_actions": [],
                "expected_improvements": {},
                "risk_assessment": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 성능 분석 기반 추천
            avg_perf = recommendations["current_performance"]
            trend = recommendations["performance_trend"]
            
            # 1. 성능이 낮은 경우 (< 0.6)
            if avg_perf < 0.6:
                recommendations["recommended_strategies"].extend([
                    {
                        "strategy": "aggressive_parameter_mutation",
                        "reason": "낮은 성능으로 인한 대폭적인 매개변수 변경 필요",
                        "priority": "HIGH",
                        "expected_improvement": 0.15
                    },
                    {
                        "strategy": "memory_expansion",
                        "reason": "메모리 부족으로 인한 학습 제한 가능성",
                        "priority": "HIGH", 
                        "expected_improvement": 0.10
                    },
                    {
                        "strategy": "cross_agent_knowledge_transfer",
                        "reason": "고성능 에이전트로부터 지식 전수 필요",
                        "priority": "MEDIUM",
                        "expected_improvement": 0.12
                    }
                ])
                recommendations["priority_actions"].append("긴급 성능 개선 필요")
            
            # 2. 성능 정체 상태 (trend ≈ 0)
            elif abs(trend) < 0.001:
                recommendations["recommended_strategies"].extend([
                    {
                        "strategy": "exploration_rate_boost",
                        "reason": "성능 정체로 인한 탐험율 증가 필요",
                        "priority": "MEDIUM",
                        "expected_improvement": 0.08
                    },
                    {
                        "strategy": "architecture_diversification",
                        "reason": "구조적 변화를 통한 돌파구 모색",
                        "priority": "MEDIUM",
                        "expected_improvement": 0.06
                    }
                ])
                recommendations["priority_actions"].append("탐험적 변화 시도")
            
            # 3. 성능 감소 추세 (trend < 0)
            elif trend < -0.005:
                recommendations["recommended_strategies"].extend([
                    {
                        "strategy": "learning_rate_reduction",
                        "reason": "과학습 방지를 위한 학습률 감소",
                        "priority": "HIGH",
                        "expected_improvement": 0.05
                    },
                    {
                        "strategy": "stability_enhancement",
                        "reason": "성능 안정화를 위한 매개변수 조정",
                        "priority": "HIGH",
                        "expected_improvement": 0.07
                    }
                ])
                recommendations["priority_actions"].append("성능 안정화 우선")
            
            # 4. 좋은 성능 유지 중 (> 0.8)
            elif avg_perf > 0.8:
                recommendations["recommended_strategies"].extend([
                    {
                        "strategy": "fine_tuning_optimization",
                        "reason": "미세 조정을 통한 최적화",
                        "priority": "LOW",
                        "expected_improvement": 0.03
                    },
                    {
                        "strategy": "efficiency_improvement",
                        "reason": "성능 유지하며 효율성 향상",
                        "priority": "LOW",
                        "expected_improvement": 0.02
                    }
                ])
                recommendations["priority_actions"].append("현재 성능 유지하며 최적화")
            
            # 에이전트 타입별 특화 추천
            type_specific = await self._get_type_specific_recommendations(config)
            recommendations["recommended_strategies"].extend(type_specific)
            
            # 위험도 평가
            recommendations["risk_assessment"] = self._assess_evolution_risks(config, performance_history)
            
            # 예상 개선 효과 계산
            for strategy in recommendations["recommended_strategies"]:
                strategy_name = strategy["strategy"]
                recommendations["expected_improvements"][strategy_name] = strategy.get("expected_improvement", 0.05)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ 진화 추천 시스템 오류: {e}")
            return {"error": str(e)}

    async def generate_evolution_roadmap(self, agent_id: str, target_performance: float = 0.9, timeframe_days: int = 30) -> Dict[str, Any]:
        """에이전트 진화 로드맵 생성"""
        try:
            if agent_id not in self.agents:
                return {"error": "에이전트를 찾을 수 없습니다"}
            
            current_performance = self.get_average_performance(agent_id)
            performance_gap = target_performance - current_performance
            
            if performance_gap <= 0:
                return {
                    "message": "이미 목표 성능에 도달했거나 초과했습니다",
                    "current_performance": current_performance,
                    "target_performance": target_performance
                }
            
            # 단계별 진화 계획 수립
            roadmap = {
                "agent_id": agent_id,
                "current_performance": current_performance,
                "target_performance": target_performance,
                "performance_gap": performance_gap,
                "timeframe_days": timeframe_days,
                "evolution_phases": [],
                "estimated_completion": None,
                "success_probability": 0.0,
                "required_resources": {},
                "risk_mitigation": []
            }
            
            # 성능 격차에 따른 단계 수 결정
            if performance_gap > 0.3:
                num_phases = 4
            elif performance_gap > 0.15:
                num_phases = 3
            else:
                num_phases = 2
            
            improvement_per_phase = performance_gap / num_phases
            days_per_phase = timeframe_days // num_phases
            
            # 각 단계별 전략 계획
            for phase in range(num_phases):
                phase_start_perf = current_performance + (improvement_per_phase * phase)
                phase_target_perf = current_performance + (improvement_per_phase * (phase + 1))
                
                phase_strategies = self._plan_phase_strategies(phase, phase_start_perf, phase_target_perf)
                
                roadmap["evolution_phases"].append({
                    "phase": phase + 1,
                    "duration_days": days_per_phase,
                    "start_performance": phase_start_perf,
                    "target_performance": phase_target_perf,
                    "improvement_target": improvement_per_phase,
                    "strategies": phase_strategies,
                    "success_criteria": self._define_success_criteria(phase_target_perf),
                    "checkpoints": self._define_checkpoints(days_per_phase)
                })
            
            # 성공 확률 추정
            roadmap["success_probability"] = self._estimate_success_probability(
                current_performance, target_performance, timeframe_days
            )
            
            # 완료 예상 일자
            roadmap["estimated_completion"] = (
                datetime.now() + timedelta(days=timeframe_days)
            ).isoformat()
            
            # 필요 리소스 계산
            roadmap["required_resources"] = {
                "computational_cycles": num_phases * 1000,
                "evolution_experiments": num_phases * 5,
                "monitoring_frequency": "daily",
                "human_intervention_probability": 0.2 if performance_gap > 0.2 else 0.1
            }
            
            # 위험 완화 전략
            roadmap["risk_mitigation"] = self._generate_risk_mitigation_strategies(performance_gap)
            
            return roadmap
            
        except Exception as e:
            self.logger.error(f"❌ 진화 로드맵 생성 실패: {e}")
            return {"error": str(e)}

    def _plan_phase_strategies(self, phase: int, start_perf: float, target_perf: float) -> List[Dict]:
        """단계별 진화 전략 계획"""
        strategies = []
        
        if phase == 0:  # 초기 단계 - 기본 최적화
            strategies.extend([
                {
                    "name": "parameter_fine_tuning",
                    "description": "기본 매개변수 미세 조정",
                    "priority": "HIGH",
                    "estimated_duration": "3-5 days",
                    "expected_improvement": 0.05
                },
                {
                    "name": "memory_optimization",
                    "description": "메모리 크기 및 구조 최적화",
                    "priority": "MEDIUM",
                    "estimated_duration": "2-3 days",
                    "expected_improvement": 0.03
                }
            ])
        
        elif phase == 1:  # 중간 단계 - 구조적 개선
            strategies.extend([
                {
                    "name": "architecture_enhancement",
                    "description": "아키텍처 구조 개선",
                    "priority": "HIGH",
                    "estimated_duration": "5-7 days",
                    "expected_improvement": 0.08
                },
                {
                    "name": "learning_rate_adaptation",
                    "description": "적응형 학습률 적용",
                    "priority": "MEDIUM",
                    "estimated_duration": "2-4 days",
                    "expected_improvement": 0.04
                }
            ])
        
        elif phase == 2:  # 고급 단계 - 지식 전이
            strategies.extend([
                {
                    "name": "cross_agent_knowledge_transfer",
                    "description": "고성능 에이전트로부터 지식 전이",
                    "priority": "HIGH",
                    "estimated_duration": "4-6 days",
                    "expected_improvement": 0.07
                },
                {
                    "name": "ensemble_integration",
                    "description": "앙상블 방법론 적용",
                    "priority": "MEDIUM",
                    "estimated_duration": "3-5 days",
                    "expected_improvement": 0.05
                }
            ])
        
        else:  # 최종 단계 - 고급 최적화
            strategies.extend([
                {
                    "name": "advanced_optimization",
                    "description": "고급 최적화 알고리즘 적용",
                    "priority": "HIGH",
                    "estimated_duration": "5-8 days",
                    "expected_improvement": 0.06
                },
                {
                    "name": "performance_stabilization",
                    "description": "성능 안정화 및 미세 조정",
                    "priority": "HIGH",
                    "estimated_duration": "3-4 days",
                    "expected_improvement": 0.03
                }
            ])
        
        return strategies

    def _define_success_criteria(self, target_performance: float) -> Dict[str, Any]:
        """성공 기준 정의"""
        return {
            "primary_metrics": {
                "overall_performance": target_performance,
                "performance_stability": 0.05,  # 표준편차 임계값
                "improvement_consistency": 0.8   # 개선 일관성
            },
            "secondary_metrics": {
                "response_time_improvement": 0.1,
                "error_rate_reduction": 0.05,
                "user_satisfaction_increase": 0.1
            },
            "validation_tests": [
                "performance_regression_test",
                "stress_test",
                "edge_case_handling_test"
            ]
        }

    def _define_checkpoints(self, phase_duration: int) -> List[Dict]:
        """체크포인트 정의"""
        checkpoints = []
        
        # 25%, 50%, 75%, 100% 지점에 체크포인트 설정
        for percentage in [25, 50, 75, 100]:
            checkpoint_day = int(phase_duration * percentage / 100)
            checkpoints.append({
                "day": checkpoint_day,
                "milestone": f"{percentage}% 완료",
                "required_actions": [
                    "성능 측정 및 기록",
                    "진화 전략 효과 평가",
                    "필요시 전략 조정"
                ],
                "success_threshold": 0.6 + (0.4 * percentage / 100)
            })
        
        return checkpoints

    def _estimate_success_probability(self, current_perf: float, target_perf: float, days: int) -> float:
        """성공 확률 추정"""
        try:
            performance_gap = target_perf - current_perf
            
            # 기본 확률 (성능 격차에 반비례)
            base_probability = max(0.1, 1.0 - (performance_gap * 2))
            
            # 시간 요소 (충분한 시간이 있으면 확률 증가)
            time_factor = min(1.0, days / 30.0)
            
            # 현재 성능 수준 요소 (높은 성능에서 시작하면 더 어려움)
            performance_factor = 1.0 - (current_perf * 0.3)
            
            # 종합 확률 계산
            final_probability = base_probability * time_factor * performance_factor
            return max(0.1, min(0.95, final_probability))
            
        except Exception:
            return 0.5  # 기본값

    def _generate_risk_mitigation_strategies(self, performance_gap: float) -> List[Dict]:
        """위험 완화 전략 생성"""
        strategies = []
        
        if performance_gap > 0.3:
            strategies.extend([
                {
                    "risk": "대폭적인 성능 개선 실패",
                    "mitigation": "단계적 접근 및 중간 목표 설정",
                    "contingency": "보수적 전략으로 전환"
                },
                {
                    "risk": "시스템 불안정성",
                    "mitigation": "빈번한 백업 및 롤백 지점 설정",
                    "contingency": "이전 안정 버전으로 복구"
                }
            ])
        
        strategies.extend([
            {
                "risk": "성능 정체",
                "mitigation": "다양한 진화 전략 병렬 시도",
                "contingency": "앙상블 방법론 적용"
            },
            {
                "risk": "과적합",
                "mitigation": "정규화 및 일반화 기법 적용",
                "contingency": "학습률 감소 및 드롭아웃 적용"
            }
        ])
        
        return strategies

    def cleanup_memory(self):
        """메모리 정리 및 최적화"""
        try:
            # 성능 히스토리 제한 (최근 20개만 유지 - 메모리 최적화)
            for agent_id in list(self.performance_history.keys()):
                if len(self.performance_history[agent_id]) > 20:
                    self.performance_history[agent_id] = self.performance_history[agent_id][-20:]
            
            # 데이터베이스 연결 정리
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 오래된 성능 로그 삭제 (30일 이상)
                cursor.execute('''
                    DELETE FROM performance_logs 
                    WHERE timestamp < datetime('now', '-30 days')
                ''')
                
                # 데이터베이스 최적화
                cursor.execute('VACUUM')
                conn.commit()
                conn.close()
                
            except Exception as e:
                self.logger.warning(f"⚠️ 데이터베이스 정리 실패: {e}")
            
            # Python 가비지 컬렉션 실행
            import gc
            gc.collect()
            
            self.logger.info("✅ 메모리 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 메모리 정리 실패: {e}")
    
    def check_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 상태 확인"""
        try:
            import psutil
            
            # CPU 및 메모리 정보
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            status = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "healthy": True,
                "warnings": []
            }
            
            # 경고 조건 확인
            if memory.percent > 85:
                status["healthy"] = False
                status["warnings"].append("높은 메모리 사용량")
            
            if cpu_percent > 90:
                status["healthy"] = False  
                status["warnings"].append("높은 CPU 사용량")
            
            if disk.percent > 90:
                status["warnings"].append("디스크 공간 부족")
            
            return status
            
        except ImportError:
            return {"error": "psutil 라이브러리가 필요합니다"}
        except Exception as e:
            return {"error": str(e)}

    async def safe_evolve_agent(self, agent_id: str, target_improvement: float = 0.1) -> Optional[AgentConfig]:
        """안전한 에이전트 진화 (리소스 체크 포함)"""
        try:
            # 시스템 리소스 확인
            system_status = self.check_system_resources()
            if not system_status.get("healthy", True):
                self.logger.warning(f"⚠️ 시스템 리소스 부족으로 진화 연기: {system_status.get('warnings', [])}")
                return None
            
            # 기존 진화 메서드 호출
            result = await self.evolve_agent(agent_id, target_improvement)
            
            # 진화 후 메모리 정리
            if result:
                self.cleanup_memory()
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 안전한 에이전트 진화 실패: {e}")
            return None

    async def _get_type_specific_recommendations(self, config: AgentConfig) -> List[Dict[str, Any]]:
        """에이전트 타입별 특화 추천"""
        recommendations = []
        
        if config.agent_type == AgentType.LEARNING:
            recommendations.append({
                "strategy": "curriculum_learning",
                "reason": "학습 에이전트를 위한 단계적 학습 과정 적용",
                "priority": "MEDIUM",
                "expected_improvement": 0.06
            })
        
        elif config.agent_type == AgentType.GOAL_ORIENTED:
            recommendations.append({
                "strategy": "goal_decomposition",
                "reason": "목표 지향 에이전트를 위한 목표 분해 전략",
                "priority": "HIGH",
                "expected_improvement": 0.08
            })
        
        elif config.agent_type == AgentType.CONVERSATIONAL:
            recommendations.append({
                "strategy": "context_window_expansion",
                "reason": "대화 에이전트를 위한 컨텍스트 확장",
                "priority": "MEDIUM",
                "expected_improvement": 0.05
            })
        
        elif config.agent_type == AgentType.CODE_GENERATION:
            recommendations.append({
                "strategy": "test_coverage_increase",
                "reason": "코드 생성 에이전트를 위한 테스트 커버리지 향상",
                "priority": "HIGH",
                "expected_improvement": 0.07
            })
        
        elif config.agent_type == AgentType.DATA_ANALYSIS:
            recommendations.append({
                "strategy": "feature_engineering",
                "reason": "데이터 분석 에이전트를 위한 피처 엔지니어링",
                "priority": "HIGH",
                "expected_improvement": 0.09
            })
        
        return recommendations

    def _assess_evolution_risks(self, config: AgentConfig, performance_history: List[PerformanceMetrics]) -> Dict[str, Any]:
        """진화 위험도 평가"""
        risks = {
            "performance_risk": "LOW",
            "stability_risk": "LOW", 
            "resource_risk": "LOW",
            "overall_risk": "LOW",
            "risk_factors": []
        }
        
        try:
            # 성능 위험도
            if len(performance_history) > 0:
                recent_scores = [p.overall_score() for p in performance_history[-5:]]
                avg_score = np.mean(recent_scores) if recent_scores else 0.5
                
                if avg_score < 0.6:
                    risks["performance_risk"] = "HIGH"
                    risks["risk_factors"].append("낮은 성능 수준")
                elif avg_score < 0.75:
                    risks["performance_risk"] = "MEDIUM"
            
            # 안정성 위험도
            if len(performance_history) > 3:
                score_std = np.std([p.overall_score() for p in performance_history[-10:]])
                if score_std > 0.15:
                    risks["stability_risk"] = "HIGH"
                    risks["risk_factors"].append("높은 성능 변동성")
                elif score_std > 0.08:
                    risks["stability_risk"] = "MEDIUM"
            
            # 리소스 위험도
            if config.memory_size > 5000:
                risks["resource_risk"] = "MEDIUM"
                risks["risk_factors"].append("높은 메모리 사용량")
            
            # 전체 위험도 계산
            risk_levels = [risks["performance_risk"], risks["stability_risk"], risks["resource_risk"]]
            if "HIGH" in risk_levels:
                risks["overall_risk"] = "HIGH"
            elif "MEDIUM" in risk_levels:
                risks["overall_risk"] = "MEDIUM"
            
            # 실시간 알림 전송
            if risks["overall_risk"] == "HIGH":
                try:
                    send_agent_alert(
                        f"에이전트 {config.agent_id} 고위험 진화 상황",
                        f"위험 요소: {', '.join(risks['risk_factors'])}",
                        AlertLevel.CRITICAL
                    )
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"위험도 평가 실패: {e}")
        
        return risks

# 전역 인스턴스
_evolution_system = None

def get_evolution_system() -> AgentEvolutionSystem:
    """에이전트 진화 시스템 싱글톤 인스턴스"""
    global _evolution_system
    if _evolution_system is None:
        _evolution_system = AgentEvolutionSystem()
    return _evolution_system

# 사용 예시 및 테스트
async def main():
    """메인 실행 함수 (메모리 최적화)"""
    evolution_system = get_evolution_system()
    
    print("🤖 AI 에이전트 진화 시스템 테스트")
    print("=" * 50)
    
    # 시스템 리소스 상태 확인
    system_status = evolution_system.check_system_resources()
    print(f"💻 시스템 상태: {'건강함' if system_status.get('healthy', True) else '주의 필요'}")
    print(f"   메모리 사용률: {system_status.get('memory_percent', 0):.1f}%")
    print(f"   CPU 사용률: {system_status.get('cpu_percent', 0):.1f}%")
    
    if not system_status.get("healthy", True):
        print("⚠️ 시스템 리소스가 부족합니다. 간단한 테스트만 실행합니다.")
        
        # 메모리 정리 먼저 실행
        evolution_system.cleanup_memory()
        
        # 단일 에이전트만 테스트
        test_agent = AgentConfig(
            agent_id="test_agent_001",
            agent_type=AgentType.LEARNING,
            learning_rate=0.1,
            memory_size=500,  # 메모리 크기 감소
            exploration_rate=0.1
        )
        
        success = evolution_system.register_agent(test_agent)
        print(f"{'✅' if success else '❌'} 테스트 에이전트 등록")
        
        # 간단한 성능 데이터 생성
        for i in range(5):  # 5개만 생성
            metrics = PerformanceMetrics(
                accuracy=random.uniform(0.6, 0.8),
                response_time=random.uniform(0.1, 1.0),
                user_satisfaction=random.uniform(0.7, 0.9),
                task_completion_rate=random.uniform(0.8, 0.95),
                error_rate=random.uniform(0.01, 0.05),
                learning_speed=random.uniform(0.5, 0.8),
                adaptability=random.uniform(0.6, 0.8)
            )
            evolution_system.record_performance(test_agent.agent_id, metrics)
        
        print("✅ 간단한 테스트 완료")
        return
    
    # 정상적인 테스트 진행
    test_agents = [
        AgentConfig(
            agent_id="learning_agent_001",
            agent_type=AgentType.LEARNING,
            learning_rate=0.1,
            memory_size=1000,
            exploration_rate=0.1,
            specialized_params={"hidden_layers": 3, "batch_size": 32}
        ),
        AgentConfig(
            agent_id="goal_agent_001", 
            agent_type=AgentType.GOAL_ORIENTED,
            learning_rate=0.05,
            memory_size=500,
            exploration_rate=0.2,
            specialized_params={"goal_threshold": 0.8, "planning_depth": 5}
        )
    ]
    
    # 에이전트 등록
    for agent in test_agents:
        success = evolution_system.register_agent(agent)
        print(f"{'✅' if success else '❌'} 에이전트 '{agent.agent_id}' 등록")
    
    # 시뮬레이션 성능 데이터 생성 (제한적)
    print("\n📊 성능 데이터 시뮬레이션 중...")
    for agent in test_agents:
        for i in range(10):  # 20개에서 10개로 감소
            metrics = PerformanceMetrics(
                accuracy=random.uniform(0.6, 0.95),
                response_time=random.uniform(0.1, 2.0),
                user_satisfaction=random.uniform(0.7, 0.9),
                task_completion_rate=random.uniform(0.8, 0.98),
                error_rate=random.uniform(0.01, 0.1),
                learning_speed=random.uniform(0.5, 0.9),
                adaptability=random.uniform(0.6, 0.85)
            )
            evolution_system.record_performance(agent.agent_id, metrics)
    
    # 에이전트 진화 테스트 (안전 모드)
    print("\n🧬 에이전트 진화 테스트...")
    for agent in test_agents:
        print(f"\n진화 테스트: {agent.agent_id}")
        evolved_config = await evolution_system.safe_evolve_agent(agent.agent_id)
        if evolved_config:
            print(f"✅ 진화 성공: {evolved_config.agent_id}")
        else:
            print("ℹ️ 진화에서 개선 사항 없음")
    
    # 메모리 정리
    evolution_system.cleanup_memory()
    
    # 진화 보고서 출력 (간소화)
    print("\n📈 진화 시스템 보고서:")
    report = evolution_system.get_evolution_report()
    simplified_report = {
        'total_agents': report.get('total_agents', 0),
        'agent_types': report.get('agent_types', {}),
        'timestamp': report.get('timestamp', '')
    }
    print(json.dumps(simplified_report, indent=2, ensure_ascii=False))
    
    print("\n🎯 에이전트 진화 시스템 테스트 완료!")
    print("💡 메모리 사용량을 모니터링하여 안정성을 개선했습니다.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
