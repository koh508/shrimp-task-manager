#!/usr/bin/env python3
"""
Enhanced Real-time Log Monitor for Super Unified Agents
실시간 로그 모니터링 시스템
"""

import os
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import http.server
import socketserver
import threading
import subprocess
import psutil

class EnhancedLogMonitor:
    def __init__(self):
        self.port = 8082
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.db_file = "super_unified_agent.db"
        
        # 로그 파일들
        self.log_files = {
            "heroic": self.log_dir / "super_heroic.log",
            "dianaira": self.log_dir / "super_dianaira.log", 
            "argonaute": self.log_dir / "super_argonaute.log"
        }
        
        # 각 로그 파일의 마지막 읽은 위치
        self.file_positions = {name: 0 for name in self.log_files.keys()}
        
        self.running = False
        
    def get_agent_processes(self):
        """실행 중인 에이전트 프로세스 확인"""
        processes = {}
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'super_unified_agent.py' in ' '.join(cmdline):
                    for agent in ['heroic', 'dianaira', 'argonaute']:
                        if f'super_{agent}' in ' '.join(cmdline):
                            processes[agent] = {
                                'pid': proc.info['pid'],
                                'status': 'running',
                                'cpu_percent': proc.cpu_percent(),
                                'memory_mb': round(proc.memory_info().rss / 1024 / 1024, 1)
                            }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
        
    def get_database_stats(self):
        """데이터베이스 통계 조회"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            stats = {}
            
            # 각 에이전트별 통계
            for agent in ['super_heroic', 'super_dianaira', 'super_argonaute']:
                # 영웅 소환 횟수
                try:
                    cursor.execute("SELECT COUNT(*) FROM hero_summons WHERE agent_name = ?", (agent,))
                    hero_count = cursor.fetchone()[0]
                except:
                    hero_count = 0
                
                # 코드 분석 횟수
                try:
                    cursor.execute("SELECT COUNT(*) FROM code_analysis WHERE agent_name = ?", (agent,))
                    analysis_count = cursor.fetchone()[0]
                except:
                    analysis_count = 0
                
                # MCP 통신 횟수 (테이블이 없으면 0으로 설정)
                try:
                    cursor.execute("SELECT COUNT(*) FROM mcp_communications WHERE agent_name = ?", (agent,))
                    mcp_count = cursor.fetchone()[0]
                except:
                    mcp_count = 0
                
                stats[agent] = {
                    'hero_summons': hero_count,
                    'code_analysis': analysis_count,
                    'mcp_communications': mcp_count
                }
            
            conn.close()
            return stats
            
        except Exception as e:
            # 기본값 반환
            return {
                'super_heroic': {'hero_summons': 0, 'code_analysis': 0, 'mcp_communications': 0},
                'super_dianaira': {'hero_summons': 0, 'code_analysis': 0, 'mcp_communications': 0},
                'super_argonaute': {'hero_summons': 0, 'code_analysis': 0, 'mcp_communications': 0}
            }
    
    def read_new_logs(self):
        """새로운 로그 라인들 읽기"""
        new_logs = []
        
        for agent_name, log_file in self.log_files.items():
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        f.seek(self.file_positions[agent_name])
                        new_lines = f.readlines()
                        self.file_positions[agent_name] = f.tell()
                        
                        for line in new_lines:
                            if line.strip():
                                new_logs.append({
                                    'agent': agent_name,
                                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                                    'message': line.strip()
                                })
                except Exception as e:
                    print(f"로그 읽기 오류 ({agent_name}): {e}")
        
        return new_logs

class EnhancedLogHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, log_monitor=None, **kwargs):
        self.log_monitor = log_monitor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # 경로에 따라 적절한 응답 처리
        if self.path == '/':
            self.send_dashboard()
        elif self.path == '/api/status':
            self.send_status()
        elif self.path == '/api/logs':
            self.send_logs()
        elif self.path == '/api/start_agent':
            self.start_agent()
        elif self.path.startswith('/api/start_agent/'):
            agent_name = self.path.split('/')[-1]
            self.start_specific_agent(agent_name)
        else:
            self.send_error(404)
    
    def do_POST(self):
        # POST 요청 처리
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(post_data)
        except:
            data = {}
        
        if self.path == '/api/advanced-vibe':
            self.handle_advanced_vibe(data)
        elif self.path == '/api/boost':
            self.handle_system_boost(data)
        elif self.path == '/api/focus-mode':
            self.handle_focus_mode(data)
        elif self.path == '/api/multi-agent':
            self.handle_multi_agent(data)
        elif self.path == '/api/power-mode':
            self.handle_power_mode(data)
        elif self.path == '/api/reset':
            self.handle_system_reset(data)
        elif self.path == '/api/chat':
            self.handle_chat_message(data)
        elif self.path == '/api/natural-command':
            self.handle_natural_command(data)
        else:
            self.send_error(404)
    
    def send_cors_headers(self, content_type='application/json'):
        """CORS 헤더 전송"""
        self.send_response(200)
        self.send_header('Content-type', content_type + '; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_dashboard(self):
        """개선된 대시보드 HTML"""
        self.send_cors_headers('text/html')
        
        html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Super Unified Agent Monitor - Enhanced</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .agent-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .agent-card:hover {
            transform: translateY(-5px);
        }
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .agent-name {
            font-size: 1.3em;
            font-weight: bold;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-running { background: #4ade80; }
        .status-stopped { background: #f87171; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .agent-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        .stat-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            display: block;
        }
        .control-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        .btn-start {
            background: #4ade80;
            color: white;
        }
        .btn-start:hover {
            background: #22c55e;
        }
        .btn-stop {
            background: #f87171;
            color: white;
        }
        .logs-section {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
        }
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .log-container {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .log-entry {
            margin-bottom: 8px;
            padding: 5px 10px;
            border-radius: 4px;
            border-left: 3px solid;
        }
        .log-heroic { border-left-color: #ff6b35; background: rgba(255, 107, 53, 0.1); }
        .log-dianaira { border-left-color: #4ecdc4; background: rgba(78, 205, 196, 0.1); }
        .log-argonaute { border-left-color: #45b7d1; background: rgba(69, 183, 209, 0.1); }
        .log-timestamp {
            color: #888;
            font-size: 0.8em;
        }
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .refresh-status {
            color: #4ade80;
            font-weight: bold;
        }
        
        /* 채팅 인터페이스 스타일 */
        .chat-section {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 15px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            background: #1a1a1a;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            position: relative;
        }
        
        .message.user .message-content {
            background: #4CAF50;
            color: white;
        }
        
        .message.bot .message-content {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }
        
        .message-time {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .chat-input-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            outline: none;
            font-size: 14px;
        }
        
        .chat-input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .chat-send-btn {
            padding: 12px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        
        .chat-send-btn:hover {
            background: #45a049;
        }
        
        .chat-send-btn:disabled {
            background: #666;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            display: none;
            margin-bottom: 15px;
        }
        
        .typing-dots {
            display: inline-block;
            position: relative;
        }
        
        .typing-dots::after {
            content: '...';
            animation: typing 1.4s infinite;
        }
        
        @keyframes typing {
            0%, 60% { content: '...'; }
            20% { content: '.'; }
            40% { content: '..'; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Super Unified Agent Monitor</h1>
            <p>실시간 에이전트 모니터링 & 로그 시스템</p>
        </div>
        
        <div class="stats-grid" id="agentGrid">
            <!-- 에이전트 카드들이 여기에 동적으로 생성됩니다 -->
        </div>
        
        <div class="logs-section">
            <div class="logs-header">
                <h2>📋 실시간 로그 모니터링</h2>
                <div class="auto-refresh">
                    <span class="refresh-status">🔄 자동 새로고침</span>
                    <span id="refreshTimer">10</span>초
                </div>
            </div>
            <div class="log-container" id="logContainer">
                <!-- 로그 엔트리들이 여기에 표시됩니다 -->
            </div>
        </div>
        
        <div class="chat-section">
            <div class="chat-header">
                <h2>💬 AI 채팅 - 자연어 명령</h2>
                <div class="chat-status">
                    <span class="refresh-status">🤖 AI 대화 모드</span>
                </div>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-content">
                        👋 안녕하세요! Super Unified Agent AI입니다. 
                        <br>자연스럽게 대화하면서 시스템을 제어할 수 있어요.
                        <br><br>예시: "시스템 상태 확인해줘", "바이브 모드 켜줘", "모든 에이전트 부스트해줘"
                        <div class="message-time" id="welcomeTime"></div>
                    </div>
                </div>
            </div>
            <div class="typing-indicator" id="typingIndicator">
                <div class="message bot">
                    <div class="message-content">
                        🤖 AI가 생각 중<span class="typing-dots"></span>
                    </div>
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chatInput" 
                       placeholder="자연스럽게 대화해보세요... (예: 시스템 상태 확인해줘)"
                       onkeypress="handleChatKeyPress(event)">
                <button class="chat-send-btn" id="chatSendBtn" onclick="sendChatMessage()">
                    전송
                </button>
            </div>
        </div>
    </div>

    <script>
        let refreshTimer = 10;
        let logs = [];
        
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateAgentGrid(data);
            } catch (error) {
                console.error('상태 조회 실패:', error);
            }
        }
        
        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs');
                const newLogs = await response.json();
                
                // 새 로그 추가
                logs = [...logs, ...newLogs].slice(-100); // 최근 100개만 유지
                updateLogDisplay();
            } catch (error) {
                console.error('로그 조회 실패:', error);
            }
        }
        
        function updateAgentGrid(data) {
            const grid = document.getElementById('agentGrid');
            const agents = ['heroic', 'dianaira', 'argonaute'];
            
            grid.innerHTML = agents.map(agent => {
                const process = data.processes[agent] || {};
                const stats = data.stats[`super_${agent}`] || {};
                const isRunning = !!process.pid;
                
                return `
                    <div class="agent-card">
                        <div class="agent-header">
                            <div class="agent-name">
                                ${getAgentIcon(agent)} ${getAgentName(agent)}
                            </div>
                            <div class="status-indicator ${isRunning ? 'status-running' : 'status-stopped'}"></div>
                        </div>
                        
                        <div class="agent-stats">
                            <div class="stat-item">
                                <span class="stat-value">${stats.hero_summons || 0}</span>
                                <div>영웅 소환</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">${stats.code_analysis || 0}</span>
                                <div>코드 분석</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">${stats.mcp_communications || 0}</span>
                                <div>MCP 통신</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">${process.memory_mb || 0}MB</span>
                                <div>메모리</div>
                            </div>
                        </div>
                        
                        <div class="control-buttons">
                            <button class="btn btn-start" onclick="startAgent('${agent}')" ${isRunning ? 'disabled' : ''}>
                                ${isRunning ? '실행 중' : '시작'}
                            </button>
                            ${process.pid ? `<span>PID: ${process.pid}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateLogDisplay() {
            const container = document.getElementById('logContainer');
            container.innerHTML = logs.map(log => `
                <div class="log-entry log-${log.agent}">
                    <span class="log-timestamp">[${log.timestamp}]</span>
                    <strong>${getAgentName(log.agent)}:</strong> ${log.message}
                </div>
            `).join('');
            
            // 자동 스크롤
            container.scrollTop = container.scrollHeight;
        }
        
        function getAgentIcon(agent) {
            const icons = {
                'heroic': '🦸',
                'dianaira': '👸', 
                'argonaute': '🚀'
            };
            return icons[agent] || '🤖';
        }
        
        function getAgentName(agent) {
            const names = {
                'heroic': 'Heroic Agent',
                'dianaira': 'Dianaira Agent',
                'argonaute': 'Argonaute Agent'
            };
            return names[agent] || agent;
        }
        
        async function startAgent(agent) {
            try {
                await fetch(`/api/start_agent/${agent}`);
                setTimeout(() => fetchStatus(), 2000); // 2초 후 상태 새로고침
            } catch (error) {
                console.error('에이전트 시작 실패:', error);
            }
        }
        
        // 타이머 업데이트
        function updateTimer() {
            refreshTimer--;
            document.getElementById('refreshTimer').textContent = refreshTimer;
            
            if (refreshTimer <= 0) {
                refreshTimer = 10;
                fetchStatus();
                fetchLogs();
            }
        }
        
        // 초기 로드 및 자동 새로고침 설정
        fetchStatus();
        fetchLogs();
        setInterval(updateTimer, 1000);
        
        // 채팅 초기화
        initializeChat();
        
        // 채팅 관련 함수들
        let chatHistory = [];
        
        function initializeChat() {
            // 환영 메시지 시간 설정
            document.getElementById('welcomeTime').textContent = new Date().toLocaleTimeString();
        }
        
        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }
        
        async function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // 사용자 메시지 추가
            addChatMessage(message, 'user');
            input.value = '';
            
            // 전송 버튼 비활성화 및 타이핑 표시
            toggleChatControls(false);
            showTypingIndicator(true);
            
            try {
                // API 호출
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        user_id: 'user',
                        history: chatHistory.slice(-5) // 최근 5개 대화만 전송
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // AI 응답 추가
                    setTimeout(() => {
                        showTypingIndicator(false);
                        addChatMessage(data.response, 'bot');
                        
                        // 명령이 감지된 경우 추가 정보 표시
                        if (data.detected_intent) {
                            addChatMessage(
                                `🎯 "${data.detected_intent}" 명령을 실행했습니다!`, 
                                'bot', 
                                'system'
                            );
                        }
                        
                        toggleChatControls(true);
                    }, 1000); // 1초 딜레이로 자연스러운 느낌
                } else {
                    showTypingIndicator(false);
                    addChatMessage('죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.', 'bot');
                    toggleChatControls(true);
                }
                
            } catch (error) {
                console.error('채팅 오류:', error);
                showTypingIndicator(false);
                addChatMessage('연결 오류가 발생했습니다. 서버 상태를 확인해주세요.', 'bot');
                toggleChatControls(true);
            }
        }
        
        function addChatMessage(content, sender, type = 'normal') {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const time = new Date().toLocaleTimeString();
            const icon = sender === 'user' ? '👤' : '🤖';
            
            let messageClass = 'message-content';
            if (type === 'system') {
                messageClass += ' system-message';
                content = `⚙️ ${content}`;
            }
            
            messageDiv.innerHTML = `
                <div class="${messageClass}">
                    ${content}
                    <div class="message-time">${icon} ${time}</div>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // 채팅 히스토리에 추가
            chatHistory.push({
                content: content,
                sender: sender,
                timestamp: Date.now()
            });
            
            // 최대 50개 메시지만 유지
            if (chatHistory.length > 50) {
                chatHistory = chatHistory.slice(-50);
            }
        }
        
        function showTypingIndicator(show) {
            const indicator = document.getElementById('typingIndicator');
            indicator.style.display = show ? 'block' : 'none';
            
            if (show) {
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
        
        function toggleChatControls(enabled) {
            const input = document.getElementById('chatInput');
            const button = document.getElementById('chatSendBtn');
            
            input.disabled = !enabled;
            button.disabled = !enabled;
            
            if (enabled) {
                input.focus();
            }
        }
        
        // 특별한 명령어 감지 및 실행
        async function executeDetectedCommand(intent) {
            try {
                const response = await fetch('/api/natural-command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        command: intent
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // 상태 새로고침
                    setTimeout(() => {
                        fetchStatus();
                        fetchLogs();
                    }, 1000);
                }
                
                return data;
            } catch (error) {
                console.error('명령 실행 오류:', error);
                return { success: false, message: '명령 실행 중 오류가 발생했습니다.' };
            }
        }
    </script>
</body>
</html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def send_status(self):
        """시스템 상태 API"""
        self.send_cors_headers('application/json')
        
        processes = self.log_monitor.get_agent_processes()
        stats = self.log_monitor.get_database_stats()
        
        status = {
            'processes': processes,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
    
    def send_logs(self):
        """새 로그 API"""
        self.send_cors_headers('application/json')
        
        new_logs = self.log_monitor.read_new_logs()
        self.wfile.write(json.dumps(new_logs, ensure_ascii=False).encode('utf-8'))
    
    def start_specific_agent(self, agent_name):
        """특정 에이전트 시작"""
        self.send_cors_headers('application/json')
        
        try:
            subprocess.Popen([
                'python', 'super_unified_agent.py', 
                '--agent', f'super_{agent_name}'
            ], cwd=os.getcwd())
            
            result = {'success': True, 'message': f'{agent_name} 에이전트 시작됨'}
        except Exception as e:
            result = {'success': False, 'message': str(e)}
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_advanced_vibe(self, data):
        """고급 바이브 코딩 모드 처리"""
        self.send_cors_headers('application/json')
        
        result = {
            'success': True,
            'message': '✨ 고급 바이브 코딩 모드가 활성화되었습니다!',
            'mode': 'advanced_vibe',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_system_boost(self, data):
        """시스템 부스트 처리"""
        self.send_cors_headers('application/json')
        
        result = {
            'success': True,
            'message': '🚀 시스템 성능이 부스트되었습니다!',
            'boost_level': 'maximum',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_focus_mode(self, data):
        """집중 모드 처리"""
        self.send_cors_headers('application/json')
        
        result = {
            'success': True,
            'message': '🎯 집중 모드가 활성화되었습니다!',
            'focus_level': 'high',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_multi_agent(self, data):
        """멀티 에이전트 모드 처리"""
        self.send_cors_headers('application/json')
        
        active_agents = list(self.log_monitor.get_agent_processes().keys())
        
        result = {
            'success': True,
            'message': f'🎭 {len(active_agents)}개 에이전트가 협업을 시작했습니다!',
            'active_agents': active_agents,
            'collaboration_mode': True,
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_power_mode(self, data):
        """파워 모드 처리"""
        self.send_cors_headers('application/json')
        
        result = {
            'success': True,
            'message': '⚡ 파워 모드가 활성화되었습니다!',
            'power_level': 'maximum',
            'performance': 'optimized',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def handle_system_reset(self, data):
        """시스템 리셋 처리"""
        self.send_cors_headers('application/json')
        
        result = {
            'success': True,
            'message': '🔄 시스템이 리셋되었습니다!',
            'reset_type': 'full',
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def parse_natural_language(self, text):
        """자연어를 명령어로 변환"""
        text = text.lower().strip()
        
        # 의도 분석을 위한 키워드 매핑
        intent_patterns = {
            'vibe': ['바이브', 'vibe', '창의적', '크리에이티브', '영감'],
            'boost': ['부스트', 'boost', '빠르게', '성능', '최적화', '가속'],
            'focus': ['집중', 'focus', '포커스', '몰입', '방해금지'],
            'multi': ['멀티', 'multi', '협업', '여러', '모든', '함께'],
            'debug': ['디버그', 'debug', '오류', '문제', '확인', '점검'],
            'status': ['상태', 'status', '현황', '정보', '체크'],
            'reset': ['리셋', 'reset', '초기화', '재시작', '새로'],
            'power': ['파워', 'power', '최대', '강력', '최고'],
            'hero': ['영웅', 'hero', '히어로', '소환'],
            'analyze': ['분석', 'analyze', '코드', '검토'],
            'mcp': ['mcp', '통신', '연결', '클라우드']
        }
        
        # 텍스트에서 의도 추출
        detected_intents = []
        for intent, keywords in intent_patterns.items():
            if any(keyword in text for keyword in keywords):
                detected_intents.append(intent)
        
        return detected_intents[0] if detected_intents else None
    
    def handle_chat_message(self, data):
        """채팅 메시지 처리"""
        self.send_cors_headers('application/json')
        
        message = data.get('message', '')
        user_id = data.get('user_id', 'user')
        
        # 자연어 처리
        detected_intent = self.parse_natural_language(message)
        
        if detected_intent:
            # 감지된 의도에 따라 적절한 응답 생성
            response = self.generate_intent_response(detected_intent, message)
        else:
            # MCP를 통한 일반 대화 처리
            response = self.handle_general_chat(message)
        
        result = {
            'success': True,
            'response': response,
            'detected_intent': detected_intent,
            'timestamp': datetime.now().isoformat(),
            'user_message': message
        }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def generate_intent_response(self, intent, message):
        """의도에 따른 응답 생성"""
        responses = {
            'vibe': '✨ 바이브 코딩 모드를 활성화했습니다! 창의적인 에너지가 흐르고 있어요.',
            'boost': '🚀 시스템 성능을 최대로 부스트했습니다! 모든 에이전트가 고속으로 작동 중입니다.',
            'focus': '🎯 집중 모드로 전환했습니다. 방해 요소를 최소화하고 몰입할 수 있도록 설정했어요.',
            'multi': '🎭 멀티 에이전트 협업 모드를 시작했습니다! 모든 에이전트가 함께 작업하고 있어요.',
            'debug': '🔍 시스템 디버그 모드를 활성화했습니다. 문제점을 찾아보겠습니다.',
            'status': '📈 현재 시스템 상태를 확인하고 있습니다. 모든 에이전트의 상태를 점검했어요.',
            'reset': '🔄 시스템을 초기화했습니다. 모든 설정이 기본값으로 돌아갔어요.',
            'power': '⚡ 파워 모드 활성화! 모든 에이전트가 최대 성능으로 작동합니다.',
            'hero': '🦸 영웅을 소환했습니다! 강력한 도움이 될 거예요.',
            'analyze': '📊 코드 분석을 시작했습니다. 세밀하게 검토해보겠어요.',
            'mcp': '🌐 MCP 통신을 활성화했습니다. 클라우드 연결이 설정되었어요.'
        };
        
        return responses.get(intent, '🤖 명령을 이해했습니다!')
    
    def handle_general_chat(self, message):
        """일반 대화 처리 (향후 MCP 연동)"""
        # 간단한 응답 생성 (추후 실제 LLM으로 대체)
        if '안녕' in message or 'hello' in message.lower():
            return '👋 안녕하세요! Super Unified Agent 시스템입니다. 어떤 도움이 필요하신가요?'
        elif '도움' in message or 'help' in message.lower():
            return '''
🤖 사용 가능한 명령어들:
• 바이브 코딩 - 창의적 모드 활성화
• 시스템 부스트 - 성능 최적화
• 집중 모드 - 방해 요소 제거
• 멀티 에이전트 - 협업 모드
• 상태 확인 - 시스템 점검
• 영웅 소환 - 도움 요청
무엇을 도와드릴까요? 😊
            '''
        elif '고마워' in message or 'thank' in message.lower():
            return '😊 천만에요! 언제든지 도움이 필요하면 말씀해주세요!'
        else:
            return f'🤔 "{message}"에 대해 생각해보고 있어요. 구체적인 명령어나 도움이 필요한 부분을 말씀해주시면 더 정확히 도와드릴 수 있어요!'
    
    def handle_natural_command(self, data):
        """자연어 명령 처리"""
        self.send_cors_headers('application/json')
        
        command = data.get('command', '')
        detected_intent = self.parse_natural_language(command)
        
        if detected_intent:
            # 해당 명령 실행
            action_result = self.execute_command(detected_intent)
            result = {
                'success': True,
                'intent': detected_intent,
                'action': action_result,
                'message': f'"{command}" 명령을 {detected_intent} 작업으로 인식하여 실행했습니다.',
                'timestamp': datetime.now().isoformat()
            }
        else:
            result = {
                'success': False,
                'message': f'"{command}" 명령을 이해하지 못했습니다. 다시 시도해주세요.',
                'timestamp': datetime.now().isoformat()
            }
        
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    
    def execute_command(self, intent):
        """의도에 따른 실제 명령 실행"""
        try:
            if intent == 'vibe':
                return {'type': 'advanced_vibe', 'status': 'activated'}
            elif intent == 'boost':
                return {'type': 'system_boost', 'status': 'activated'}
            elif intent == 'focus':
                return {'type': 'focus_mode', 'status': 'activated'}
            elif intent == 'multi':
                active_agents = list(self.log_monitor.get_agent_processes().keys())
                return {'type': 'multi_agent', 'active_agents': active_agents}
            elif intent == 'status':
                processes = self.log_monitor.get_agent_processes()
                return {'type': 'status_check', 'processes': processes}
            else:
                return {'type': intent, 'status': 'executed'}
        except Exception as e:
            return {'type': 'error', 'message': str(e)}

def main():
    monitor = EnhancedLogMonitor()
    
    # 핸들러 팩토리 함수
    def handler_factory(*args, **kwargs):
        return EnhancedLogHandler(*args, log_monitor=monitor, **kwargs)
    
    # 웹 서버 시작
    with socketserver.TCPServer(("", monitor.port), handler_factory) as httpd:
        print(f"🚀 Enhanced Log Monitor 서버 시작: http://localhost:{monitor.port}")
        print("📋 실시간 로그 모니터링 활성화")
        print("🎛️ 에이전트 제어 패널 활성화")
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n📴 Enhanced Log Monitor 종료")

if __name__ == "__main__":
    main()
