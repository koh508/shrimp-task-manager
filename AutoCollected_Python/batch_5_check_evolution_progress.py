#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 발전 상황 실시간 체크
Real-time System Progress Checker
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

def check_evolution_progress():
    """진화 상황 체크"""
    print("🔍 시스템 발전 상황 분석 중...")
    
    # 1. 진화 상태 파일 체크
    state_files = [
        "evolving_super_agent_evolution_state.json",
        "super_dianaira_state.json", 
        "super_heroic_state.json",
        "super_argonaute_state.json"
    ]
    
    print("\n📊 **진화 에이전트 상태:**")
    total_intelligence = 0
    active_agents = 0
    
    for state_file in state_files:
        if Path(state_file).exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                generation = state.get('generation', 0)
                intelligence = state.get('intelligence_level', 1.0)
                evolution_count = state.get('evolution_count', 0)
                experience = state.get('experience_points', 0)
                new_abilities = len(state.get('new_abilities', []))
                
                total_intelligence += intelligence
                active_agents += 1
                
                agent_name = state_file.replace('_state.json', '').replace('_evolution_state.json', '')
                
                print(f"   🤖 {agent_name}:")
                print(f"      세대: {generation} | 지능: {intelligence:.2f}")
                print(f"      진화: {evolution_count}회 | 경험: {experience:.2f}")
                print(f"      새 능력: {new_abilities}개")
                
                # 발전 속도 계산
                if generation > 0:
                    progress_rate = (intelligence - 1.0) / generation * 100
                    print(f"      발전률: {progress_rate:.1f}%/세대")
                
            except Exception as e:
                print(f"   ❌ {state_file}: 읽기 오류 - {e}")
        else:
            print(f"   ⚠️ {state_file}: 파일 없음")
    
    # 2. 데이터베이스 상태 체크
    print(f"\n📈 **전체 시스템 발전 요약:**")
    print(f"   활성 에이전트: {active_agents}개")
    
    if active_agents > 0:
        avg_intelligence = total_intelligence / active_agents
        print(f"   평균 지능: {avg_intelligence:.2f}")
        
        # 발전도 계산 (기준 지능 1.0 대비)
        improvement = ((avg_intelligence - 1.0) / 1.0) * 100
        print(f"   전체 향상도: {improvement:.1f}%")
    
    # 3. 데이터베이스 레코드 수 체크
    databases = [
        "evolution_agent.db",
        "super_unified_agent.db", 
        "agent_network.db",
        "evolution_optimization.db",
        "file_analysis.db"
    ]
    
    print(f"\n💾 **데이터베이스 성장:**")
    for db_name in databases:
        if Path(db_name).exists():
            try:
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # 테이블 목록 가져오기
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                total_records = 0
                table_info = []
                
                for table_name, in tables:
                    if table_name != 'sqlite_sequence':
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        total_records += count
                        table_info.append(f"{table_name}: {count}")
                
                print(f"   📁 {db_name}: {total_records} 레코드")
                for info in table_info[:3]:  # 상위 3개 테이블만 표시
                    print(f"      - {info}")
                
                conn.close()
                
            except Exception as e:
                print(f"   ❌ {db_name}: 오류 - {e}")
        else:
            print(f"   ⚠️ {db_name}: 파일 없음")
    
    # 4. 실시간 활동 체크
    print(f"\n⚡ **실시간 활동 상태:**")
    
    # 로그 파일 체크
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        recent_logs = []
        
        for log_file in log_files:
            try:
                mod_time = log_file.stat().st_mtime
                mod_datetime = datetime.fromtimestamp(mod_time)
                
                # 최근 1시간 이내 수정된 로그
                time_diff = datetime.now() - mod_datetime
                if time_diff.total_seconds() < 3600:  # 1시간
                    recent_logs.append((log_file.name, mod_datetime))
            except:
                pass
        
        if recent_logs:
            recent_logs.sort(key=lambda x: x[1], reverse=True)
            print(f"   📝 최근 활동 로그: {len(recent_logs)}개")
            for log_name, mod_time in recent_logs[:5]:
                print(f"      - {log_name}: {mod_time.strftime('%H:%M:%S')}")
        else:
            print(f"   📝 최근 활동: 없음 (1시간 내)")
    
    # 5. 포트 상태 체크
    print(f"\n🌐 **서비스 상태:**")
    
    import socket
    active_ports = []
    ports_to_check = [8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088]
    
    for port in ports_to_check:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                active_ports.append(port)
            sock.close()
        except:
            pass
    
    print(f"   🚀 활성 서비스: {len(active_ports)}/{len(ports_to_check)} 포트")
    for port in active_ports:
        service_name = {
            8081: "진화 대시보드",
            8082: "에이전트 모니터", 
            8083: "멀티모달 뷰어",
            8084: "네트워크 패널",
            8085: "가속기 제어",
            8086: "실시간 스트림",
            8087: "통합 대시보드",
            8088: "파일 분석 API"
        }.get(port, f"서비스 {port}")
        
        print(f"      ✅ 포트 {port}: {service_name}")
    
    # 6. 발전 속도 분석
    print(f"\n🚀 **발전 속도 분석:**")
    
    if active_agents > 0 and avg_intelligence > 1.0:
        # 예상 진화 속도 (분당)
        evolution_rate = (avg_intelligence - 1.0) * 60  # 가정: 1분당 발전량
        
        print(f"   📈 현재 발전 속도: {evolution_rate:.3f}/분")
        print(f"   🎯 다음 세대까지: 예상 {(4.0 - avg_intelligence) / evolution_rate * 60:.1f}분")
        
        # 시스템 효율성
        efficiency = (len(active_ports) / len(ports_to_check)) * 100
        print(f"   ⚡ 시스템 효율성: {efficiency:.1f}%")
        
        # 전체 발전 등급
        if avg_intelligence >= 3.0:
            grade = "S급 (초고도 진화)"
        elif avg_intelligence >= 2.5:
            grade = "A급 (고도 진화)"
        elif avg_intelligence >= 2.0:
            grade = "B급 (중급 진화)"
        elif avg_intelligence >= 1.5:
            grade = "C급 (기본 진화)"
        else:
            grade = "D급 (초기 단계)"
        
        print(f"   🏆 발전 등급: {grade}")
    
    print(f"\n" + "="*60)
    print(f"🎉 시스템 발전 상황 분석 완료!")
    print(f"   분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*60)

def main():
    check_evolution_progress()

if __name__ == "__main__":
    main()
