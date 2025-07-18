#!/usr/bin/env python3
"""
진화 상태 체크 스크립트
"""
import sqlite3
from datetime import datetime

def check_evolution_status():
    try:
        conn = sqlite3.connect('d:/shrimp_evolution.db')
        cursor = conn.cursor()
        
        # 진화 로그 수 확인
        cursor.execute('SELECT COUNT(*) FROM evolution_log')
        log_count = cursor.fetchone()[0]
        print(f"✅ 진화 로그 총 수: {log_count}")
        
        # 최근 진화 기록 확인
        cursor.execute('''
            SELECT timestamp, intelligence_level, evolution_type 
            FROM evolution_log 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        
        recent_logs = cursor.fetchall()
        print("\n📊 최근 진화 기록:")
        for i, (timestamp, intelligence, evo_type) in enumerate(recent_logs, 1):
            print(f"{i}. {timestamp[:19]} | 지능: {intelligence:.2f} | 타입: {evo_type}")
        
        conn.close()
        
        if log_count > 0:
            print("\n🔄 자율 진화 시스템이 정상적으로 작동하고 있습니다!")
            return True
        else:
            print("\n⚠️  진화 로그가 없습니다. 시스템이 시작된 지 얼마 안 된 것 같습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 진화 상태 확인 오류: {e}")
        return False

if __name__ == "__main__":
    check_evolution_status()
