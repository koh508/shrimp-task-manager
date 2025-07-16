#!/usr/bin/env python3
"""
간결한 대시보드 시스템
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
import logging

# 로깅 레벨을 WARNING으로 설정하여 불필요한 로그 줄이기
logging.basicConfig(level=logging.WARNING)

try:
    from flask import Flask, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

class SimpleDashboard:
    """간결한 대시보드"""
    
    def __init__(self):
        self.app = Flask(__name__) if FLASK_AVAILABLE else None
        self.setup_routes()
        
    def get_system_data(self) -> Dict[str, Any]:
        """시스템 데이터 수집"""
        try:
            import psutil
            
            # 디스크 사용량 (Windows/Linux 호환)
            try:
                disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
            except:
                disk = psutil.disk_usage('.')
            
            # 기본 시스템 정보
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system': {
                    'cpu': psutil.cpu_percent(),
                    'memory': psutil.virtual_memory().percent,
                    'disk': disk.percent,
                    'status': 'healthy'
                },
                'github': {
                    'token_set': bool(os.getenv('GITHUB_TOKEN')),
                    'repo_set': bool(os.getenv('REPO_NAME')),
                    'issues': 2
                },
                'components': {
                    'stability_monitor': os.path.exists('stability_monitor_fixed.py'),
                    'backup_system': os.path.exists('backup_system_fixed.py'),
                    'plugin_system': os.path.exists('plugin_system.py'),
                    'performance_optimizer': os.path.exists('performance_optimizer.py')
                }
            }
            
            # 헬스 리포트 로드
            if os.path.exists('health_report.json'):
                with open('health_report.json', 'r') as f:
                    health_data = json.load(f)
                    data['system']['status'] = health_data.get('overall_status', 'unknown')
            
            return data
            
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'system': {'status': 'error'}
            }
    
    def setup_routes(self):
        """라우트 설정"""
        if not self.app:
            return
            
        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify(self.get_system_data())
        
        @self.app.route('/api/health')
        def health():
            return jsonify({'status': 'ok', 'service': 'dashboard'})
    
    def get_html_template(self) -> str:
        """간결한 HTML 템플릿"""
        return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 시스템 대시보드</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 15px; }
        .metric { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .healthy { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
        .status-item { display: flex; justify-content: space-between; margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 5px; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px; }
        .refresh-btn:hover { background: #2980b9; }
        .timestamp { text-align: center; color: #7f8c8d; margin-top: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 시스템 대시보드</h1>
            <p>안정성 -  확장성 -  성능 -  사용성</p>
        </div>
        <div class="grid">
            <div class="card">
                <h3>📊 시스템 상태</h3>
                <div id="system-status" class="metric healthy">HEALTHY</div>
                <div class="status-item">CPU 사용률: <span id="cpu-usage">0%</span></div>
                <div class="status-item">메모리 사용률: <span id="memory-usage">0%</span></div>
                <div class="status-item">디스크 사용률: <span id="disk-usage">0%</span></div>
            </div>
            <div class="card">
                <h3>🔧 컴포넌트</h3>
                <div class="status-item">안정성 모니터: <span id="stability-status">❌</span></div>
                <div class="status-item">백업 시스템: <span id="backup-status">❌</span></div>
                <div class="status-item">플러그인 시스템: <span id="plugin-status">❌</span></div>
                <div class="status-item">성능 최적화: <span id="performance-status">❌</span></div>
            </div>
            <div class="card">
                <h3>📂 GitHub 연동</h3>
                <div class="status-item">토큰 설정: <span id="github-token">❌</span></div>
                <div class="status-item">저장소 설정: <span id="github-repo">❌</span></div>
                <div class="status-item">오픈 이슈: <span id="github-issues">0</span></div>
            </div>
            <div class="card">
                <h3>🎛️ 제어판</h3>
                <button class="refresh-btn" onclick="refreshData()">🔄 새로고침</button>
                <label style="margin-left:10px;"><input type="checkbox" id="auto-refresh" checked onchange="toggleAutoRefresh()"> ⏸️ 자동새로고침</label>
                <div style="margin-top:10px; color:#7f8c8d; font-size:0.9em;">자동 새로고침 (30초)</div>
            </div>
        </div>
        <div class="timestamp">마지막 업데이트: <span id="last-update">--</span></div>
    </div>
    <script>
        let autoRefreshInterval = null;
        let autoRefreshEnabled = true;
        
        async function fetchData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('데이터 로드 실패:', error);
            }
        }
        
        function updateDashboard(data) {
            if (data.error) {
                document.getElementById('system-status').textContent = 'ERROR';
                document.getElementById('system-status').className = 'metric error';
                return;
            }
            
            // 시스템 상태
            const status = data.system.status.toUpperCase();
            document.getElementById('system-status').textContent = status;
            document.getElementById('system-status').className = `metric ${data.system.status}`;
            
            document.getElementById('cpu-usage').textContent = data.system.cpu.toFixed(1) + '%';
            document.getElementById('memory-usage').textContent = data.system.memory.toFixed(1) + '%';
            document.getElementById('disk-usage').textContent = data.system.disk.toFixed(1) + '%';
            
            // 컴포넌트 상태
            document.getElementById('stability-status').textContent = data.components.stability_monitor ? '✅' : '❌';
            document.getElementById('backup-status').textContent = data.components.backup_system ? '✅' : '❌';
            document.getElementById('plugin-status').textContent = data.components.plugin_system ? '✅' : '❌';
            document.getElementById('performance-status').textContent = data.components.performance_optimizer ? '✅' : '❌';
            
            // GitHub 상태
            document.getElementById('github-token').textContent = data.github.token_set ? '✅' : '❌';
            document.getElementById('github-repo').textContent = data.github.repo_set ? '✅' : '❌';
            document.getElementById('github-issues').textContent = data.github.issues || 0;
            
            // 타임스탬프
            document.getElementById('last-update').textContent = data.timestamp;
        }
        
        function refreshData() {
            fetchData();
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('auto-refresh');
            autoRefreshEnabled = !autoRefreshEnabled;
            checkbox.checked = autoRefreshEnabled;
            
            if (autoRefreshEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        }
        
        function startAutoRefresh() {
            if (autoRefreshInterval) clearInterval(autoRefreshInterval);
            autoRefreshInterval = setInterval(fetchData, 30000); // 30초 간격
        }
        
        function stopAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
        }
        
        // 초기 로드
        fetchData();
        
        // 자동 새로고침 시작
        startAutoRefresh();
        
        // 체크박스 이벤트
        document.getElementById('auto-refresh').addEventListener('change', function(e) {
            autoRefreshEnabled = e.target.checked;
            if (autoRefreshEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    </script>
</body>
</html>
'''
    
    def run(self, host='127.0.0.1', port=5000):
        """대시보드 실행"""
        if not self.app:
            print("❌ Flask가 설치되지 않음")
            print("📥 설치: pip install flask")
            return
        
        print(f"🌐 간결한 대시보드 실행")
        print(f"📊 URL: http://{host}:{port}")
        print(f"🔄 자동 새로고침: 30초 간격")
        print(f"⏸️ Ctrl+C로 종료")
        
        # Flask 로그 레벨 조정
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        try:
            self.app.run(host=host, port=port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            print(f"\n🛑 대시보드 종료")

def main():
    """메인 함수"""
    dashboard = SimpleDashboard()
    
    # 데이터 테스트
    data = dashboard.get_system_data()
    print(f"📊 시스템 상태: {data['system']['status']}")
    print(f"💻 CPU: {data['system']['cpu']:.1f}%")
    print(f"🧠 메모리: {data['system']['memory']:.1f}%")
    print(f"💾 디스크: {data['system']['disk']:.1f}%")
    
    if FLASK_AVAILABLE:
        print(f"\n🚀 웹 대시보드 시작 중...")
        dashboard.run()
    else:
        print(f"\n⚠️ Flask 미설치")
        print(f"📥 설치 후 재실행: pip install flask")

if __name__ == "__main__":
    main()
