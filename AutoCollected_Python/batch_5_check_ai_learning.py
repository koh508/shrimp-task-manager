#!/usr/bin/env python3
"""
🤖 옵시디언 개인 AI 어시스턴트 학습 상태 확인
"""

import sqlite3
import json
from datetime import datetime

def check_learning_status():
    """AI 어시스턴트 학습 상태 확인"""
    try:
        # 데이터베이스 연결
        db = sqlite3.connect('personal_ai_assistant.db')
        cursor = db.cursor()
        
        print("🧠 옵시디언 개인 AI 어시스턴트 학습 상태 보고서")
        print("=" * 60)
        
        # 학습된 콘텐츠 조회
        cursor.execute('SELECT COUNT(*) FROM learned_content')
        content_count = cursor.fetchone()[0]
        print(f"📚 총 학습된 파일 수: {content_count}개")
        
        # 콘텐츠 타입별 분석
        cursor.execute('SELECT content_type, COUNT(*) FROM learned_content GROUP BY content_type')
        content_types = cursor.fetchall()
        print(f"\n📊 콘텐츠 타입별 분석:")
        for content_type, count in content_types:
            print(f"  • {content_type}: {count}개")
        
        # 사용자 프로필 조회
        cursor.execute('SELECT * FROM user_profile ORDER BY timestamp DESC LIMIT 1')
        profile_data = cursor.fetchone()
        if profile_data:
            profile_json = json.loads(profile_data[2])
            print(f"\n👤 개인 프로필 분석:")
            print(f"  🎯 발견된 관심사: {len(profile_json.get('interests', set()))}개")
            print(f"  📋 추출된 목표: {len(profile_json.get('goals', []))}개")
            print(f"  🔄 파악된 습관: {len(profile_json.get('habits', {}))}개")
            print(f"  🧠 지식 영역: {len(profile_json.get('knowledge_areas', set()))}개")
            print(f"  📊 학습 세션: {profile_data[3]}회")
            print(f"  🎚️ 적응 레벨: {profile_data[4]:.2f}")
            
            # 관심사 상위 10개 표시
            interests = list(profile_json.get('interests', set()))[:10]
            if interests:
                print(f"\n🎯 주요 관심사 (상위 10개):")
                for i, interest in enumerate(interests, 1):
                    print(f"  {i}. {interest}")
            
            # 지식 영역 상위 10개 표시
            knowledge_areas = list(profile_json.get('knowledge_areas', set()))[:10]
            if knowledge_areas:
                print(f"\n🧠 주요 지식 영역 (상위 10개):")
                for i, area in enumerate(knowledge_areas, 1):
                    print(f"  {i}. {area}")
        
        # 최근 학습한 내용 조회
        cursor.execute('''
            SELECT file_path, content_type, importance_score, timestamp
            FROM learned_content 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_content = cursor.fetchall()
        
        print(f"\n📖 최근 학습한 내용 (상위 10개):")
        for content in recent_content:
            filename = content[0].split('/')[-1] if '/' in content[0] else content[0].split('\\')[-1]
            print(f"  • {filename}")
            print(f"    타입: {content[1]} | 중요도: {content[2]:.2f} | 시간: {content[3]}")
        
        # 상호작용 히스토리 조회
        cursor.execute('SELECT COUNT(*) FROM interaction_history')
        interaction_count = cursor.fetchone()[0]
        print(f"\n💬 상호작용 히스토리: {interaction_count}건")
        
        print(f"\n✅ AI 어시스턴트가 성공적으로 당신의 노트를 학습했습니다!")
        print(f"✅ 개인화된 비서, 멘토, 동반자 역할을 수행할 준비가 완료되었습니다!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 상태 확인 중 오류: {e}")
        return False

if __name__ == "__main__":
    check_learning_status()
