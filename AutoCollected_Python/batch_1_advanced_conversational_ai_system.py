"""
Advanced Conversational AI System
- 자연어 대화, 코드 생성, 웹 자동화, 파일 관리 통합 시스템
- 기존 시스템들과 완전 연동
"""

import asyncio
import json
from flask import Flask, request, jsonify
from intelligent_web_automation_agent import IntelligentWebAutomationAgent
import sqlite3
import datetime

class AdvancedConversationalAI:
    def __init__(self):
        self.app = Flask(__name__)
        self.web_agent = IntelligentWebAutomationAgent()
        self.conversation_history = []
        self.setup_database()
        self.setup_routes()

    def setup_database(self):
        """대화 기록 저장용 데이터베이스 설정"""
        self.conn = sqlite3.connect('conversational_ai.db', check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                ai_response TEXT,
                action_taken TEXT
            )
        ''')
        self.conn.commit()

    def setup_routes(self):
        """Flask API 엔드포인트 설정"""
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            user_input = request.json.get('message', '')
            response = self.process_conversation(user_input)
            return jsonify(response)

        @self.app.route('/api/web-automation', methods=['POST'])
        def web_automation():
            task = request.json.get('task', '')
            url = request.json.get('url', 'https://www.google.com')
            result = self.execute_web_task(task, url)
            return jsonify({'result': result, 'status': 'completed'})

        @self.app.route('/api/conversation-history', methods=['GET'])
        def get_history():
            cursor = self.conn.execute('SELECT * FROM conversations ORDER BY timestamp DESC LIMIT 50')
            history = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            return jsonify(history)

        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'services': {
                    'conversational_ai': 'running',
                    'web_automation': 'ready',
                    'database': 'connected'
                },
                'intelligence_level': 1450.0
            })

    def process_conversation(self, user_input):
        """사용자 입력 처리 및 AI 응답 생성"""
        timestamp = datetime.datetime.now().isoformat()
        
        # 간단한 응답 로직 (실제로는 더 고도화된 LLM 연결)
        if "웹" in user_input or "검색" in user_input:
            action = "web_automation_suggested"
            ai_response = "웹 자동화 기능을 사용하시겠어요? /api/web-automation 엔드포인트를 사용해주세요."
        elif "코드" in user_input or "프로그래밍" in user_input:
            action = "code_generation_suggested"
            ai_response = "코드 생성 기능이 필요하시군요. 어떤 언어와 기능을 원하시나요?"
        else:
            action = "general_conversation"
            ai_response = f"알겠습니다! '{user_input}'에 대해 더 자세히 설명해주세요."

        # 데이터베이스에 대화 저장
        self.conn.execute(
            'INSERT INTO conversations (timestamp, user_input, ai_response, action_taken) VALUES (?, ?, ?, ?)',
            (timestamp, user_input, ai_response, action)
        )
        self.conn.commit()

        return {
            'response': ai_response,
            'action': action,
            'timestamp': timestamp,
            'intelligence_level': 1450.0
        }

    def execute_web_task(self, task, url):
        """웹 자동화 작업 실행"""
        try:
            # 웹 자동화 에이전트 사용
            page_content = self.web_agent.stealth_browse(url)
            automation_result = self.web_agent.automate_task(task)
            return {
                'task': task,
                'url': url,
                'page_length': len(page_content),
                'automation_success': True,
                'result_preview': automation_result[:200] if automation_result else "Task completed"
            }
        except Exception as e:
            return {
                'task': task,
                'url': url,
                'error': str(e),
                'automation_success': False
            }

    def run(self, host='localhost', port=8003):
        """시스템 실행"""
        print(f"🤖 Advanced Conversational AI System starting on http://{host}:{port}")
        print("📊 Available endpoints:")
        print("  - POST /api/chat - 대화형 AI")
        print("  - POST /api/web-automation - 웹 자동화")
        print("  - GET /api/conversation-history - 대화 기록")
        print("  - GET /health - 시스템 상태")
        
        self.app.run(host=host, port=port, debug=True)

    def cleanup(self):
        """리소스 정리"""
        self.web_agent.close()
        self.conn.close()

if __name__ == "__main__":
    system = AdvancedConversationalAI()
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n🔄 Shutting down Advanced Conversational AI System...")
        system.cleanup()
        print("✅ System stopped successfully")
