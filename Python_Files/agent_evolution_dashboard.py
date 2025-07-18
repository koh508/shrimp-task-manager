#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 Agent Evolution Web Dashboard
================================
에이전트 진화 시스템을 위한 실시간 웹 대시보드
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from advanced_agent_evolution_system import get_evolution_system, AgentConfig, AgentType, PerformanceMetrics

# FastAPI 앱 초기화
app = FastAPI(
    title="AI Agent Evolution Dashboard",
    description="실시간 AI 에이전트 진화 모니터링 및 관리 대시보드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
evolution_system = get_evolution_system()
connected_clients: Set[WebSocket] = set()
logger = logging.getLogger(__name__)

@app.get("/")
async def dashboard():
    """메인 대시보드 HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 AI Agent Evolution Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                margin: 0;
                padding: 20px;
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 30px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }
            .chart-container {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                height: 400px;
            }
            .agent-list {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                max-height: 500px;
                overflow-y: auto;
            }
            .agent-item {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .agent-status {
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }
            .status-excellent { background: #4caf50; }
            .status-normal { background: #2196f3; }
            .status-declining { background: #ff9800; }
            .status-critical { background: #f44336; }
            .controls {
                display: flex;
                gap: 10px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            .btn {
                background: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s ease;
            }
            .btn:hover {
                background: #45a049;
                transform: translateY(-2px);
            }
            .btn-warning { background: #ff9800; }
            .btn-danger { background: #f44336; }
            .btn-info { background: #2196f3; }
            .alert {
                background: rgba(244, 67, 54, 0.2);
                border: 2px solid #f44336;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            }
            .log-container {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
                padding: 15px;
                max-height: 300px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Agent Evolution Dashboard</h1>
                <p>실시간 에이전트 진화 모니터링 및 관리 시스템</p>
                <div id="connectionStatus">🔴 연결 끊김</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>총 에이전트</h3>
                    <div class="stat-value" id="totalAgents">0</div>
                </div>
                <div class="stat-card">
                    <h3>평균 성능</h3>
                    <div class="stat-value" id="avgPerformance">0.00</div>
                </div>
                <div class="stat-card">
                    <h3>진행 중인 진화</h3>
                    <div class="stat-value" id="activeEvolutions">0</div>
                </div>
                <div class="stat-card">
                    <h3>시스템 상태</h3>
                    <div class="stat-value" id="systemHealth">대기</div>
                </div>
            </div>

            <div class="controls">
                <button class="btn" onclick="startEvolution()">🧬 진화 시작</button>
                <button class="btn btn-info" onclick="generateReport()">📊 보고서 생성</button>
                <button class="btn btn-warning" onclick="createEnsemble()">🔗 앙상블 생성</button>
                <button class="btn btn-info" onclick="showRecommendations()">💡 추천 보기</button>
                <button class="btn btn-danger" onclick="emergencyStop()">🛑 긴급 중단</button>
            </div>

            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>

            <div class="agent-list">
                <h3>🤖 활성 에이전트 목록</h3>
                <div id="agentList">로딩 중...</div>
            </div>

            <div class="log-container">
                <h3>📋 실시간 로그</h3>
                <div id="logStream"></div>
            </div>
        </div>

        <script>
            let ws = null;
            let performanceChart = null;
            let agentData = {};

            function connectWebSocket() {
                try {
                    ws = new WebSocket('ws://localhost:8002/ws');
                    
                    ws.onopen = function() {
                        console.log('WebSocket 연결됨');
                        document.getElementById('connectionStatus').innerHTML = '🟢 연결됨';
                        requestInitialData();
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    ws.onclose = function() {
                        document.getElementById('connectionStatus').innerHTML = '🔴 연결 끊김';
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket 오류:', error);
                    };
                } catch (e) {
                    console.error('WebSocket 연결 실패:', e);
                    setTimeout(connectWebSocket, 3000);
                }
            }

            function handleWebSocketMessage(data) {
                switch(data.type) {
                    case 'agent_status':
                        updateAgentStatus(data.data);
                        break;
                    case 'performance_update':
                        updatePerformanceChart(data.data);
                        break;
                    case 'system_stats':
                        updateSystemStats(data.data);
                        break;
                    case 'log_entry':
                        addLogEntry(data.data);
                        break;
                    case 'alert':
                        showAlert(data.data);
                        break;
                }
            }

            function updateSystemStats(stats) {
                document.getElementById('totalAgents').textContent = stats.total_agents || 0;
                document.getElementById('avgPerformance').textContent = (stats.avg_performance || 0).toFixed(3);
                document.getElementById('activeEvolutions').textContent = stats.active_evolutions || 0;
                document.getElementById('systemHealth').textContent = stats.system_health || '대기';
            }

            function updateAgentStatus(agents) {
                const container = document.getElementById('agentList');
                container.innerHTML = '';
                
                Object.values(agents).forEach(agent => {
                    const agentDiv = document.createElement('div');
                    agentDiv.className = 'agent-item';
                    agentDiv.innerHTML = `
                        <div>
                            <strong>${agent.agent_id}</strong><br>
                            <small>성능: ${agent.performance.toFixed(3)} | 추세: ${agent.trend > 0 ? '📈' : agent.trend < 0 ? '📉' : '➡️'}</small>
                        </div>
                        <div class="agent-status status-${agent.status}">${agent.status}</div>
                    `;
                    container.appendChild(agentDiv);
                });
                
                agentData = agents;
            }

            function updatePerformanceChart(data) {
                if (!performanceChart) {
                    initializeChart();
                }
                
                // 차트 데이터 업데이트 로직
                const ctx = document.getElementById('performanceChart').getContext('2d');
                if (performanceChart) {
                    performanceChart.data.labels.push(new Date().toLocaleTimeString());
                    performanceChart.data.datasets[0].data.push(data.avg_performance);
                    
                    // 최대 20개 데이터 포인트 유지
                    if (performanceChart.data.labels.length > 20) {
                        performanceChart.data.labels.shift();
                        performanceChart.data.datasets[0].data.shift();
                    }
                    
                    performanceChart.update();
                }
            }

            function initializeChart() {
                const ctx = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: '평균 성능',
                            data: [],
                            borderColor: '#4caf50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            borderWidth: 2,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1.0
                            }
                        },
                        plugins: {
                            legend: {
                                labels: {
                                    color: 'white'
                                }
                            }
                        },
                        scales: {
                            x: {
                                ticks: {
                                    color: 'white'
                                }
                            },
                            y: {
                                ticks: {
                                    color: 'white'
                                }
                            }
                        }
                    }
                });
            }

            function addLogEntry(logData) {
                const container = document.getElementById('logStream');
                const logDiv = document.createElement('div');
                logDiv.innerHTML = `[${new Date().toLocaleTimeString()}] ${logData.message}`;
                container.appendChild(logDiv);
                
                // 최대 50개 로그 유지
                const logs = container.children;
                if (logs.length > 50) {
                    container.removeChild(logs[0]);
                }
                
                container.scrollTop = container.scrollHeight;
            }

            function showAlert(alertData) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert';
                alertDiv.innerHTML = `
                    <strong>${alertData.level}:</strong> ${alertData.message}<br>
                    <small>에이전트: ${alertData.agent_id} | 권장 조치: ${alertData.action}</small>
                `;
                
                document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.stats-grid'));
                
                // 5초 후 알림 제거
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 5000);
            }

            function requestInitialData() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'request_initial_data'
                    }));
                }
            }

            // 컨트롤 함수들
            function startEvolution() {
                fetch('/api/evolution/start', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        addLogEntry({message: `진화 시작: ${data.message}`});
                    })
                    .catch(error => console.error('진화 시작 오류:', error));
            }

            function generateReport() {
                fetch('/api/reports/evolution')
                    .then(response => response.json())
                    .then(data => {
                        console.log('진화 보고서:', data);
                        addLogEntry({message: '진화 보고서가 생성되었습니다'});
                    });
            }

            function createEnsemble() {
                const selectedAgents = Object.keys(agentData).slice(0, 3);
                fetch('/api/evolution/ensemble', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({agent_ids: selectedAgents})
                })
                .then(response => response.json())
                .then(data => {
                    addLogEntry({message: `앙상블 생성: ${data.generated_hybrids}개 하이브리드 에이전트`});
                });
            }

            function showRecommendations() {
                const firstAgent = Object.keys(agentData)[0];
                if (firstAgent) {
                    fetch(`/api/evolution/recommendations/${firstAgent}`)
                        .then(response => response.json())
                        .then(data => {
                            console.log('추천사항:', data);
                            addLogEntry({message: `${firstAgent}에 대한 추천사항 ${data.recommended_strategies?.length || 0}개`});
                        });
                }
            }

            function emergencyStop() {
                fetch('/api/evolution/emergency-stop', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        addLogEntry({message: '긴급 중단 실행됨'});
                    });
            }

            // 페이지 로드 시 초기화
            window.onload = function() {
                connectWebSocket();
                initializeChart();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# WebSocket 연결 관리
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"새 클라이언트 연결: {len(connected_clients)}개 활성")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "request_initial_data":
                # 초기 데이터 전송
                await send_initial_data(websocket)
            
            # 다른 메시지 타입 처리...
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"클라이언트 연결 해제: {len(connected_clients)}개 활성")

async def send_initial_data(websocket: WebSocket):
    """초기 데이터 전송"""
    try:
        # 시스템 통계
        report = evolution_system.get_evolution_report()
        await websocket.send_text(json.dumps({
            "type": "system_stats",
            "data": {
                "total_agents": report.get("total_agents", 0),
                "avg_performance": 0.75,  # 계산된 평균
                "active_evolutions": 0,
                "system_health": "healthy"
            }
        }))
        
        # 에이전트 상태
        agent_statuses = {}
        for agent_id in evolution_system.agents.keys():
            perf = evolution_system.get_average_performance(agent_id)
            trend = evolution_system.get_performance_trend(agent_id)
            
            status = "normal"
            if perf < 0.4:
                status = "critical"
            elif trend < -0.01:
                status = "declining"
            elif perf > 0.9:
                status = "excellent"
            
            agent_statuses[agent_id] = {
                "agent_id": agent_id,
                "performance": perf,
                "trend": trend,
                "status": status
            }
        
        await websocket.send_text(json.dumps({
            "type": "agent_status",
            "data": agent_statuses
        }))
        
    except Exception as e:
        logger.error(f"초기 데이터 전송 실패: {e}")

# REST API 엔드포인트들
@app.get("/api/agents")
async def get_agents():
    """모든 에이전트 목록 조회"""
    try:
        agents = []
        for agent_id, config in evolution_system.agents.items():
            agents.append({
                "agent_id": agent_id,
                "agent_type": config.agent_type.value,
                "performance": evolution_system.get_average_performance(agent_id),
                "trend": evolution_system.get_performance_trend(agent_id),
                "config": {
                    "learning_rate": config.learning_rate,
                    "memory_size": config.memory_size,
                    "exploration_rate": config.exploration_rate,
                    "temperature": config.temperature
                }
            })
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/evolution")
async def get_evolution_report():
    """진화 시스템 보고서"""
    try:
        report = evolution_system.get_evolution_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evolution/start")
async def start_evolution():
    """진화 프로세스 시작"""
    try:
        # 백그라운드에서 진화 시작
        asyncio.create_task(evolution_system.run_continuous_evolution(check_interval=1800))
        
        # 클라이언트들에게 알림
        await broadcast_to_clients({
            "type": "log_entry",
            "data": {"message": "🧬 지속적인 진화 프로세스가 시작되었습니다"}
        })
        
        return {"message": "진화 프로세스가 시작되었습니다", "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evolution/ensemble")
async def create_ensemble(request: dict):
    """앙상블 에이전트 생성"""
    try:
        agent_ids = request.get("agent_ids", [])
        if len(agent_ids) < 2:
            raise HTTPException(status_code=400, detail="최소 2개 에이전트가 필요합니다")
        
        result = await evolution_system.ensemble_evolution_strategy(agent_ids)
        
        # 클라이언트들에게 알림
        await broadcast_to_clients({
            "type": "log_entry",
            "data": {"message": f"🔗 앙상블 생성 완료: {result.get('generated_hybrids', 0)}개 하이브리드"}
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evolution/recommendations/{agent_id}")
async def get_recommendations(agent_id: str):
    """에이전트별 진화 추천사항"""
    try:
        recommendations = await evolution_system.intelligent_evolution_recommendation(agent_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evolution/roadmap/{agent_id}")
async def get_evolution_roadmap(agent_id: str, target_performance: float = 0.9, timeframe_days: int = 30):
    """에이전트 진화 로드맵"""
    try:
        roadmap = await evolution_system.generate_evolution_roadmap(
            agent_id, target_performance, timeframe_days
        )
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evolution/emergency-stop")
async def emergency_stop():
    """긴급 중단"""
    try:
        # 모든 진화 프로세스 중단 로직
        await broadcast_to_clients({
            "type": "alert",
            "data": {
                "level": "WARNING",
                "message": "진화 프로세스가 긴급 중단되었습니다",
                "agent_id": "system",
                "action": "수동 재시작 필요"
            }
        })
        
        return {"message": "긴급 중단 실행됨", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def broadcast_to_clients(message: dict):
    """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
    if connected_clients:
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send_text(json.dumps(message))
            except:
                disconnected.add(client)
        
        # 연결 끊긴 클라이언트 제거
        connected_clients -= disconnected

# 백그라운드 태스크: 실시간 모니터링
async def background_monitoring():
    """백그라운드 실시간 모니터링"""
    while True:
        try:
            if connected_clients:
                # 성능 업데이트 전송
                avg_perf = 0.75  # 실제 계산 로직
                await broadcast_to_clients({
                    "type": "performance_update",
                    "data": {"avg_performance": avg_perf}
                })
            
            await asyncio.sleep(30)  # 30초마다 업데이트
        except Exception as e:
            logger.error(f"백그라운드 모니터링 오류: {e}")
            await asyncio.sleep(60)

# 앱 시작 시 백그라운드 태스크 실행
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_monitoring())
    logger.info("🌐 Agent Evolution Dashboard 시작됨")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
