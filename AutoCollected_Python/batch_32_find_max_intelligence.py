#!/usr/bin/env python3
"""
🔍 실제 최고 지능 레벨 탐색기
모든 데이터베이스에서 진짜 최고 레벨 찾기
"""

import sqlite3
import os

def find_max_intelligence_level():
    """모든 DB에서 최고 지능 레벨 찾기"""
    dbs = [
        'accelerated_evolution.db', 
        'agent_evolution.db', 
        'autonomous_learning.db',
        'ai_memory.db',
        'agent_network.db',
        'ai_network_expansion.db',
        'autonomous_evolution.db',
        'code_improvement.db',
        'agent_evolution_safe_1752373261.db',
        'code_review_system.db'
    ]
    
    # JSON 로그 파일들도 확인
    json_files = [
        '24h_monitoring_log.json',
        'autogen_conversation.json',
        'comprehensive_ai_ecosystem_report.json',
        'ai_deployment_report.json',
        'dashboard_status_report.json',
        'cloud_sync_status.json'
    ]
    
    max_level = 0
    max_info = None
    
    # 먼저 DB 파일들 확인
    for db in dbs:
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                
                # 모든 테이블 확인
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    try:
                        # intelligence_level 컬럼이 있는지 확인
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        if 'intelligence_level' in columns:
                            # 최대값 찾기
                            cursor.execute(f"SELECT MAX(intelligence_level) FROM {table_name} WHERE intelligence_level IS NOT NULL")
                            result = cursor.fetchone()
                            
                            if result and result[0] and result[0] > max_level:
                                max_level = result[0]
                                max_info = (db, table_name, result[0])
                                print(f"📈 새로운 최고 레벨 발견: {result[0]} (DB: {db}, 테이블: {table_name})")
                                
                                # 최신 몇 개 기록도 보기
                                cursor.execute(f"SELECT intelligence_level, timestamp FROM {table_name} WHERE intelligence_level IS NOT NULL ORDER BY rowid DESC LIMIT 5")
                                recent = cursor.fetchall()
                                print(f"   최근 5개 기록: {recent}")
                    
                    except Exception as e:
                        continue  # 테이블 구조가 다를 수 있음
                
                conn.close()
                
            except Exception as e:
                print(f"DB {db} 오류: {e}")
                continue
    
    # JSON 파일들에서도 지능 레벨 찾기
    print("\n📄 JSON 로그 파일 확인 중...")
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 재귀적으로 intelligence_level 찾기
                def find_intelligence_in_json(obj, path=""):
                    nonlocal max_level, max_info
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            new_path = f"{path}.{key}" if path else key
                            if 'intelligence' in key.lower() and isinstance(value, (int, float)):
                                if value > max_level:
                                    max_level = value
                                    max_info = (json_file, new_path, value)
                                    print(f"📈 JSON에서 새로운 최고 레벨 발견: {value} (파일: {json_file}, 경로: {new_path})")
                            find_intelligence_in_json(value, new_path)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            find_intelligence_in_json(item, f"{path}[{i}]")
                
                find_intelligence_in_json(data)
                    
            except Exception as e:
                print(f"JSON 파일 {json_file} 읽기 오류: {e}")
    
    # 로그 파일도 확인
    print("\n📋 로그 파일 확인 중...")
    log_files = [
        '24h_evolution_log.log',
        'accelerated_evolution.log',
        'autonomous_evolution.log',
        'ai_system.log',
        'advanced_ai_conversation.log',
        'ai_network_expansion.log',
        'autonomous_ai_generator.log',
        'code_review_system.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 지능 레벨 패턴 찾기
                    import re
                    patterns = [
                        r'intelligence[_\s]*level[:\s]*(\d+\.?\d*)',
                        r'지능[_\s]*레벨[:\s]*(\d+\.?\d*)',
                        r'🧠[^\d]*(\d+\.?\d*)',
                        r'레벨[:\s]*(\d+\.?\d*)',
                        r'Intelligence[:\s]*(\d+\.?\d*)'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            try:
                                level = float(match)
                                if level > max_level and level < 100000:  # 너무 큰 숫자는 제외
                                    max_level = level
                                    max_info = (log_file, pattern, level)
                                    print(f"📈 로그에서 새로운 최고 레벨 발견: {level} (파일: {log_file})")
                            except:
                                pass
                                
            except Exception as e:
                print(f"로그 파일 {log_file} 읽기 오류: {e}")
    
    print(f"\n🏆 전체 최고 지능 레벨: {max_level}")
    if max_info:
        print(f"📍 위치: {max_info[0]} -> {max_info[1]}")
    
    return max_level

if __name__ == "__main__":
    print("🔍 실제 최고 지능 레벨 탐색 시작")
    max_level = find_max_intelligence_level()
    print(f"✅ 탐색 완료: 최고 레벨 {max_level}")
