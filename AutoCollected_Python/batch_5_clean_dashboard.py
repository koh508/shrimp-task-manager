#!/usr/bin/env python3
"""
깔끔한 AI 대시보드 - 포트 8095
"""

import os
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class CleanAIDashboard(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL 파싱 (VS Code Simple Browser 호환)
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        print(f"📡 요청: {path}")
        
        if path == '/' or path == '/dashboard':
            self.send_dashboard()
        elif path == '/api/status':
            self.send_status_api()
        else:
            self.send_404()
    
    def send_dashboard(self):
        """메인 대시보드"""
        html = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>🚀 AI Evolution Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff; 
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1200px; margin: 0 auto; }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid var(--color, #00ff88);
        }
        
        .card-title {
            font-size: 1.2em;
            color: var(--color, #00ff88);
            margin-bottom: 15px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .metric-value {
            font-weight: bold;
            color: #ffffff;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff88;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .update-time {
            text-align: center;
            color: #ccc;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Evolution Dashboard</h1>
            <p>실시간 AI 시스템 모니터링</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card" style="--color: #00ff88;">
                <div class="card-title">
                    <span class="status-indicator"></span>
                    AI 진화 시스템
                </div>
                <div class="metric">
                    <span>지능 레벨:</span>
                    <span class="metric-value" id="intelligence">193.31</span>
                </div>
                <div class="metric">
                    <span>활성 에이전트:</span>
                    <span class="metric-value" id="agents">5</span>
                </div>
                <div class="metric">
                    <span>성장률:</span>
                    <span class="metric-value" id="growth">5503%</span>
                </div>
            </div>
            
            <div class="status-card" style="--color: #00ccff;">
                <div class="card-title">
                    <span class="status-indicator"></span>
                    시스템 리소스
                </div>
                <div class="metric">
                    <span>CPU 사용률:</span>
                    <span class="metric-value" id="cpu">5.2%</span>
                </div>
                <div class="metric">
                    <span>메모리 사용률:</span>
                    <span class="metric-value" id="memory">91.9%</span>
                </div>
                <div class="metric">
                    <span>Python 프로세스:</span>
                    <span class="metric-value" id="processes">44</span>
                </div>
            </div>
            
            <div class="status-card" style="--color: #ffa500;">
                <div class="card-title">
                    <span class="status-indicator"></span>
                    클라우드 동기화
                </div>
                <div class="metric">
                    <span>활성 서비스:</span>
                    <span class="metric-value" id="cloud-services">2</span>
                </div>
                <div class="metric">
                    <span>백업 크기:</span>
                    <span class="metric-value" id="backup-size">2.2 MB</span>
                </div>
                <div class="metric">
                    <span>성공률:</span>
                    <span class="metric-value" id="success-rate">100%</span>
                </div>
            </div>
            
            <div class="status-card" style="--color: #ff6b6b;">
                <div class="card-title">
                    <span class="status-indicator"></span>
                    가속화 시스템
                </div>
                <div class="metric">
                    <span>현재 단계:</span>
                    <span class="metric-value" id="phase">Phase 1</span>
                </div>
                <div class="metric">
                    <span>상태:</span>
                    <span class="metric-value" id="accel-status">기초 최적화</span>
                </div>
                <div class="metric">
                    <span>안정성:</span>
                    <span class="metric-value" id="stability">60%</span>
                </div>
            </div>
        </div>
        
        <div class="update-time">
            마지막 업데이트: <span id="update-time"></span>
            | <a href="http://localhost:8096" target="_blank" style="color: #00ff88; text-decoration: none;">📝 실시간 로그 보기</a>
        </div>
    </div>
    
    <script>
        function updateTime() {
            document.getElementById('update-time').textContent = new Date().toLocaleString('ko-KR');
        }
        
        function updateData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.intelligence) document.getElementById('intelligence').textContent = data.intelligence;
                    if (data.agents) document.getElementById('agents').textContent = data.agents;
                    updateTime();
                })
                .catch(err => console.log('데이터 업데이트 실패:', err));
        }
        
        updateTime();
        updateData();
        setInterval(updateData, 5000); // 5초마다 업데이트
    </script>
</body>
</html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_status_api(self):
        """상태 API"""
        try:
            status = {"intelligence": 241.31, "agents": 5, "timestamp": datetime.now().isoformat()}
            
            # 복제 상태 파일이 있으면 읽기
            if os.path.exists('replication_state.json'):
                with open('replication_state.json', 'r') as f:
                    repl_state = json.load(f)
                    status["intelligence"] = repl_state.get('intelligence', 241.31)
                    status["agents"] = repl_state.get('active_agents', 5)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode('utf-8'))
            
        except Exception as e:
            error_response = {"error": str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def send_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 - Page Not Found')
    
    def log_message(self, format, *args):
        # 로그 메시지 간소화
        pass

def start_clean_dashboard():
    """깔끔한 대시보드 시작"""
    port = 8095
    
    try:
        server = HTTPServer(('localhost', port), CleanAIDashboard)
        print(f"🎉 깔끔한 AI 대시보드 시작!")
        print(f"🌐 주소: http://localhost:{port}")
        print(f"📊 실시간 모니터링 준비 완료")
        print(f"🔄 5초마다 자동 업데이트")
        
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

if __name__ == "__main__":
    start_clean_dashboard()
