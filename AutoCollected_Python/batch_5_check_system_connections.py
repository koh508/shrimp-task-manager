#!/usr/bin/env python3
"""
🔍 시스템 연결 상태 최종 확인 스크립트
"""
import requests
import json
from datetime import datetime

def check_system_connections():
    print("🔍 시스템 연결 상태 최종 확인")
    print("=" * 50)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "port_8001": False,
        "port_8002": False,
        "gemini_api": False,
        "shrimp_mcp": False,
        "autonomous_evolution": False
    }
    
    # 포트 8001 확인 (메인 Vibe AI 시스템)
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 포트 8001 (Vibe AI): 정상 연결")
            print(f"   - 서비스: {data.get('service')}")
            print(f"   - 버전: {data.get('version')}")
            print(f"   - 지능 레벨: {data.get('intelligence_level')}")
            print(f"   - 디버그 상태: {data.get('debug_status')}")
            results["port_8001"] = True
        else:
            print(f"❌ 포트 8001: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 포트 8001 연결 실패: {e}")
    
    print()
    
    # 포트 8002 확인 (자율 진화 시스템)
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 포트 8002 (자율 진화): 정상 연결")
            print(f"   - 서비스: {data.get('service')}")
            print(f"   - 버전: {data.get('version')}")
            print(f"   - 지능 레벨: {data.get('intelligence_level')}")
            print(f"   - 자율 학습: {data.get('autonomous_learning')}")
            print(f"   - Ollama 대체: {data.get('replaces_ollama')}")
            results["port_8002"] = True
        else:
            print(f"❌ 포트 8002: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 포트 8002 연결 실패: {e}")
    
    print()
    
    # 시스템 상태 상세 확인
    try:
        response = requests.get("http://localhost:8001/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            connections = data.get('connections', {})
            print("🔗 연결 상태 상세:")
            print(f"   - Gemini API: {'✅ 연결됨' if connections.get('gemini') else '❌ 연결 안됨'}")
            print(f"   - Shrimp MCP: {'✅ 연결됨' if connections.get('shrimp_mcp') else '❌ 연결 안됨'}")
            print(f"   - 시스템 상태: {connections.get('system_health', 'unknown')}")
            
            results["gemini_api"] = connections.get('gemini', False)
            results["shrimp_mcp"] = connections.get('shrimp_mcp', False)
    except Exception as e:
        print(f"❌ 상태 API 확인 실패: {e}")
    
    print()
    
    # 자율 진화 상태 확인
    try:
        response = requests.get("http://localhost:8002/api/evolution-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("🧠 자율 진화 상태:")
            print(f"   - 진화 횟수: {data.get('evolution_count')}")
            print(f"   - 활성 에이전트: {data.get('active_agents')}")
            print(f"   - 마지막 진화: {data.get('last_evolution', '')[:19]}")
            print(f"   - 자율 학습: {'✅ 활성화' if data.get('autonomous_learning') else '❌ 비활성화'}")
            
            results["autonomous_evolution"] = data.get('autonomous_learning', False)
    except Exception as e:
        print(f"❌ 진화 상태 확인 실패: {e}")
    
    print()
    print("📊 최종 연결 상태 요약:")
    print("=" * 30)
    
    all_good = True
    for service, status in results.items():
        if service != "timestamp":
            symbol = "✅" if status else "❌"
            service_name = {
                "port_8001": "메인 Vibe AI 시스템 (8001)",
                "port_8002": "자율 진화 시스템 (8002)",
                "gemini_api": "Gemini API",
                "shrimp_mcp": "Shrimp MCP",
                "autonomous_evolution": "자율 진화"
            }.get(service, service)
            print(f"{symbol} {service_name}")
            if not status:
                all_good = False
    
    print()
    if all_good:
        print("🎉 모든 시스템이 정상적으로 연결되어 있습니다!")
        print("🌐 접속 URL:")
        print("   - 메인 대시보드: http://localhost:8001")
        print("   - 자율 진화: http://localhost:8002")
    else:
        print("⚠️  일부 시스템에 문제가 있습니다. 위의 상태를 확인해주세요.")
    
    # 결과를 JSON 파일로 저장
    with open("d:/system_connection_status.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return all_good

if __name__ == "__main__":
    check_system_connections()
