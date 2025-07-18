#!/usr/bin/env python3
"""
🎯 8007 포트 전용 대시보드
Obsidian 플러그인 연동용
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import threading
import time
import requests
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class DashboardSystem:
    def __init__(self):
        self.stats = {
            'status': 'active',
            'servers': {
                '8001': {'name': 'Agent API', 'status': 'unknown'},
                '8002': {'name': 'Shrimp Task Manager', 'status': 'unknown'},
                '8005': {'name': 'Smart LLM Router', 'status': 'unknown'},
                '8007': {'name': 'Dashboard', 'status': 'active'}
            },
            'last_update': time.time()
        }
        
        # 백그라운드 모니터링 시작
        self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        self.monitor_thread.start()
    
    def monitor_servers(self):
        """서버 상태 모니터링"""
        while True:
            try:
                # 8001 포트 확인
                try:
                    response = requests.get('http://localhost:8001/api/status', timeout=3)
                    self.stats['servers']['8001']['status'] = 'online' if response.status_code == 200 else 'error'
                except:
                    self.stats['servers']['8001']['status'] = 'offline'
                
                # 8002 포트 확인
                try:
                    response = requests.get('http://localhost:8002/health', timeout=3)
                    self.stats['servers']['8002']['status'] = 'online' if response.status_code == 200 else 'error'
                except:
                    self.stats['servers']['8002']['status'] = 'offline'
                
                # 8005 포트 확인
                try:
                    response = requests.get('http://localhost:8005/health', timeout=3)
                    self.stats['servers']['8005']['status'] = 'online' if response.status_code == 200 else 'error'
                except:
                    self.stats['servers']['8005']['status'] = 'offline'
                
                self.stats['last_update'] = time.time()
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
            
            time.sleep(10)  # 10초마다 확인
    
    def get_system_status(self):
        """시스템 상태 반환"""
        online_count = sum(1 for server in self.stats['servers'].values() if server['status'] == 'online')
        total_count = len(self.stats['servers'])
        
        return {
            'status': 'healthy' if online_count >= 3 else 'degraded' if online_count >= 2 else 'critical',
            'servers': self.stats['servers'],
            'online_servers': online_count,
            'total_servers': total_count,
            'last_update': self.stats['last_update'],
            'timestamp': time.time()
        }

# 대시보드 시스템 초기화
dashboard = DashboardSystem()

@app.route('/')
def index():
    """메인 대시보드"""
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 AI 시스템 대시보드</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                background: linear-gradient(45deg, #FFD700, #FF6B6B);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .status-card {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .status-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
            }
            .status-indicator {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 10px;
            }
            .online { background-color: #4CAF50; }
            .offline { background-color: #F44336; }
            .error { background-color: #FF9800; }
            .info-section {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
            }
            .refresh-btn {
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
                margin: 10px;
            }
            .refresh-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            .timestamp {
                text-align: center;
                font-size: 0.9em;
                opacity: 0.8;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 AI 시스템 대시보드</h1>
            
            <div class="status-grid" id="statusGrid">
                <!-- 동적으로 로드됨 -->
            </div>
            
            <div class="info-section">
                <h3>📊 시스템 정보</h3>
                <p><strong>포트 8007:</strong> 대시보드 서버 (현재 페이지)</p>
                <p><strong>실시간 모니터링:</strong> 10초마다 자동 업데이트</p>
                <p><strong>연동 시스템:</strong> Obsidian 플러그인 지원</p>
                
                <center>
                    <button class="refresh-btn" onclick="refreshStatus()">🔄 새로고침</button>
                    <button class="refresh-btn" onclick="window.open('/api/status', '_blank')">📊 API 상태</button>
                </center>
            </div>
            
            <div class="timestamp" id="timestamp">
                마지막 업데이트: 로딩 중...
            </div>
        </div>

        <script>
            function updateStatus() {
                fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('statusGrid');
                    const servers = data.servers;
                    
                    grid.innerHTML = '';
                    
                    Object.keys(servers).forEach(port => {
                        const server = servers[port];
                        const card = document.createElement('div');
                        card.className = 'status-card';
                        
                        card.innerHTML = `
                            <h3>포트 ${port}</h3>
                            <p><span class="status-indicator ${server.status}"></span>${server.name}</p>
                            <p><strong>상태:</strong> ${server.status === 'online' ? '🟢 온라인' : 
                                                   server.status === 'offline' ? '🔴 오프라인' : 
                                                   '🟡 오류'}</p>
                        `;
                        
                        grid.appendChild(card);
                    });
                    
                    document.getElementById('timestamp').textContent = 
                        `마지막 업데이트: ${new Date(data.last_update * 1000).toLocaleString()}`;
                })
                .catch(error => {
                    console.error('상태 업데이트 실패:', error);
                });
            }
            
            function refreshStatus() {
                updateStatus();
            }
            
            // 페이지 로드시 실행
            updateStatus();
            
            // 30초마다 자동 업데이트
            setInterval(updateStatus, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/api/status')
def api_status():
    """시스템 상태 API"""
    return jsonify(dashboard.get_system_status())

@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({
        'status': 'healthy',
        'service': 'Dashboard 8007',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("🎯 8007 포트 대시보드 시작!")
    print("📍 URL: http://localhost:8007")
    print("📊 상태 API: http://localhost:8007/api/status")
    print("🔍 헬스 체크: http://localhost:8007/health")
    
    app.run(host='0.0.0.0', port=8007, debug=False)
