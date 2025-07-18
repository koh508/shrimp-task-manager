#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
클라우드 동기화 API 서버
Cloud Sync API Server
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 구글 클라우드 동기화 모듈 import
from google_cloud_sync import GoogleCloudSync

class CloudSyncAPI:
    def __init__(self):
        self.port = 8089
        self.sync_system = GoogleCloudSync()
        self.api_stats = {
            "requests_handled": 0,
            "syncs_triggered": 0,
            "last_request": None,
            "server_started": datetime.now().isoformat()
        }
    
    def create_handler(self):
        """API 핸들러 생성"""
        api = self
        
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/sync':
                    try:
                        # 요청 데이터 읽기
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        request_data = json.loads(post_data.decode('utf-8'))
                        
                        api.api_stats["requests_handled"] += 1
                        api.api_stats["last_request"] = datetime.now().isoformat()
                        
                        # 동기화 실행
                        sync_start = time.time()
                        
                        print(f"🔄 동기화 요청 받음 (출처: {request_data.get('source', 'unknown')})")
                        
                        # 백그라운드에서 동기화 실행
                        sync_thread = threading.Thread(
                            target=api.perform_sync_with_callback,
                            args=(request_data,),
                            daemon=True
                        )
                        sync_thread.start()
                        
                        # 즉시 응답 (비동기)
                        response = {
                            "status": "진행 중",
                            "message": "클라우드 동기화가 시작되었습니다",
                            "sync_id": f"sync_{int(time.time())}",
                            "estimated_duration": "30-60초",
                            "files_to_sync": api.get_file_count_estimate(),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        api.api_stats["syncs_triggered"] += 1
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        
                    except Exception as e:
                        error_response = {
                            "status": "오류",
                            "message": f"동기화 요청 처리 실패: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                
                elif self.path == '/api/status':
                    try:
                        sync_status = api.sync_system.get_sync_status()
                        
                        status_response = {
                            "sync_status": sync_status,
                            "api_stats": api.api_stats,
                            "system_info": {
                                "server_uptime": api.calculate_uptime(),
                                "active_syncs": 1 if sync_status["sync_active"] else 0,
                                "last_sync": sync_status["last_sync"]
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        self.wfile.write(json.dumps(status_response, ensure_ascii=False).encode('utf-8'))
                        
                    except Exception as e:
                        error_response = {
                            "status": "오류",
                            "message": f"상태 조회 실패: {str(e)}"
                        }
                        
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_GET(self):
                if self.path == '/':
                    # 간단한 상태 페이지
                    html_content = api.create_status_page()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    self.wfile.write(html_content.encode('utf-8'))
                
                elif self.path == '/api/status':
                    # GET으로도 상태 조회 가능
                    self.do_POST()
                
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def log_message(self, format, *args):
                # 로그 억제
                pass
        
        return Handler
    
    def perform_sync_with_callback(self, request_data):
        """콜백과 함께 동기화 실행"""
        try:
            print(f"🚀 백그라운드 동기화 시작...")
            
            # 실제 동기화 수행
            self.sync_system.perform_sync()
            
            print(f"✅ 백그라운드 동기화 완료!")
            
        except Exception as e:
            print(f"❌ 백그라운드 동기화 실패: {e}")
    
    def get_file_count_estimate(self):
        """동기화할 파일 수 추정"""
        try:
            db_files = ["evolution_agent.db", "super_unified_agent.db", "agent_network.db"]
            state_files = list(Path(".").glob("*_state.json"))
            
            return len(db_files) + len(state_files) + 1  # +1 for logs
        except:
            return 5
    
    def calculate_uptime(self):
        """서버 가동 시간 계산"""
        try:
            start_time = datetime.fromisoformat(self.api_stats["server_started"])
            uptime = datetime.now() - start_time
            
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            return f"{hours}시간 {minutes}분"
        except:
            return "알 수 없음"
    
    def create_status_page(self):
        """상태 페이지 HTML 생성"""
        sync_status = self.sync_system.get_sync_status()
        
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☁️ Cloud Sync API Status</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .status-card {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .status-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #4CAF50;
            margin-top: 10px;
        }}
        .api-endpoint {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }}
        .sync-button {{
            background: linear-gradient(45deg, #4CAF50, #45a049);
            border: none;
            border-radius: 25px;
            color: white;
            padding: 15px 30px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
            transition: transform 0.3s ease;
        }}
        .sync-button:hover {{
            transform: scale(1.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ Cloud Sync API Status</h1>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🔄 동기화 상태</h3>
                <div class="status-value">{'활성' if sync_status['sync_active'] else '대기 중'}</div>
                <p>마지막 동기화: {sync_status['last_sync'] or '없음'}</p>
            </div>
            
            <div class="status-card">
                <h3>📊 API 통계</h3>
                <div class="status-value">{self.api_stats['requests_handled']}</div>
                <p>처리된 요청 수</p>
                <p>트리거된 동기화: {self.api_stats['syncs_triggered']}회</p>
            </div>
            
            <div class="status-card">
                <h3>⏱️ 서버 정보</h3>
                <div class="status-value">{self.calculate_uptime()}</div>
                <p>가동 시간</p>
                <p>포트: {self.port}</p>
            </div>
            
            <div class="status-card">
                <h3>📁 파일 현황</h3>
                <div class="status-value">{sync_status['files_synced']}</div>
                <p>동기화된 파일</p>
                <p>총 크기: {sync_status['total_size'] / 1024 / 1024:.1f}MB</p>
            </div>
        </div>
        
        <h3>🔗 API 엔드포인트</h3>
        <div class="api-endpoint">
            POST /api/sync - 동기화 트리거
        </div>
        <div class="api-endpoint">
            GET /api/status - 상태 조회
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="sync-button" onclick="triggerSync()">🔄 수동 동기화</button>
            <button class="sync-button" onclick="refreshStatus()">📊 상태 새로고침</button>
        </div>
        
        <p style="text-align: center; margin-top: 20px; opacity: 0.8;">
            마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
    
    <script>
        function triggerSync() {{
            fetch('/api/sync', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{'source': 'web_interface', 'manual': true}})
            }})
            .then(response => response.json())
            .then(data => {{
                alert('동기화 요청이 전송되었습니다: ' + data.message);
            }})
            .catch(error => {{
                alert('동기화 요청 실패: ' + error.message);
            }});
        }}
        
        function refreshStatus() {{
            location.reload();
        }}
        
        // 30초마다 자동 새로고침
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
        """
    
    def start_api_server(self):
        """API 서버 시작"""
        try:
            handler = self.create_handler()
            server = HTTPServer(('localhost', self.port), handler)
            
            print(f"☁️ 클라우드 동기화 API 서버 시작")
            print(f"🔗 API URL: http://localhost:{self.port}")
            print(f"📊 상태 페이지: http://localhost:{self.port}")
            print(f"🔄 동기화 API: POST http://localhost:{self.port}/api/sync")
            
            # 자동 동기화 스케줄 시작
            self.sync_system.schedule_auto_sync()
            
            # 백그라운드에서 서버 실행
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            return server
            
        except Exception as e:
            print(f"❌ API 서버 시작 실패: {e}")
            return None

def main():
    api = CloudSyncAPI()
    server = api.start_api_server()
    
    if server:
        try:
            print("\n💡 API 서버 명령어:")
            print("   - 'sync': 수동 동기화")
            print("   - 'status': 서버 상태")
            print("   - 'quit': 종료")
            
            while True:
                command = input("\nAPI> ").strip().lower()
                
                if command == 'sync':
                    api.sync_system.force_sync()
                elif command == 'status':
                    stats = api.api_stats
                    sync_status = api.sync_system.get_sync_status()
                    print(f"서버 가동시간: {api.calculate_uptime()}")
                    print(f"처리된 요청: {stats['requests_handled']}개")
                    print(f"트리거된 동기화: {stats['syncs_triggered']}회")
                    print(f"동기화 상태: {'활성' if sync_status['sync_active'] else '대기'}")
                elif command == 'quit':
                    break
                else:
                    print("알 수 없는 명령어입니다.")
                    
        except KeyboardInterrupt:
            print("\n👋 클라우드 동기화 API 서버 종료")
            server.shutdown()

if __name__ == "__main__":
    main()
