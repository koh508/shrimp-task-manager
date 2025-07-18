#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Evolution Algorithm Optimizer v1.0
====================================
- 진화 알고리즘 자동 최적화
- 유전자 알고리즘 자동 생성
- 변이 및 교배 전략 최적화
- 실시간 성능 모니터링 및 조정
"""

import asyncio
import sqlite3
import json
import random
import numpy as np
import psutil
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evolution_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class GeneticOperator:
    """유전자 연산자"""
    operator_id: str
    operator_type: str  # 'crossover', 'mutation', 'selection'
    parameters: Dict[str, float]
    performance_score: float
    usage_count: int
    created_at: str

@dataclass
class EvolutionStrategy:
    """진화 전략"""
    strategy_id: str
    population_size: int
    mutation_rate: float
    crossover_rate: float
    selection_method: str
    genetic_operators: List[GeneticOperator]
    fitness_history: List[float]
    generation_count: int
    effectiveness_score: float

@dataclass
class EvolutionaryIndividual:
    """진화 개체"""
    individual_id: str
    genome: List[float]
    fitness_score: float
    generation: int
    parent_ids: List[str]
    mutation_history: List[str]
    age: int

class EvolutionAlgorithmOptimizer:
    """진화 알고리즘 최적화기"""
    
    def __init__(self):
        self.db_path = "evolution_optimizer.db"
        self.strategies = {}
        self.populations = {}
        self.genetic_operators = self._initialize_genetic_operators()
        self.fitness_functions = self._initialize_fitness_functions()
        self.system_resources = self._get_system_resources()
        self.setup_database()
        
    def _get_system_resources(self):
        """시스템 리소스 감지"""
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total // (1024**3)
        return {
            'cpu_count': cpu_count,
            'memory_gb': memory_gb,
            'max_population_size': min(1000, max(50, cpu_count * 20)),
            'evolution_intensity': 'high' if memory_gb >= 16 else 'medium' if memory_gb >= 8 else 'low'
        }
        
    def _initialize_genetic_operators(self):
        """유전자 연산자 초기화"""
        operators = []
        
        # 교배 연산자들
        crossover_ops = [
            {'type': 'single_point', 'params': {'point_ratio': 0.5}},
            {'type': 'two_point', 'params': {'point1_ratio': 0.3, 'point2_ratio': 0.7}},
            {'type': 'uniform', 'params': {'probability': 0.5}},
            {'type': 'arithmetic', 'params': {'alpha': 0.5}},
            {'type': 'blend_alpha', 'params': {'alpha': 0.3}}
        ]
        
        # 변이 연산자들
        mutation_ops = [
            {'type': 'gaussian', 'params': {'sigma': 0.1}},
            {'type': 'uniform', 'params': {'range': 0.2}},
            {'type': 'polynomial', 'params': {'eta': 20}},
            {'type': 'non_uniform', 'params': {'b': 5}},
            {'type': 'adaptive', 'params': {'initial_rate': 0.1}}
        ]
        
        # 선택 연산자들
        selection_ops = [
            {'type': 'tournament', 'params': {'tournament_size': 3}},
            {'type': 'roulette_wheel', 'params': {}},
            {'type': 'rank_based', 'params': {'pressure': 1.5}},
            {'type': 'stochastic_universal', 'params': {}},
            {'type': 'elitist', 'params': {'elite_ratio': 0.1}}
        ]
        
        # 연산자 객체 생성
        for i, op_data in enumerate(crossover_ops + mutation_ops + selection_ops):
            op_type = 'crossover' if i < len(crossover_ops) else ('mutation' if i < len(crossover_ops) + len(mutation_ops) else 'selection')
            
            operator = GeneticOperator(
                operator_id=f"{op_type}_{op_data['type']}_{random.randint(1000, 9999)}",
                operator_type=op_type,
                parameters=op_data['params'],
                performance_score=random.uniform(0.3, 0.7),
                usage_count=0,
                created_at=datetime.now().isoformat()
            )
            operators.append(operator)
            
        return operators
        
    def _initialize_fitness_functions(self):
        """적합도 함수들 초기화"""
        return {
            'sphere': lambda x: -sum(xi**2 for xi in x),  # 최소화 문제
            'rosenbrock': lambda x: -sum(100*(x[i+1] - x[i]**2)**2 + (1-x[i])**2 for i in range(len(x)-1)),
            'rastrigin': lambda x: -10*len(x) - sum(xi**2 - 10*math.cos(2*math.pi*xi) for xi in x),
            'ackley': lambda x: -(-20*math.exp(-0.2*math.sqrt(sum(xi**2 for xi in x)/len(x))) - 
                                 math.exp(sum(math.cos(2*math.pi*xi) for xi in x)/len(x)) + 20 + math.e),
            'schwefel': lambda x: -418.9829*len(x) + sum(xi*math.sin(math.sqrt(abs(xi))) for xi in x),
            'custom_multi_modal': lambda x: -(sum(math.sin(xi)*math.exp(-xi**2) for xi in x) + 
                                            sum(math.cos(xi*2)*math.exp(-abs(xi)) for xi in x))
        }
        
    def setup_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_strategies (
                strategy_id TEXT PRIMARY KEY,
                population_size INTEGER,
                mutation_rate REAL,
                crossover_rate REAL,
                selection_method TEXT,
                genetic_operators TEXT,
                fitness_history TEXT,
                generation_count INTEGER,
                effectiveness_score REAL,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolutionary_populations (
                population_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                generation INTEGER,
                individuals TEXT,
                avg_fitness REAL,
                best_fitness REAL,
                diversity_score REAL,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genetic_operators (
                operator_id TEXT PRIMARY KEY,
                operator_type TEXT,
                parameters TEXT,
                performance_score REAL,
                usage_count INTEGER,
                success_rate REAL,
                created_at TEXT,
                last_used TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_sessions (
                session_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                fitness_function TEXT,
                initial_fitness REAL,
                final_fitness REAL,
                generations_elapsed INTEGER,
                improvement_rate REAL,
                session_duration REAL,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ 진화 최적화 데이터베이스 초기화 완료")
        
    def create_evolution_strategy(self, fitness_function: str = 'sphere') -> EvolutionStrategy:
        """새로운 진화 전략 생성"""
        strategy_id = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(10000, 99999)}"
        
        # 시스템 리소스에 따른 모집단 크기 조정
        base_population = {
            'high': random.randint(200, 500),
            'medium': random.randint(100, 300),
            'low': random.randint(50, 150)
        }[self.system_resources['evolution_intensity']]
        
        # 유전자 연산자 선택 (각 타입에서 랜덤 선택)
        crossover_ops = [op for op in self.genetic_operators if op.operator_type == 'crossover']
        mutation_ops = [op for op in self.genetic_operators if op.operator_type == 'mutation']
        selection_ops = [op for op in self.genetic_operators if op.operator_type == 'selection']
        
        selected_operators = [
            random.choice(crossover_ops),
            random.choice(mutation_ops),
            random.choice(selection_ops)
        ]
        
        strategy = EvolutionStrategy(
            strategy_id=strategy_id,
            population_size=base_population,
            mutation_rate=random.uniform(0.01, 0.1),
            crossover_rate=random.uniform(0.6, 0.9),
            selection_method=selected_operators[2].operator_id,
            genetic_operators=selected_operators,
            fitness_history=[],
            generation_count=0,
            effectiveness_score=0.0
        )
        
        self.strategies[strategy_id] = strategy
        self._save_strategy(strategy)
        
        logger.info(f"🧬 새 진화 전략 생성: {strategy_id} (모집단: {base_population}, 적합도: {fitness_function})")
        return strategy
        
    def _save_strategy(self, strategy: EvolutionStrategy):
        """진화 전략 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO evolution_strategies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            strategy.strategy_id,
            strategy.population_size,
            strategy.mutation_rate,
            strategy.crossover_rate,
            strategy.selection_method,
            json.dumps([asdict(op) for op in strategy.genetic_operators]),
            json.dumps(strategy.fitness_history),
            strategy.generation_count,
            strategy.effectiveness_score,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    def initialize_population(self, strategy: EvolutionStrategy, genome_length: int = 10) -> List[EvolutionaryIndividual]:
        """초기 모집단 생성"""
        population = []
        
        for i in range(strategy.population_size):
            individual = EvolutionaryIndividual(
                individual_id=f"ind_{strategy.strategy_id}_{i:06d}",
                genome=[random.uniform(-5.0, 5.0) for _ in range(genome_length)],
                fitness_score=0.0,
                generation=0,
                parent_ids=[],
                mutation_history=[],
                age=0
            )
            population.append(individual)
            
        return population
        
    def evaluate_fitness(self, population: List[EvolutionaryIndividual], fitness_function: str):
        """적합도 평가"""
        fitness_func = self.fitness_functions[fitness_function]
        
        for individual in population:
            individual.fitness_score = fitness_func(individual.genome)
            
    def selection(self, population: List[EvolutionaryIndividual], strategy: EvolutionStrategy, num_parents: int) -> List[EvolutionaryIndividual]:
        """선택 연산"""
        selection_op = next(op for op in strategy.genetic_operators if op.operator_type == 'selection')
        
        # 토너먼트 선택 구현
        if 'tournament' in selection_op.operator_id:
            tournament_size = selection_op.parameters.get('tournament_size', 3)
            parents = []
            
            for _ in range(num_parents):
                tournament = random.sample(population, min(tournament_size, len(population)))
                winner = max(tournament, key=lambda x: x.fitness_score)
                parents.append(winner)
                
            return parents
            
        # 룰렛 휠 선택
        elif 'roulette' in selection_op.operator_id:
            # 음수 적합도를 양수로 변환
            min_fitness = min(ind.fitness_score for ind in population)
            adjusted_fitness = [ind.fitness_score - min_fitness + 1 for ind in population]
            total_fitness = sum(adjusted_fitness)
            
            parents = []
            for _ in range(num_parents):
                pick = random.uniform(0, total_fitness)
                current = 0
                for i, fitness in enumerate(adjusted_fitness):
                    current += fitness
                    if current >= pick:
                        parents.append(population[i])
                        break
                        
            return parents
            
        # 기본: 상위 개체 선택
        else:
            sorted_pop = sorted(population, key=lambda x: x.fitness_score, reverse=True)
            return sorted_pop[:num_parents]
            
    def crossover(self, parent1: EvolutionaryIndividual, parent2: EvolutionaryIndividual, 
                 strategy: EvolutionStrategy) -> Tuple[EvolutionaryIndividual, EvolutionaryIndividual]:
        """교배 연산"""
        crossover_op = next(op for op in strategy.genetic_operators if op.operator_type == 'crossover')
        
        genome_length = len(parent1.genome)
        
        # 단일점 교배
        if 'single_point' in crossover_op.operator_id:
            point = int(genome_length * crossover_op.parameters.get('point_ratio', 0.5))
            
            child1_genome = parent1.genome[:point] + parent2.genome[point:]
            child2_genome = parent2.genome[:point] + parent1.genome[point:]
            
        # 균등 교배
        elif 'uniform' in crossover_op.operator_id:
            prob = crossover_op.parameters.get('probability', 0.5)
            
            child1_genome = []
            child2_genome = []
            
            for i in range(genome_length):
                if random.random() < prob:
                    child1_genome.append(parent1.genome[i])
                    child2_genome.append(parent2.genome[i])
                else:
                    child1_genome.append(parent2.genome[i])
                    child2_genome.append(parent1.genome[i])
                    
        # 산술 교배
        else:  # arithmetic crossover
            alpha = crossover_op.parameters.get('alpha', 0.5)
            
            child1_genome = [alpha * p1 + (1-alpha) * p2 for p1, p2 in zip(parent1.genome, parent2.genome)]
            child2_genome = [(1-alpha) * p1 + alpha * p2 for p1, p2 in zip(parent1.genome, parent2.genome)]
            
        # 자식 개체 생성
        child1 = EvolutionaryIndividual(
            individual_id=f"child_{datetime.now().strftime('%H%M%S')}_{random.randint(1000, 9999)}",
            genome=child1_genome,
            fitness_score=0.0,
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.individual_id, parent2.individual_id],
            mutation_history=[],
            age=0
        )
        
        child2 = EvolutionaryIndividual(
            individual_id=f"child_{datetime.now().strftime('%H%M%S')}_{random.randint(1000, 9999)}",
            genome=child2_genome,
            fitness_score=0.0,
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.individual_id, parent2.individual_id],
            mutation_history=[],
            age=0
        )
        
        return child1, child2
        
    def mutation(self, individual: EvolutionaryIndividual, strategy: EvolutionStrategy):
        """변이 연산"""
        mutation_op = next(op for op in strategy.genetic_operators if op.operator_type == 'mutation')
        
        # 가우시안 변이
        if 'gaussian' in mutation_op.operator_id:
            sigma = mutation_op.parameters.get('sigma', 0.1)
            
            for i in range(len(individual.genome)):
                if random.random() < strategy.mutation_rate:
                    individual.genome[i] += random.gauss(0, sigma)
                    individual.mutation_history.append(f"gaussian_{i}")
                    
        # 균등 변이
        elif 'uniform' in mutation_op.operator_id:
            range_val = mutation_op.parameters.get('range', 0.2)
            
            for i in range(len(individual.genome)):
                if random.random() < strategy.mutation_rate:
                    individual.genome[i] += random.uniform(-range_val, range_val)
                    individual.mutation_history.append(f"uniform_{i}")
                    
        # 적응적 변이
        else:  # adaptive mutation
            base_rate = mutation_op.parameters.get('initial_rate', 0.1)
            adapted_rate = base_rate / (1 + individual.age * 0.1)  # 나이에 따라 변이율 감소
            
            for i in range(len(individual.genome)):
                if random.random() < adapted_rate:
                    individual.genome[i] += random.gauss(0, adapted_rate)
                    individual.mutation_history.append(f"adaptive_{i}")
                    
    async def run_evolution_optimization(self, strategy: EvolutionStrategy, fitness_function: str, 
                                       max_generations: int = 100) -> Dict[str, Any]:
        """진화 최적화 실행"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        start_time = time.time()
        
        # 초기 모집단 생성
        population = self.initialize_population(strategy, genome_length=10)
        
        # 초기 적합도 평가
        self.evaluate_fitness(population, fitness_function)
        initial_fitness = max(ind.fitness_score for ind in population)
        
        best_fitness_history = []
        avg_fitness_history = []
        
        for generation in range(max_generations):
            # 적합도 통계
            fitness_scores = [ind.fitness_score for ind in population]
            best_fitness = max(fitness_scores)
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            
            best_fitness_history.append(best_fitness)
            avg_fitness_history.append(avg_fitness)
            
            # 새로운 세대 생성
            new_population = []
            
            # 엘리트 보존 (상위 10%)
            elite_count = max(1, int(0.1 * len(population)))
            elite = sorted(population, key=lambda x: x.fitness_score, reverse=True)[:elite_count]
            new_population.extend(elite)
            
            # 나머지 개체 생성
            while len(new_population) < strategy.population_size:
                # 부모 선택
                parents = self.selection(population, strategy, 2)
                
                # 교배
                if random.random() < strategy.crossover_rate:
                    child1, child2 = self.crossover(parents[0], parents[1], strategy)
                else:
                    child1, child2 = parents[0], parents[1]
                    
                # 변이
                self.mutation(child1, strategy)
                self.mutation(child2, strategy)
                
                # 나이 증가
                for ind in [child1, child2]:
                    ind.age += 1
                    
                new_population.extend([child1, child2])
                
            # 모집단 크기 조정
            population = new_population[:strategy.population_size]
            
            # 적합도 재평가
            self.evaluate_fitness(population, fitness_function)
            
            # 진행률 로깅 (10세대마다)
            if generation % 10 == 0:
                logger.info(f"🧬 세대 {generation}: 최고적합도={best_fitness:.4f}, 평균적합도={avg_fitness:.4f}")
                
            await asyncio.sleep(0.001)  # 비동기 처리
            
        # 최종 결과
        final_fitness_scores = [ind.fitness_score for ind in population]
        final_fitness = max(final_fitness_scores)
        improvement_rate = ((final_fitness - initial_fitness) / abs(initial_fitness)) * 100 if initial_fitness != 0 else 0
        
        session_duration = time.time() - start_time
        
        # 전략 효과성 업데이트
        strategy.fitness_history.extend(best_fitness_history)
        strategy.generation_count += max_generations
        strategy.effectiveness_score = improvement_rate
        
        # 결과 저장
        result = {
            'session_id': session_id,
            'strategy_id': strategy.strategy_id,
            'fitness_function': fitness_function,
            'initial_fitness': initial_fitness,
            'final_fitness': final_fitness,
            'improvement_rate': improvement_rate,
            'generations_elapsed': max_generations,
            'best_fitness_history': best_fitness_history,
            'avg_fitness_history': avg_fitness_history,
            'session_duration': session_duration,
            'population_diversity': np.std(final_fitness_scores)
        }
        
        self._save_optimization_session(result)
        self._save_strategy(strategy)
        
        logger.info(f"✅ 진화 최적화 완료: {session_id} | 개선율: {improvement_rate:.2f}%")
        return result
        
    def _save_optimization_session(self, session_data: Dict[str, Any]):
        """최적화 세션 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO optimization_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data['session_id'],
            session_data['strategy_id'],
            session_data['fitness_function'],
            session_data['initial_fitness'],
            session_data['final_fitness'],
            session_data['generations_elapsed'],
            session_data['improvement_rate'],
            session_data['session_duration'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    async def mass_evolution_optimization(self, num_strategies: int = None) -> Dict[str, Any]:
        """대규모 진화 최적화 실행"""
        if num_strategies is None:
            num_strategies = min(8, max(3, self.system_resources['cpu_count'] // 2))
            
        logger.info(f"🚀 대규모 진화 최적화 시작: {num_strategies}개 전략")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'num_strategies': num_strategies,
            'strategies_created': [],
            'optimization_sessions': [],
            'fitness_functions_tested': list(self.fitness_functions.keys()),
            'system_resources': self.system_resources
        }
        
        # 전략 생성 및 최적화 작업 준비
        optimization_tasks = []
        
        for i in range(num_strategies):
            fitness_func = list(self.fitness_functions.keys())[i % len(self.fitness_functions)]
            strategy = self.create_evolution_strategy(fitness_func)
            
            results['strategies_created'].append({
                'strategy_id': strategy.strategy_id,
                'population_size': strategy.population_size,
                'mutation_rate': strategy.mutation_rate,
                'crossover_rate': strategy.crossover_rate,
                'fitness_function': fitness_func
            })
            
            # 세대 수 조정 (시스템 리소스 기반)
            max_gens = {
                'high': 150,
                'medium': 100,
                'low': 50
            }[self.system_resources['evolution_intensity']]
            
            optimization_tasks.append(
                self.run_evolution_optimization(strategy, fitness_func, max_gens)
            )
            
        logger.info(f"✅ {num_strategies}개 진화 전략 생성 완료")
        
        # 병렬 최적화 실행
        session_results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        for result in session_results:
            if isinstance(result, dict):
                results['optimization_sessions'].append(result)
            else:
                logger.error(f"최적화 세션 오류: {result}")
                
        # 결과 분석
        if results['optimization_sessions']:
            improvements = [s['improvement_rate'] for s in results['optimization_sessions']]
            final_fitnesses = [s['final_fitness'] for s in results['optimization_sessions']]
            
            results['analysis'] = {
                'average_improvement': sum(improvements) / len(improvements),
                'max_improvement': max(improvements),
                'min_improvement': min(improvements),
                'best_final_fitness': max(final_fitnesses),
                'total_generations': sum(s['generations_elapsed'] for s in results['optimization_sessions']),
                'total_duration': sum(s['session_duration'] for s in results['optimization_sessions'])
            }
            
        results['end_time'] = datetime.now().isoformat()
        
        logger.info(f"🎉 대규모 진화 최적화 완료!")
        if 'analysis' in results:
            logger.info(f"📊 평균 개선율: {results['analysis']['average_improvement']:.2f}%")
            logger.info(f"🏆 최고 개선율: {results['analysis']['max_improvement']:.2f}%")
            logger.info(f"⚡ 최고 적합도: {results['analysis']['best_final_fitness']:.4f}")
            
        return results
        
    async def continuous_evolution_optimization(self, duration_hours: int = 24):
        """24시간 연속 진화 최적화"""
        logger.info(f"🌟 연속 진화 최적화 모드 시작 ({duration_hours}시간)")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        optimization_cycle = 0
        
        while datetime.now() < end_time:
            optimization_cycle += 1
            logger.info(f"🔄 최적화 사이클 {optimization_cycle} 실행 중...")
            
            # 새로운 진화 전략 생성 및 최적화
            fitness_func = random.choice(list(self.fitness_functions.keys()))
            strategy = self.create_evolution_strategy(fitness_func)
            
            # 짧은 최적화 세션 (연속 모드용)
            max_gens = random.randint(20, 50)
            await self.run_evolution_optimization(strategy, fitness_func, max_gens)
            
            # 기존 전략들 개선 (30% 확률)
            if self.strategies and random.random() < 0.3:
                existing_strategy = random.choice(list(self.strategies.values()))
                fitness_func = random.choice(list(self.fitness_functions.keys()))
                await self.run_evolution_optimization(existing_strategy, fitness_func, 30)
                
            # 진화 리포트 (50 사이클마다)
            if optimization_cycle % 50 == 0:
                await self.generate_evolution_report()
                
            await asyncio.sleep(10)  # 10초 대기
            
        logger.info(f"✨ 연속 진화 최적화 모드 완료 (총 {optimization_cycle} 사이클)")
        
    async def generate_evolution_report(self):
        """진화 최적화 리포트 생성"""
        if not self.strategies:
            return
            
        total_strategies = len(self.strategies)
        effectiveness_scores = [s.effectiveness_score for s in self.strategies.values()]
        total_generations = sum(s.generation_count for s in self.strategies.values())
        
        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
        max_effectiveness = max(effectiveness_scores) if effectiveness_scores else 0
        
        logger.info("📊 === 진화 알고리즘 최적화 리포트 ===")
        logger.info(f"   총 전략: {total_strategies}개")
        logger.info(f"   평균 효과성: {avg_effectiveness:.2f}%")
        logger.info(f"   최고 효과성: {max_effectiveness:.2f}%")
        logger.info(f"   총 진화 세대: {total_generations}")
        logger.info(f"   유전자 연산자: {len(self.genetic_operators)}개")
        logger.info("============================================")

async def main():
    """메인 실행 함수"""
    print("🧬 Evolution Algorithm Optimizer v1.0")
    print("=" * 60)
    
    # 시스템 초기화
    optimizer = EvolutionAlgorithmOptimizer()
    
    print(f"🖥️ 시스템 리소스: {optimizer.system_resources}")
    print(f"🧬 유전자 연산자: {len(optimizer.genetic_operators)}개")
    print(f"📊 적합도 함수: {len(optimizer.fitness_functions)}개")
    
    # 대규모 진화 최적화
    results = await optimizer.mass_evolution_optimization()
    
    print(f"\n✅ 초기 진화 최적화 완료!")
    print(f"🧬 생성된 전략: {results['num_strategies']}개")
    print(f"📊 최적화 세션: {len(results['optimization_sessions'])}개")
    if 'analysis' in results:
        print(f"📈 평균 개선율: {results['analysis']['average_improvement']:.2f}%")
        print(f"🏆 최고 개선율: {results['analysis']['max_improvement']:.2f}%")
        print(f"⚡ 최고 적합도: {results['analysis']['best_final_fitness']:.4f}")
    
    print("\n🌟 연속 진화 최적화 모드로 전환...")
    print("⏰ 24시간 자율 진화 시작")
    
    # 연속 진화 최적화 모드 시작
    await optimizer.continuous_evolution_optimization(duration_hours=24)

if __name__ == "__main__":
    asyncio.run(main())
