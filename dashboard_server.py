#!/usr/bin/env python3
"""
실시간 웹 대시보드 서버
"""
from flask import Flask, render_template_string, jsonify
import json
from datetime import datetime
import threading

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang='ko'>
<head>
    <meta charset='UTF-8'>
    <title>통합 시스템 대시보드</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f3f7fa; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px #eee; }
        .metric { font-size: 2em; font-weight: bold; }
        .status-healthy { color: green; }
        .status-warning { color: orange; }
        .status-error { color: red; }
    </style>
</head>
<body>
    <h1>🚀 통합 개발 시스템 대시보드</h1>
    <div class='dashboard'>
        <div class='card'>
            <h2>📊 시스템 상태</h2>
            <div id='system-status'>로딩 중...</div>
        </div>
        <div class='card'>
            <h2>🎯 학습 목표</h2>
            <div id='learning-goals'>로딩 중...</div>
        </div>
        <div class='card'>
            <h2>📂 GitHub 활동</h2>
            <div id='github-activity'>로딩 중...</div>
        </div>
        <div class='card'>
            <h2>📈 성능 메트릭</h2>
            <canvas id='performance-chart' width='200' height='200'></canvas>
        </div>
    </div>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <script>
        function updateDashboard() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(data.system_health);
                    updateLearningGoals(data.learning_goals);
                    updateGithubActivity(data.github_activity);
                    updatePerformanceChart(data.performance_metrics);
                })
                .catch(error => console.error('데이터 로드 오류:', error));
        }
        function updateSystemStatus(data) {
            const statusDiv = document.getElementById('system-status');
            if (!data || data.error) {
                statusDiv.innerHTML = '데이터 없음';
                return;
            }
            const status = data.overall_status || 'unknown';
            let colorClass = 'status-healthy';
            if (status === 'warning') colorClass = 'status-warning';
            if (status === 'error') colorClass = 'status-error';
            statusDiv.innerHTML = `<span class='${colorClass}'>${status.toUpperCase()}</span>`;
        }
        function updateLearningGoals(data) {
            const goalsDiv = document.getElementById('learning-goals');
            if (!data || data.error) {
                goalsDiv.innerHTML = '데이터 없음';
                return;
            }
            goalsDiv.innerHTML = `총 목표: ${data.total_goals}<br>완료: ${data.completed_goals}<br>진행 중: ${data.in_progress}<br>진척률: ${data.completion_rate}%`;
        }
        function updateGithubActivity(data) {
            const activityDiv = document.getElementById('github-activity');
            if (!data || data.error) {
                activityDiv.innerHTML = '데이터 없음';
                return;
            }
            activityDiv.innerHTML = `오픈 이슈: ${data.open_issues}<br>완료 이슈: ${data.closed_issues}<br>활성 브랜치: ${data.active_branches}<br>최근 커밋: ${data.recent_commits}`;
        }
        function updatePerformanceChart(data) {
            if (!data || data.error) return;
            const ctx = document.getElementById('performance-chart').getContext('2d');
            if(window.performanceChart) window.performanceChart.destroy();
            window.performanceChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['성공', '에러'],
                    datasets: [{
                        data: [data.success_rate || 98, data.error_rate || 2],
                        backgroundColor: ['#4CAF50', '#F44336']
                    }]
                },
                options: { responsive: false, maintainAspectRatio: false }
            });
        }
        setInterval(updateDashboard, 5000);
        updateDashboard();
    </script>
</body>
</html>
"""

class DashboardManager:
    def __init__(self):
        pass
    def get_system_metrics(self):
        try:
            with open('monitoring_report.json', 'r', encoding='utf-8') as f:
                monitoring_data = json.load(f)
        except Exception as e:
            monitoring_data = {'error': str(e)}
        # 임시 목표/활동/성능 데이터 (실제 연동 시 확장)
        learning_goals = {
            'total_goals': 2,
            'completed_goals': 1,
            'in_progress': 1,
            'completion_rate': 50.0
        }
        github_activity = {
            'open_issues': 3,
            'closed_issues': 1,
            'active_branches': 2,
            'recent_commits': 5
        }
        performance_metrics = {
            'success_rate': 98.5,
            'error_rate': 1.5,
            'uptime': '99.9%'
        }
        return {
            'system_health': monitoring_data,
            'learning_goals': learning_goals,
            'github_activity': github_activity,
            'performance_metrics': performance_metrics
        }
dashboard = DashboardManager()

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/metrics')
def get_metrics():
    return jsonify(dashboard.get_system_metrics())

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

def run_dashboard():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    run_dashboard()
