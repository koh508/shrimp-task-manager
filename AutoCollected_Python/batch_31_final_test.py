print("🎯 Final Test: 수정된 시스템 테스트")

try:
    # 원본 파일에서 클래스 import
    import sys
    sys.path.append('.')
    from advanced_agent_evolution_system import AgentType, AgentConfig
    
    print("✅ 클래스 import 성공")
    
    # 간단한 에이전트 생성
    test_agent = AgentConfig(
        agent_id="final_test",
        agent_type=AgentType.LEARNING
    )
    
    print(f"✅ 에이전트 생성 성공: {test_agent.agent_id}")
    print("🎯 모든 테스트 통과!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print("추가 수정이 필요합니다.")
