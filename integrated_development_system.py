#!/usr/bin/env python3
"""
통합 개발 시스템 (수정 버전)
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class IntegratedDevelopmentSystem:
    """통합 개발 시스템 관리자"""
    
    def __init__(self, data_file: str = 'integrated_system_data.json'):
        self.data_file = data_file
        self.goals = []
        self.load_data()

    def load_data(self):
        """데이터 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.goals = data.get('goals', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"데이터 로드 오류: {e}")
                self.goals = []

    def save_data(self):
        """데이터 저장"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({'goals': self.goals}, f, indent=2)
        except IOError as e:
            print(f"데이터 저장 오류: {e}")

    def add_goal(self, title: str, description: str, priority: str = 'medium'):
        """학습 목표 추가"""
        goal = {
            'id': len(self.goals) + 1,
            'title': title,
            'description': description,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        self.goals.append(goal)
        self.save_data()
        print(f"✅ 목표 추가 완료: '{title}'")

    def list_goals(self):
        """목표 목록 조회"""
        if not self.goals:
            print("🎯 등록된 목표가 없습니다.")
            return

        print("\n📋 학습 목표 목록:")
        for goal in sorted(self.goals, key=lambda x: x['id']):
            status_icon = {
                'pending': '⏳',
                'in_progress': '🏃‍♂️',
                'completed': '✅'
            }.get(goal['status'], '❓')
            
            print(f"  {status_icon} [{goal['id']}] {goal['title']} ({goal['priority']}) - {goal['progress']}% ")

    def update_goal_progress(self, goal_id: int, progress: int):
        """목표 진행률 업데이트"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['progress'] = max(0, min(100, progress))
                if goal['progress'] == 100:
                    goal['status'] = 'completed'
                elif goal['progress'] > 0:
                    goal['status'] = 'in_progress'
                else:
                    goal['status'] = 'pending'
                self.save_data()
                print(f"✅ 목표 업데이트 완료: [{goal_id}] {goal['progress']}%")
                return
        print(f"❌ ID가 {goal_id}인 목표를 찾을 수 없습니다.")

    def get_status_report(self):
        """상태 리포트 조회"""
        total = len(self.goals)
        if total == 0:
            print("📊 목표 없음")
            return

        completed = sum(1 for g in self.goals if g['status'] == 'completed')
        in_progress = sum(1 for g in self.goals if g['status'] == 'in_progress')
        pending = total - completed - in_progress
        
        print("\n📊 목표 상태 리포트:")
        print(f"  - 총 목표: {total}")
        print(f"  - ✅ 완료: {completed}")
        print(f"  - 🏃‍♂️ 진행 중: {in_progress}")
        print(f"  - ⏳ 대기: {pending}")
        print(f"  - 전체 진행률: {completed/total*100:.1f}%" if total > 0 else "0.0%")

def main():
    """메인 실행 함수"""
    ids = IntegratedDevelopmentSystem()
    
    print("🚀 통합 개발 시스템")
    print("=" * 40)

    while True:
        print("\n📋 메뉴:")
        print("1. 목표 추가")
        print("2. 목표 목록 보기")
        print("3. 목표 진행률 업데이트")
        print("4. 상태 리포트")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-4): ").strip()

        if choice == '0':
            print("👋 시스템 종료")
            break
        elif choice == '1':
            title = input("목표 제목: ")
            desc = input("설명: ")
            priority = input("중요도 (high, medium, low): ").lower()
            ids.add_goal(title, desc, priority if priority in ['high', 'medium', 'low'] else 'medium')
        elif choice == '2':
            ids.list_goals()
        elif choice == '3':
            try:
                goal_id = int(input("목표 ID: "))
                progress = int(input("진행률 (0-100): "))
                ids.update_goal_progress(goal_id, progress)
            except ValueError:
                print("❌ 잘못된 숫자 형식입니다.")
        elif choice == '4':
            ids.get_status_report()
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
