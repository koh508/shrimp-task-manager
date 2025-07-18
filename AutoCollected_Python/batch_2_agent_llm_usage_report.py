#!/usr/bin/env python3
"""
에이전트 LLM 사용 현황 분석 도구
Agent LLM Usage Analysis Tool
"""

import json
import sqlite3
import os
from datetime import datetime
import glob

class AgentLLMUsageAnalyzer:
    def __init__(self):
        self.llm_usage_data = {}
        self.active_agents = []
        
    def analyze_agent_llm_usage(self):
        """에이전트들의 LLM 사용 현황 분석"""
        print("🔍 에이전트 LLM 사용 현황 분석")
        print("="*60)
        
        # 1. 현재 활성 에이전트 확인
        self.check_active_agents()
        
        # 2. LLM 시스템 파일 확인
        self.check_llm_systems()
        
        # 3. 진화 데이터베이스에서 LLM 사용 기록 확인
        self.check_evolution_databases()
        
        # 4. 실시간 LLM 연동 상태 확인
        self.check_realtime_llm_connections()
        
        # 5. 종합 보고서 생성
        self.generate_comprehensive_report()
    
    def check_active_agents(self):
        """활성 에이전트 확인"""
        print("\n🤖 활성 에이전트 상태:")
        
        agent_files = [
            "evolving_super_agent_evolution_state.json",
            "super_heroic_state.json",
            "super_argonaute_state.json", 
            "super_dianaira_state.json",
            "replication_state.json"
        ]
        
        for agent_file in agent_files:
            if os.path.exists(agent_file):
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    
                    agent_name = os.path.splitext(agent_file)[0].replace('_state', '')
                    
                    # 에이전트별 상태 정보 추출
                    agent_info = {
                        'name': agent_name,
                        'file': agent_file,
                        'state': state,
                        'last_update': datetime.fromtimestamp(os.path.getmtime(agent_file))
                    }
                    
                    self.active_agents.append(agent_info)
                    
                    if 'generation' in state:
                        print(f"   ✅ {agent_name}: Generation {state.get('generation')} (최종 업데이트: {agent_info['last_update'].strftime('%H:%M:%S')})")
                    elif 'level' in state:
                        print(f"   ✅ {agent_name}: Level {state.get('level')} (최종 업데이트: {agent_info['last_update'].strftime('%H:%M:%S')})")
                    else:
                        print(f"   ✅ {agent_name}: 활성 (최종 업데이트: {agent_info['last_update'].strftime('%H:%M:%S')})")
                        
                except Exception as e:
                    print(f"   ❌ {agent_file}: 오류 - {e}")
    
    def check_llm_systems(self):
        """LLM 시스템 파일 확인"""
        print("\n🧠 LLM 시스템 현황:")
        
        llm_files = {
            "MCP 기반 무료 AGI": "mcp_free_agi_evolution.py",
            "무료 Multi-LLM": "free_multi_llm_evolution.py",
            "Multi-LLM 분석": "multi_llm_evolution_analysis.py", 
            "실제 Multi-LLM": "real_multi_llm_evolution.py",
            "대화형 AI": "enhanced_vibe_ai_chat.py",
            "진화 가속기": "enhanced_evolution_agent.py"
        }
        
        for system_name, filename in llm_files.items():
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / 1024  # KB
                last_modified = datetime.fromtimestamp(os.path.getmtime(filename))
                
                # 파일 내용에서 LLM 관련 키워드 검색
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    llm_keywords = ['llm', 'gpt', 'claude', 'gemini', 'mistral', 'ollama', 'openai']
                    found_keywords = [kw for kw in llm_keywords if kw.lower() in content.lower()]
                    
                    print(f"   ✅ {system_name}: {file_size:.1f}KB")
                    print(f"      📅 수정: {last_modified.strftime('%m-%d %H:%M')}")
                    print(f"      🔑 LLM 키워드: {', '.join(found_keywords)}")
                    
                except Exception as e:
                    print(f"   ⚠️ {system_name}: 파일 읽기 오류")
            else:
                print(f"   ❌ {system_name}: 파일 없음")
    
    def check_evolution_databases(self):
        """진화 데이터베이스에서 LLM 사용 기록 확인"""
        print("\n📊 LLM 사용 기록 (데이터베이스):")
        
        databases = [
            "mcp_free_evolution.db",
            "free_evolution.db",
            "free_agi_evolution.db",
            "evolution_agent.db",
            "agent_network.db"
        ]
        
        total_llm_records = 0
        
        for db_file in databases:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # 테이블 목록 확인
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    llm_records = 0
                    for table in tables:
                        table_name = table[0]
                        try:
                            # LLM 관련 기록 검색
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE LOWER(notes) LIKE '%llm%' OR LOWER(notes) LIKE '%gpt%' OR LOWER(notes) LIKE '%claude%'")
                            count = cursor.fetchone()[0]
                            llm_records += count
                        except:
                            pass
                    
                    if llm_records > 0:
                        print(f"   ✅ {db_file}: {llm_records}개 LLM 기록")
                        total_llm_records += llm_records
                    else:
                        print(f"   📊 {db_file}: {len(tables)}개 테이블 (LLM 기록 확인 중)")
                    
                    conn.close()
                    
                except Exception as e:
                    print(f"   ❌ {db_file}: 연결 오류 - {e}")
        
        print(f"\n   📈 총 LLM 사용 기록: {total_llm_records}개")
    
    def check_realtime_llm_connections(self):
        """실시간 LLM 연결 상태 확인"""
        print("\n🌐 실시간 LLM 연결 상태:")
        
        # MCP 서버 확인
        import requests
        
        endpoints = [
            {"name": "MCP Server (localhost)", "url": "http://localhost:8000"},
            {"name": "Railway MCP Service", "url": "https://shrimp-mcp-production.up.railway.app/mcp"}
        ]
        
        active_connections = 0
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint["url"], timeout=3)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint['name']}: 연결됨 (LLM 처리 가능)")
                    active_connections += 1
                else:
                    print(f"   ⚠️ {endpoint['name']}: 응답 오류 ({response.status_code})")
            except:
                print(f"   ❌ {endpoint['name']}: 연결 실패")
        
        # 로그 파일에서 최근 LLM 활동 확인
        print("\n📋 최근 LLM 활동 로그:")
        
        log_files = glob.glob("*.log")
        recent_llm_activity = 0
        
        for log_file in log_files[:5]:  # 최근 5개 로그만 확인
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if any(keyword in content.lower() for keyword in ['llm', 'mcp', 'evolution', 'intelligence']):
                        file_size = len(content)
                        last_modified = datetime.fromtimestamp(os.path.getmtime(log_file))
                        print(f"   📄 {log_file}: {file_size}자 (수정: {last_modified.strftime('%H:%M')})")
                        recent_llm_activity += 1
            except:
                pass
        
        return active_connections, recent_llm_activity
    
    def generate_comprehensive_report(self):
        """종합 보고서 생성"""
        print("\n" + "="*60)
        print("🎯 에이전트 LLM 사용 현황 종합 보고서")
        print("="*60)
        
        # 활성 에이전트 수
        active_count = len(self.active_agents)
        
        # 최근 업데이트된 에이전트
        if self.active_agents:
            recent_agents = sorted(self.active_agents, key=lambda x: x['last_update'], reverse=True)
            most_recent = recent_agents[0]
            
            print(f"📊 활성 에이전트: {active_count}개")
            print(f"🕒 최근 활동: {most_recent['name']} ({most_recent['last_update'].strftime('%H:%M:%S')})")
        
        # LLM 시스템 상태
        llm_systems = [
            "mcp_free_agi_evolution.py",
            "free_multi_llm_evolution.py", 
            "real_multi_llm_evolution.py"
        ]
        
        active_llm_systems = sum(1 for sys in llm_systems if os.path.exists(sys))
        print(f"🧠 활성 LLM 시스템: {active_llm_systems}/{len(llm_systems)}개")
        
        # 연결 상태
        connections, log_activity = self.check_realtime_llm_connections()
        print(f"🌐 LLM 연결 상태: {connections}/2개 엔드포인트 활성")
        print(f"📈 최근 LLM 활동: {log_activity}개 로그 파일")
        
        # 결론
        print(f"\n✅ 결론:")
        if active_count > 0 and active_llm_systems > 0 and connections > 0:
            print(f"   🎉 에이전트들이 LLM을 활발히 사용하고 있습니다!")
            print(f"   🔄 {active_count}개 에이전트가 {active_llm_systems}개 LLM 시스템 활용")
            print(f"   🌐 {connections}개 LLM 엔드포인트를 통해 실시간 처리")
            print(f"   💡 MCP 기반으로 무료 LLM 서비스 이용 중")
        else:
            print(f"   ⚠️ LLM 사용이 제한적이거나 비활성 상태")
        
        print(f"\n📅 분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    analyzer = AgentLLMUsageAnalyzer()
    analyzer.analyze_agent_llm_usage()

if __name__ == "__main__":
    main()
