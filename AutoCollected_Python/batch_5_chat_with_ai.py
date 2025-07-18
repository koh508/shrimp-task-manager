#!/usr/bin/env python3
"""
🤖 옵시디언 개인 AI 어시스턴트와 대화하기
"""

import sqlite3
import json
from datetime import datetime
import random

class PersonalAIChat:
    def __init__(self):
        self.db = sqlite3.connect('personal_ai_assistant.db')
        self.cursor = self.db.cursor()
        self.load_user_profile()
    
    def load_user_profile(self):
        """사용자 프로필 로드"""
        try:
            self.cursor.execute('SELECT * FROM user_profile ORDER BY timestamp DESC LIMIT 1')
            profile_data = self.cursor.fetchone()
            if profile_data:
                self.profile = json.loads(profile_data[2])
                self.learning_sessions = profile_data[3]
                self.adaptation_level = profile_data[4]
            else:
                self.profile = {}
                self.learning_sessions = 0
                self.adaptation_level = 1.0
        except Exception as e:
            print(f"프로필 로드 오류: {e}")
            self.profile = {}
    
    def get_interests_list(self):
        """관심사 목록을 리스트로 변환"""
        interests = self.profile.get('interests', set())
        if isinstance(interests, str):
            # JSON string인 경우 파싱
            try:
                interests = json.loads(interests.replace("'", '"'))
            except:
                interests = []
        elif isinstance(interests, set):
            interests = list(interests)
        return interests[:20]  # 상위 20개만
    
    def get_knowledge_areas_list(self):
        """지식 영역 목록을 리스트로 변환"""
        knowledge = self.profile.get('knowledge_areas', set())
        if isinstance(knowledge, str):
            try:
                knowledge = json.loads(knowledge.replace("'", '"'))
            except:
                knowledge = []
        elif isinstance(knowledge, set):
            knowledge = list(knowledge)
        return knowledge[:20]  # 상위 20개만
    
    def get_recent_notes(self, limit=5):
        """최근 학습한 노트 가져오기"""
        self.cursor.execute('''
            SELECT file_path, summary, importance_score
            FROM learned_content 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    def personal_secretary_response(self, query):
        """개인 비서 모드 응답"""
        interests = self.get_interests_list()
        recent_notes = self.get_recent_notes(3)
        
        response = f"📋 비서 역할로 답변드립니다:\n\n"
        
        if "일정" in query or "계획" in query:
            response += "당신의 노트를 분석한 결과, 다음과 같은 패턴을 발견했습니다:\n"
            if interests:
                response += f"• 주요 관심 분야: {', '.join(interests[:5])}\n"
            response += f"• 학습 세션: {self.learning_sessions}회 완료\n"
            response += f"• 적응 레벨: {self.adaptation_level:.2f}\n"
        
        elif "요약" in query or "정리" in query:
            response += "최근 학습한 내용을 요약해드립니다:\n"
            for i, note in enumerate(recent_notes, 1):
                filename = note[0].split('\\')[-1] if '\\' in note[0] else note[0]
                response += f"{i}. {filename} (중요도: {note[2]:.2f})\n"
        
        else:
            response += f"총 {len(interests)}개의 관심사와 387개의 노트를 학습했습니다.\n"
            response += "구체적인 질문을 해주시면 더 자세한 도움을 드릴 수 있습니다."
        
        return response
    
    def personal_mentor_response(self, query):
        """개인 멘토 모드 응답"""
        goals = self.profile.get('goals', [])
        knowledge = self.get_knowledge_areas_list()
        
        response = f"🎓 멘토 역할로 조언드립니다:\n\n"
        
        if "학습" in query or "공부" in query:
            response += "당신의 학습 패턴을 분석해봤습니다:\n"
            if knowledge:
                response += f"• 강점 영역: {', '.join(knowledge[:5])}\n"
            response += f"• 목표 달성을 위한 제안: {len(goals)}개의 목표를 체계적으로 추진하세요\n"
        
        elif "조언" in query or "방향" in query:
            response += "당신의 노트에서 발견한 성장 포인트:\n"
            response += f"• 지속적인 학습: {self.learning_sessions}회의 세션을 통해 꾸준히 발전 중\n"
            response += f"• 다양한 관심사: {len(self.get_interests_list())}개 분야에 관심을 보임\n"
        
        else:
            response += "구체적인 학습 목표나 방향에 대해 질문해주시면 맞춤형 조언을 드리겠습니다."
        
        return response
    
    def personal_companion_response(self, query):
        """개인 동반자 모드 응답"""
        response = f"💝 따뜻한 동반자로서 말씀드립니다:\n\n"
        
        if "기분" in query or "감정" in query:
            response += "당신의 글에서 다양한 감정과 생각을 느낄 수 있었습니다.\n"
            response += f"387개의 노트를 통해 당신의 성장 과정을 지켜보며 응원하고 있어요. 💪"
        
        elif "힘들" in query or "어려" in query:
            response += "힘든 시간을 보내고 계시는군요. 하지만 당신의 노트를 보면\n"
            response += "항상 배우고 성장하려는 의지가 느껴집니다. 함께 해결해나가요! 🌟"
        
        else:
            response += f"당신의 {len(self.get_interests_list())}가지 관심사를 통해 얼마나 호기심 많고\n"
            response += "성장하는 분인지 알 수 있어요. 언제든 대화 나누어요! 😊"
        
        return response
    
    def chat(self):
        """대화 시작"""
        print("🤖 옵시디언 개인 AI 어시스턴트")
        print("=" * 50)
        print("안녕하세요! 당신의 387개 노트를 학습한 개인 AI 어시스턴트입니다.")
        print("비서(1), 멘토(2), 동반자(3) 중 원하는 모드를 선택하거나")
        print("자유롭게 대화해보세요! (종료: 'quit')")
        print()
        
        while True:
            query = input("💬 당신: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료', '나가기']:
                print("👋 또 만나요! 언제든 도움이 필요하면 불러주세요.")
                break
            
            if not query:
                continue
            
            # 모드 선택
            if query == "1" or "비서" in query:
                response = self.personal_secretary_response(query)
            elif query == "2" or "멘토" in query:
                response = self.personal_mentor_response(query)
            elif query == "3" or "동반자" in query:
                response = self.personal_companion_response(query)
            else:
                # 키워드 기반 자동 모드 선택
                if any(word in query for word in ["일정", "계획", "정리", "요약"]):
                    response = self.personal_secretary_response(query)
                elif any(word in query for word in ["학습", "공부", "조언", "방향"]):
                    response = self.personal_mentor_response(query)
                elif any(word in query for word in ["기분", "감정", "힘들", "어려"]):
                    response = self.personal_companion_response(query)
                else:
                    # 기본 응답
                    interests = self.get_interests_list()
                    response = f"🤖 AI 어시스턴트:\n\n"
                    response += f"당신의 질문 '{query}'에 대해 답변드리겠습니다.\n\n"
                    response += f"387개의 노트를 학습한 결과, 당신은 다음 분야에 관심이 많으신 것 같아요:\n"
                    if interests:
                        response += f"• {', '.join(interests[:10])}\n\n"
                    response += "더 구체적인 도움이 필요하시면 비서(1), 멘토(2), 동반자(3) 모드를 선택해주세요!"
            
            print(f"\n{response}\n")
            print("-" * 50)
            
            # 상호작용 기록
            try:
                self.cursor.execute('''
                    INSERT INTO interaction_history (interaction_type, user_input, ai_response, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', ('chat', query, response, datetime.now().isoformat()))
                self.db.commit()
            except:
                pass

if __name__ == "__main__":
    chat_bot = PersonalAIChat()
    chat_bot.chat()
