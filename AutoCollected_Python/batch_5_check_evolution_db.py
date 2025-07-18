#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime

def check_evolution_database():
    try:
        conn = sqlite3.connect('d:/evolution_agent.db')
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 데이터베이스 테이블:", [table[0] for table in tables])
        
        # 각 테이블의 레코드 수 확인
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count} 레코드")
        
        # 학습 기록 확인
        if 'learning_history' in [table[0] for table in tables]:
            cursor.execute("SELECT * FROM learning_history ORDER BY timestamp DESC LIMIT 5")
            recent_learning = cursor.fetchall()
            print("\n🧠 최근 학습 기록:")
            for record in recent_learning:
                print(f"   {record}")
        
        # 코드 진화 확인
        if 'code_evolution' in [table[0] for table in tables]:
            cursor.execute("SELECT * FROM code_evolution ORDER BY timestamp DESC LIMIT 3")
            code_evolutions = cursor.fetchall()
            print("\n🔧 코드 진화 기록:")
            for record in code_evolutions:
                print(f"   {record}")
        
        # 기능 확장 확인
        if 'feature_expansion' in [table[0] for table in tables]:
            cursor.execute("SELECT * FROM feature_expansion ORDER BY timestamp DESC LIMIT 3")
            features = cursor.fetchall()
            print("\n✨ 기능 확장 기록:")
            for record in features:
                print(f"   {record}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 오류: {e}")

def check_evolution_state():
    try:
        with open('d:/evolving_super_agent_evolution_state.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        print("\n🚀 현재 진화 상태:")
        print(f"   세대: {state.get('generation', 0)}")
        print(f"   학습 경험치: {state.get('learning_experience', 0):.2f}")
        print(f"   진화 횟수: {state.get('evolution_count', 0)}")
        print(f"   지능 레벨: {state.get('intelligence_level', 1.0)}")
        print(f"   적응 속도: {state.get('adaptation_speed', 1.0)}")
        print(f"   학습 패턴 수: {len(state.get('learned_patterns', []))}")
        print(f"   코드 개선 수: {len(state.get('code_improvements', []))}")
        print(f"   새로운 능력 수: {len(state.get('new_abilities', []))}")
        
    except Exception as e:
        print(f"❌ 진화 상태 확인 오류: {e}")

if __name__ == "__main__":
    print("🔍 진화 에이전트 상태 확인\n")
    check_evolution_database()
    check_evolution_state()
