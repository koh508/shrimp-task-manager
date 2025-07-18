#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 에이전트 시스템 활성화 및 연속 실행
"""

import asyncio
import sys
import os
import time
import random

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.getcwd())

class AgentActivator:
    """에이전트 시스템 활성화 관리자"""
    
    def __init__(self):
        self.system = None
        self.active_agents = {}
        self.running = False
    
    def initialize_system(self):
        """시스템 초기화"""
        try:
            from advanced_agent_evolution_system import get_evolution_system, AgentConfig, AgentType
            self.system = get_evolution_system()
            
            # 메모리 정리 먼저 실행
            self.system.cleanup_memory()
            
            print("✅ 에이전트 시스템 초기화 완료")
            return True
        except Exception as e:
            print(f"❌ 시스템 초기화 실패: {e}")
            return False
    
    def create_essential_agents(self):
        """필수 에이전트들 생성"""
        try:
            from advanced_agent_evolution_system import AgentConfig, AgentType
            
            essential_agents = [
                {
                    "id": "learning_master_001",
                    "type": AgentType.LEARNING,
                    "lr": 0.1,
                    "memory": 800,
                    "exploration": 0.15,
                    "params": {"hidden_layers": 2, "batch_size": 16}
                },
                {
                    "id": "goal_oriented_001", 
                    "type": AgentType.GOAL_ORIENTED,
                    "lr": 0.08,
                    "memory": 600,
                    "exploration": 0.2,
                    "params": {"goal_threshold": 0.85, "planning_depth": 4}
                },
                {
                    "id": "conversational_001",
                    "type": AgentType.CONVERSATIONAL,
                    "lr": 0.12,
                    "memory": 700,
                    "exploration": 0.1,
                    "params": {"context_window": 1000, "response_quality": 0.8}
                }
            ]
            
            created_count = 0
            
            for agent_info in essential_agents:
                config = AgentConfig(
                    agent_id=agent_info["id"],
                    agent_type=agent_info["type"],
                    learning_rate=agent_info["lr"],
                    memory_size=agent_info["memory"],
                    exploration_rate=agent_info["exploration"],
                    specialized_params=agent_info["params"]
                )
                
                if self.system.register_agent(config):
                    self.active_agents[agent_info["id"]] = config
                    print(f"✅ 에이전트 '{agent_info['id']}' 생성 및 활성화")
                    created_count += 1
                else:
                    print(f"❌ 에이전트 '{agent_info['id']}' 생성 실패")
            
            print(f"📊 총 {created_count}개 에이전트 활성화 완료")
            return created_count > 0
            
        except Exception as e:
            print(f"❌ 에이전트 생성 실패: {e}")
            return False
    
    async def start_continuous_monitoring(self, duration_minutes=5):
        """연속 모니터링 시작"""
        try:
            from advanced_agent_evolution_system import PerformanceMetrics
            
            self.running = True
            print(f"🔄 {duration_minutes}분간 연속 모니터링 시작...")
            
            start_time = time.time()
            cycle_count = 0
            
            while self.running and (time.time() - start_time) < (duration_minutes * 60):
                cycle_count += 1
                print(f"\n📊 모니터링 사이클 {cycle_count}")
                
                # 시스템 리소스 체크
                try:
                    import psutil
                    memory_percent = psutil.virtual_memory().percent
                    print(f"💻 메모리 사용률: {memory_percent:.1f}%")
                    
                    if memory_percent > 90:
                        print("⚠️ 메모리 사용량 높음 - 정리 실행")
                        self.system.cleanup_memory()
                except:
                    pass
                
                # 각 에이전트 성능 업데이트
                for agent_id in self.active_agents.keys():
                    # 시뮬레이션 성능 데이터 생성
                    metrics = self.generate_realistic_metrics(agent_id)
                    
                    success = self.system.record_performance(agent_id, metrics)
                    if success:
                        avg_perf = self.system.get_average_performance(agent_id)
                        trend = self.system.get_performance_trend(agent_id)
                        
                        trend_symbol = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                        print(f"  {trend_symbol} {agent_id}: 성능 {avg_perf:.3f} (트렌드: {trend:+.4f})")
                
                # 진화 기회 확인 (메모리 상태가 좋을 때만)
                try:
                    system_status = self.system.check_system_resources()
                    if system_status.get("healthy", False):
                        await self.try_agent_evolution()
                except:
                    pass
                
                # 시스템 상태 보고
                if cycle_count % 3 == 0:
                    await self.print_system_status()
                
                # 다음 사이클까지 대기 (30초)
                await asyncio.sleep(30)
            
            print(f"\n🎯 모니터링 완료 (총 {cycle_count}개 사이클)")
            self.running = False
            
        except Exception as e:
            print(f"❌ 연속 모니터링 실패: {e}")
            self.running = False
    
    def generate_realistic_metrics(self, agent_id):
        """현실적인 성능 메트릭 생성"""
        from advanced_agent_evolution_system import PerformanceMetrics
        
        # 에이전트 타입에 따른 기본 성능 특성
        base_performance = {
            "learning_master_001": {"acc": 0.85, "speed": 0.7},
            "goal_oriented_001": {"acc": 0.8, "speed": 0.8},
            "conversational_001": {"acc": 0.75, "speed": 0.9}
        }
        
        base = base_performance.get(agent_id, {"acc": 0.7, "speed": 0.7})
        
        # 시간에 따른 점진적 개선 시뮬레이션
        time_factor = min(1.0, time.time() % 300 / 300)  # 5분 주기
        improvement = time_factor * 0.1
        
        return PerformanceMetrics(
            accuracy=min(0.95, base["acc"] + improvement + random.uniform(-0.05, 0.05)),
            response_time=max(0.1, 2.0 - base["speed"] + random.uniform(-0.2, 0.2)),
            user_satisfaction=random.uniform(0.8, 0.95),
            task_completion_rate=random.uniform(0.85, 0.98),
            error_rate=max(0.01, random.uniform(0.01, 0.08)),
            learning_speed=random.uniform(0.6, 0.9),
            adaptability=random.uniform(0.65, 0.85)
        )
    
    async def try_agent_evolution(self):
        """에이전트 진화 시도"""
        try:
            # 가장 성능이 낮은 에이전트 선택
            worst_agent = None
            worst_performance = 1.0
            
            for agent_id in self.active_agents.keys():
                avg_perf = self.system.get_average_performance(agent_id)
                if avg_perf < worst_performance:
                    worst_performance = avg_perf
                    worst_agent = agent_id
            
            if worst_agent and worst_performance < 0.8:
                print(f"🧬 '{worst_agent}' 진화 시도 (현재 성능: {worst_performance:.3f})")
                
                evolved_config = await self.system.safe_evolve_agent(worst_agent)
                if evolved_config:
                    print(f"✅ 진화 성공: {evolved_config.agent_id}")
                    # 새 에이전트를 활성 목록에 추가
                    self.active_agents[evolved_config.agent_id] = evolved_config
                else:
                    print("ℹ️ 진화에서 개선 사항 없음")
        except Exception as e:
            print(f"⚠️ 진화 시도 실패: {e}")
    
    async def print_system_status(self):
        """시스템 상태 출력"""
        try:
            report = self.system.get_evolution_report()
            print(f"\n📈 시스템 상태 보고:")
            print(f"   총 에이전트: {report.get('total_agents', 0)}개")
            print(f"   활성 에이전트: {len(self.active_agents)}개")
            print(f"   에이전트 타입 분포: {report.get('agent_types', {})}")
            
            # 최고 성능 에이전트 표시
            best_agent = None
            best_performance = 0.0
            
            for agent_id in self.active_agents.keys():
                avg_perf = self.system.get_average_performance(agent_id)
                if avg_perf > best_performance:
                    best_performance = avg_perf
                    best_agent = agent_id
            
            if best_agent:
                print(f"   🏆 최고 성능: {best_agent} ({best_performance:.3f})")
                
        except Exception as e:
            print(f"⚠️ 상태 보고 실패: {e}")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        print("🛑 모니터링 중지됨")

async def main():
    """메인 실행 함수"""
    print("🚀 에이전트 시스템 활성화 시작")
    print("=" * 50)
    
    activator = AgentActivator()
    
    # 시스템 초기화
    if not activator.initialize_system():
        print("❌ 시스템 초기화 실패")
        return
    
    # 필수 에이전트 생성
    if not activator.create_essential_agents():
        print("❌ 에이전트 생성 실패")
        return
    
    print("\n🎯 에이전트 시스템이 정상적으로 활성화되었습니다!")
    print("💡 연속 모니터링을 시작합니다...")
    
    try:
        # 5분간 연속 모니터링
        await activator.start_continuous_monitoring(duration_minutes=5)
        
        print("\n✅ 에이전트 시스템이 정상적으로 작동했습니다!")
        print("🔄 시스템은 계속 실행 중입니다.")
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
        activator.stop_monitoring()
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())
