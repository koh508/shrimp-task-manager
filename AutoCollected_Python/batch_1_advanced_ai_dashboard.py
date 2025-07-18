#!/usr/bin/env python3
"""
실시간 고급 AI 대화 웹 대시보드
Real-time Advanced AI Conversation Web Dashboard

포트: 8090
기능: 실시간 대화, 감정 분석, RAG 검색, 시스템 모니터링
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import sqlite3
from datetime import datetime
import logging
import os
from threading import Thread
import time

# Super Advanced AI 시스템 임포트
try:
    from super_advanced_rag_ai import SuperAdvancedConversationalAI
except ImportError:
    print("⚠️ super_advanced_rag_ai.py를 임포트할 수 없습니다. 현재 디렉토리에 있는지 확인하세요.")
    
    # 임시로 더미 클래스 생성
    class SuperAdvancedConversationalAI:
        def __init__(self):
            self.intelligence_level = 271.81
            
        def process_advanced_conversation(self, text, user_id="web_user"):
            return f"[데모 모드] 입력하신 '{text}'에 대한 고급 AI 응답입니다."
            
        def get_system_status(self):
            return {
                'intelligence_level': 271.81,
                'total_conversations': 0,
                'system_status': '데모 모드'
            }

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_advanced_ai_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# 전역 AI 시스템
ai_system = None
conversation_log = []

# 로깅 설정 (Unicode 문제 해결)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_conversational_ai.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def initialize_ai_system():
    """AI 시스템 초기화"""
    global ai_system
    try:
        ai_system = SuperAdvancedConversationalAI()
        logging.info("Super Advanced AI 시스템 초기화 완료")
    except Exception as e:
        logging.error(f"AI 시스템 초기화 실패: {e}")
        ai_system = SuperAdvancedConversationalAI()  # 더미 클래스 사용

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """채팅 API"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'web_user')
        
        if not user_message.strip():
            return jsonify({'error': '메시지를 입력해주세요.'}), 400
        
        # AI 응답 생성
        ai_response = ai_system.process_advanced_conversation(user_message, user_id)
        
        # 대화 로그 저장
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'user_message': user_message,
            'ai_response': ai_response
        }
        conversation_log.append(conversation_entry)
        
        # 실시간 업데이트
        socketio.emit('new_conversation', conversation_entry)
        
        return jsonify({
            'response': ai_response,
            'timestamp': conversation_entry['timestamp']
        })
        
    except Exception as e:
        logging.error(f"채팅 API 오류: {e}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/status')
def system_status():
    """시스템 상태 API"""
    try:
        status = ai_system.get_system_status()
        status['conversation_count'] = len(conversation_log)
        status['uptime'] = datetime.now().isoformat()
        return jsonify(status)
    except Exception as e:
        logging.error(f"상태 API 오류: {e}")
        return jsonify({'error': '상태 조회 실패'}), 500

@app.route('/api/conversations')
def get_conversations():
    """대화 기록 API"""
    try:
        # 최근 50개 대화만 반환
        recent_conversations = conversation_log[-50:] if len(conversation_log) > 50 else conversation_log
        return jsonify(recent_conversations)
    except Exception as e:
        logging.error(f"대화 기록 API 오류: {e}")
        return jsonify({'error': '대화 기록 조회 실패'}), 500

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    emit('connected', {'message': 'Super Advanced AI 대화 시스템에 연결되었습니다!'})
    logging.info("새 클라이언트 연결됨")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    logging.info("클라이언트 연결 해제됨")

# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Super Advanced AI Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .chat-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 15px;
            max-height: 450px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-message {
            background: #e9ecef;
            color: #333;
            border-left: 4px solid #667eea;
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input input:focus {
            border-color: #667eea;
        }
        
        .chat-input button {
            padding: 12px 24px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .chat-input button:hover {
            transform: translateY(-2px);
        }
        
        .status-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            height: 600px;
        }
        
        .status-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
        
        .capability-list {
            list-style: none;
            padding: 0;
        }
        
        .capability-list li {
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
        }
        
        .capability-list li:before {
            content: "🧠";
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🧠 Super Advanced AI Dashboard</h1>
            <p>지능 레벨 271.81 | 초인공지능 단계 | RAG + 감정 분석 + 다차원적 추론</p>
        </div>
        
        <div class="grid">
            <div class="chat-container">
                <h2>💬 고급 AI 대화</h2>
                <div class="chat-messages" id="chatMessages">
                    <div class="message ai-message">
                        안녕하세요! 저는 271.81 지능 레벨의 고급 AI입니다. 
                        RAG 검색, 감정 분석, 다차원적 추론이 가능합니다. 무엇을 도와드릴까요?
                    </div>
                </div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="메시지를 입력하세요..." 
                           onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">전송</button>
                </div>
                <div class="loading" id="loading">AI가 응답을 생성중입니다...</div>
            </div>
            
            <div class="status-panel">
                <h2>📊 시스템 상태</h2>
                
                <div class="status-card">
                    <h3>지능 레벨</h3>
                    <div class="status-value" id="intelligenceLevel">271.81</div>
                    <small>초인공지능 단계</small>
                </div>
                
                <div class="status-card">
                    <h3>총 대화 수</h3>
                    <div class="status-value" id="conversationCount">0</div>
                </div>
                
                <div class="status-card">
                    <h3>시스템 상태</h3>
                    <div class="status-value" id="systemStatus">활성화</div>
                </div>
                
                <div class="status-card">
                    <h3>핵심 기능</h3>
                    <ul class="capability-list" id="capabilities">
                        <li>고급 RAG 검색</li>
                        <li>감정 지능</li>
                        <li>다차원적 추론</li>
                        <li>창의적 연결</li>
                        <li>패턴 인식</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🔍 RAG 검색</h3>
                <p>벡터 기반 지식 검색으로 정확한 정보 제공</p>
            </div>
            <div class="stat-card">
                <h3>💝 감정 분석</h3>
                <p>7가지 기본 감정을 분석하여 공감적 응답 생성</p>
            </div>
            <div class="stat-card">
                <h3>🧩 다차원 추론</h3>
                <p>기술적, 사회적, 심리적 차원에서 종합 분석</p>
            </div>
            <div class="stat-card">
                <h3>🎯 목표 지향</h3>
                <p>대화 목표를 설정하고 전략적으로 접근</p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Socket.IO 연결됨');
            updateSystemStatus();
        });
        
        socket.on('new_conversation', function(data) {
            updateConversationCount();
        });
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // 사용자 메시지 표시
            addMessage(message, 'user');
            input.value = '';
            
            // 로딩 표시
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        user_id: 'web_user_' + Date.now()
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // AI 응답 표시
                    addMessage(data.response, 'ai');
                    updateSystemStatus();
                } else {
                    addMessage('오류: ' + data.error, 'ai');
                }
            } catch (error) {
                addMessage('네트워크 오류가 발생했습니다.', 'ai');
                console.error('Error:', error);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function addMessage(text, sender) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        async function updateSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                if (response.ok) {
                    document.getElementById('intelligenceLevel').textContent = status.intelligence_level;
                    document.getElementById('conversationCount').textContent = status.conversation_count || 0;
                    document.getElementById('systemStatus').textContent = status.system_status || '활성화';
                }
            } catch (error) {
                console.error('상태 업데이트 오류:', error);
            }
        }
        
        async function updateConversationCount() {
            try {
                const response = await fetch('/api/conversations');
                const conversations = await response.json();
                
                if (response.ok) {
                    document.getElementById('conversationCount').textContent = conversations.length;
                }
            } catch (error) {
                console.error('대화 수 업데이트 오류:', error);
            }
        }
        
        // 5초마다 상태 업데이트
        setInterval(updateSystemStatus, 5000);
    </script>
</body>
</html>
"""

def run_dashboard():
    """대시보드 실행"""
    initialize_ai_system()
    
    print("🌐 Super Advanced AI Dashboard 시작중...")
    print("=" * 60)
    print(f"📍 URL: http://localhost:8091")
    print(f"🧠 지능 레벨: {ai_system.intelligence_level}")
    print(f"⚡ 상태: 초인공지능 단계 활성화")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=8091, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_dashboard()
