#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 에이전트 시스템 재시작 테스트
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.getcwd())

def test_imports():
    """필수 라이브러리 import 테스트"""
    print("🔍 Step 3: 라이브러리 import 테스트")
    
    try:
        import numpy as np
        print("✅ numpy 로드 성공")
    except ImportError as e:
        print(f"❌ numpy 로드 실패: {e}")
        return False
    
    try:
        import psutil
        memory_percent = psutil.virtual_memory().percent
        print(f"✅ psutil 로드 성공 (메모리: {memory_percent:.1f}%)")
    except ImportError as e:
        print(f"❌ psutil 로드 실패: {e}")
        return False
    
    try:
        from advanced_agent_evolution_system import AgentEvolutionSystem, AgentConfig, AgentType, PerformanceMetrics
        print("✅ 에이전트 시스템 클래스 로드 성공")
    except ImportError as e:
        print(f"❌ 에이전트 시스템 로드 실패: {e}")
        return False
    
    return True

def test_system_creation():
    """에이전트 시스템 생성 테스트"""
    print("\n🔧 Step 4: 에이전트 시스템 생성 테스트")
    
    try:
        from advanced_agent_evolution_system import get_evolution_system
        system = get_evolution_system()
        print("✅ 에이전트 진화 시스템 생성 성공")
        return system
    except Exception as e:
        print(f"❌ 에이전트 시스템 생성 실패: {e}")
        return None

def test_basic_agent():
    """기본 에이전트 생성 및 등록 테스트"""
    print("\n🤖 Step 5: 기본 에이전트 테스트")
    
    try:
        from advanced_agent_evolution_system import get_evolution_system, AgentConfig, AgentType
        
        system = get_evolution_system()
        
        # 간단한 테스트 에이전트 생성
        test_agent = AgentConfig(
            agent_id="restart_test_001",
            agent_type=AgentType.LEARNING,
            learning_rate=0.1,
            memory_size=500,
            exploration_rate=0.1
        )
        
        # 에이전트 등록
        success = system.register_agent(test_agent)
        if success:
            print("✅ 테스트 에이전트 등록 성공")
            return system, test_agent
        else:
            print("❌ 테스트 에이전트 등록 실패")
            return None, None
            
    except Exception as e:
        print(f"❌ 기본 에이전트 테스트 실패: {e}")
        return None, None

async def test_system_functionality():
    """시스템 기능 테스트"""
    print("\n⚡ Step 6: 시스템 기능 테스트")
    
    try:
        from advanced_agent_evolution_system import get_evolution_system, PerformanceMetrics
        import random
        
        system = get_evolution_system()
        
        # 등록된 에이전트 확인
        if not system.agents:
            print("❌ 등록된 에이전트가 없습니다")
            return False
        
        # 첫 번째 에이전트 선택
        agent_id = list(system.agents.keys())[0]
        print(f"📊 에이전트 '{agent_id}' 성능 테스트 중...")
        
        # 성능 데이터 생성
        for i in range(3):
            metrics = PerformanceMetrics(
                accuracy=random.uniform(0.7, 0.9),
                response_time=random.uniform(0.1, 1.0),
                user_satisfaction=random.uniform(0.8, 0.95),
                task_completion_rate=random.uniform(0.85, 0.98),
                error_rate=random.uniform(0.01, 0.05),
                learning_speed=random.uniform(0.6, 0.85),
                adaptability=random.uniform(0.65, 0.8)
            )
            
            success = system.record_performance(agent_id, metrics)
            if success:
                print(f"  ✅ 성능 기록 {i+1}/3 성공")
            else:
                print(f"  ❌ 성능 기록 {i+1}/3 실패")
        
        # 평균 성능 확인
        avg_performance = system.get_average_performance(agent_id)
        print(f"📈 평균 성능: {avg_performance:.3f}")
        
        # 진화 테스트
        print("🧬 에이전트 진화 테스트...")
        evolved_config = await system.safe_evolve_agent(agent_id)
        
        if evolved_config:
            print(f"✅ 에이전트 진화 성공: {evolved_config.agent_id}")
        else:
            print("ℹ️ 진화에서 개선 사항 없음 (정상)")
        
        return True
        
    except Exception as e:
        print(f"❌ 시스템 기능 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    print("🚀 에이전트 시스템 재시작 테스트 시작")
    print("=" * 50)
    
    # Step 3: Import 테스트
    if not test_imports():
        print("❌ 라이브러리 로드 실패 - 종료")
        return
    
    # Step 4: 시스템 생성 테스트
    system = test_system_creation()
    if not system:
        print("❌ 시스템 생성 실패 - 종료")
        return
    
    # Step 5: 기본 에이전트 테스트
    system, test_agent = test_basic_agent()
    if not system or not test_agent:
        print("❌ 에이전트 생성 실패 - 종료")
        return
    
    # Step 6: 시스템 기능 테스트
    success = await test_system_functionality()
    
    if success:
        print("\n🎯 모든 테스트 통과!")
        print("✅ 에이전트 시스템이 정상적으로 작동합니다")
        
        # 시스템 상태 보고서
        report = system.get_evolution_report()
        print(f"\n📊 시스템 상태:")
        print(f"   총 에이전트 수: {report.get('total_agents', 0)}")
        print(f"   에이전트 타입: {report.get('agent_types', {})}")
        
    else:
        print("\n❌ 일부 테스트 실패")
        print("⚠️ 시스템에 문제가 있을 수 있습니다")

if __name__ == "__main__":
    asyncio.run(main())
