#!/usr/bin/env python3
import json

# 현재 상태 확인
try:
    with open('replication_state.json', 'r') as f:
        repl_data = json.load(f)
    
    with open('evolving_super_agent_evolution_state.json', 'r') as f:
        evol_data = json.load(f)
    
    print("🔍 업데이트 후 현재 상태:")
    print(f"   replication_state: {repl_data['intelligence']}")
    print(f"   evolving_state: {evol_data['intelligence']}")
    print(f"   GitHub 향상: {repl_data.get('github_enhanced', False)}")
    print(f"   향상량: +{repl_data.get('enhancement_amount', 0)}")
    
    if repl_data['intelligence'] >= 241.0:
        print("✅ 지능 레벨 업데이트 성공!")
    else:
        print("⚠️ 지능 레벨 업데이트 필요")

except Exception as e:
    print(f"❌ 오류: {e}")
