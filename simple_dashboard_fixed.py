#!/usr/bin/env python3
"""
간단한 대시보드 시스템 (수정 버전 - 순수 Python)
"""
import http.server
import json
import os
import socketserver
import threading
import time
from datetime import datetime

PORT = 5000
REFRESH_INTERVAL = 5  # 5초마다 새로고침

def get_system_status():
    """시스템 상태 데이터 수집"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'HEALTHY',
        'components': [],
        'metrics': {}
    }

    # 파일 존재 여부 확인
    core_files = [
        'run_system_fixed.py',
        'comprehensive_test.py',
        'stability_monitor_fixed.py',
        'backup_system_fixed.py',
        'plugin_system.py',
        'integrated_development_system.py'
    ]

    files_present = all(os.path.exists(f) for f in core_files)
    status['components'].append({
        'name': 'Core Files',
        'status': 'OK' if files_present else 'MISSING',
        'details': f'{sum(os.path.exists(f) for f in core_files)}/{len(core_files)} files present'
    })

    # 백업 상태 확인
    if os.path.exists('backups'):
        backups = os.listdir('backups')
        status['components'].append({
            'name': 'Backup System',
            'status': 'OK',
            'details': f'{len(backups)} backups found'
        })
    else:
        status['components'].append({
            'name': 'Backup System',
            'status': 'NOT_FOUND',
            'details': 'Backup directory not found'
        })

    # 안정성 리포트 확인
    if os.path.exists('health_report.json'):
        try:
            with open('health_report.json', 'r') as f:
                health_report = json.load(f)
            status['components'].append({
                'name': 'Stability Monitor',
                'status': health_report.get('overall_status', 'UNKNOWN').upper(),
                'details': f"Last check: {health_report.get('timestamp')}"
            })
            status['metrics']['memory_usage_percent'] = health_report.get('memory_info', {}).get('usage_percent', 0)
        except (json.JSONDecodeError, IOError):
            status['components'].append({'name': 'Stability Monitor', 'status': 'ERROR', 'details': 'Could not read report'})
    else:
        status['components'].append({'name': 'Stability Monitor', 'status': 'NOT_RUN', 'details': 'No report found'})

    # 전체 상태 결정
    if any(c['status'] not in ['OK', 'HEALTHY'] for c in status['components']):
        status['overall_status'] = 'WARNING'

    return status

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status_data = get_system_status()
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = self.generate_html()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()

    def generate_html(self):
        """HTML 페이지 생성"""
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>통합 시스템 대시보드</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e1e; color: #d4d4d4; margin: 20px; }}
                h1, h2 {{ color: #4ec9b0; border-bottom: 2px solid #4ec9b0; padding-bottom: 10px; }}
                .container {{ max-width: 800px; margin: auto; background-color: #252526; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }}
                .status-box {{ border: 1px solid #3e3e42; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                .status-HEALTHY {{ border-left: 5px solid #3f9; color: #3f9; }}
                .status-WARNING {{ border-left: 5px solid #fd9; color: #fd9; }}
                .status-ERROR, .status-MISSING {{ border-left: 5px solid #f66; color: #f66; }}
                #last-updated {{ font-size: 0.9em; color: #9cdcfe; text-align: right; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 통합 시스템 대시보드</h1>
                <p id="last-updated">마지막 업데이트: </p>

                <h2>📊 시스템 상태</h2>
                <div id="overall-status" class="status-box"></div>

                <h2>🔧 컴포넌트 상태</h2>
                <div id="components-status"></div>
            </div>

            <script>
                function updateStatus() {{
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {{
                            document.getElementById('last-updated').innerText = `마지막 업데이트: ${new Date(data.timestamp).toLocaleTimeString()}`;

                            const overallStatusDiv = document.getElementById('overall-status');
                            overallStatusDiv.className = `status-box status-${data.overall_status}`;
                            overallStatusDiv.innerHTML = `<strong>전체 상태:</strong> ${data.overall_status}`;

                            const componentsDiv = document.getElementById('components-status');
                            componentsDiv.innerHTML = '';
                            data.components.forEach(c => {{
                                const componentDiv = document.createElement('div');
                                componentDiv.className = `status-box status-${c.status}`;
                                componentDiv.innerHTML = `<strong>${c.name}:</strong> ${c.status} <br><small>${c.details}</small>`;
                                componentsDiv.appendChild(componentDiv);
                            }});
                        }})
                        .catch(error => console.error('상태 업데이트 오류:', error));
                }}

                setInterval(updateStatus, {REFRESH_INTERVAL * 1000});
                updateStatus(); // 초기 로드
            </script>
        </body>
        </html>
        """

def run_dashboard():
    """대시보드 서버 실행"""
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print("🎨 간단한 대시보드 시스템")
        print("=" * 50)
        print(f"🌐 대시보드 시작: http://127.0.0.1:{PORT}")
        print("⏸️ Ctrl+C로 종료")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        print("\n🛑 대시보드 종료")

if __name__ == "__main__":
    run_dashboard()
