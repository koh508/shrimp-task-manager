#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ 빠른 에이전트 API 서버
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import threading
import sys
import os
import time
import random

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.getcwd())

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 글로벌 에이전트 시스템
agent_system = None

def init_agents():
    """에이전트 시스템 초기화"""
    global agent_system
    try:
        from advanced_agent_evolution_system import get_evolution_system, AgentConfig, AgentType, PerformanceMetrics
        
        agent_system = get_evolution_system()
        
        # 빠른 에이전트 3개 생성
        agents = [
            AgentConfig("api_agent_1", AgentType.LEARNING, 0.1, 300, 0.1),
            AgentConfig("api_agent_2", AgentType.GOAL_ORIENTED, 0.08, 250, 0.15),
            AgentConfig("api_agent_3", AgentType.CONVERSATIONAL, 0.12, 280, 0.12)
        ]
        
        for agent in agents:
            agent_system.register_agent(agent)
            
            # 초기 성능 데이터 추가
            for i in range(3):
                metrics = PerformanceMetrics(
                    accuracy=random.uniform(0.75, 0.9),
                    response_time=random.uniform(0.2, 0.8),
                    user_satisfaction=random.uniform(0.8, 0.95),
                    task_completion_rate=random.uniform(0.9, 0.98),
                    error_rate=random.uniform(0.01, 0.04),
                    learning_speed=random.uniform(0.7, 0.9),
                    adaptability=random.uniform(0.75, 0.9)
                )
                agent_system.record_performance(agent.agent_id, metrics)
        
        print("✅ 에이전트 시스템 초기화 완료")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 초기화 실패: {e}")
        return False

@app.route('/api/status', methods=['GET'])
def get_status():
    """시스템 상태 API"""
    global agent_system
    
    if not agent_system:
        return jsonify({
            "status": "initializing",
            "message": "에이전트 시스템 초기화 중...",
            "agents": 0
        }), 200
    
    try:
        report = agent_system.get_evolution_report()
        
        agent_details = []
        for agent_id in agent_system.agents.keys():
            perf = agent_system.get_average_performance(agent_id)
            trend = agent_system.get_performance_trend(agent_id)
            
            agent_details.append({
                "id": agent_id,
                "type": agent_system.agents[agent_id].agent_type.value,
                "performance": round(perf, 3),
                "trend": round(trend, 4),
                "status": "active"
            })
        
        return jsonify({
            "status": "running",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_agents": report.get('total_agents', 0),
            "agent_types": report.get('agent_types', {}),
            "agents": agent_details,
            "system_health": "good"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"상태 조회 실패: {str(e)}",
            "agents": 0
        }), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """에이전트 목록 API"""
    global agent_system
    
    if not agent_system:
        return jsonify({"agents": []}), 200
    
    try:
        agents = []
        for agent_id, config in agent_system.agents.items():
            perf = agent_system.get_average_performance(agent_id)
            trend = agent_system.get_performance_trend(agent_id)
            
            agents.append({
                "id": agent_id,
                "type": config.agent_type.value,
                "learning_rate": config.learning_rate,
                "memory_size": config.memory_size,
                "exploration_rate": config.exploration_rate,
                "performance": round(perf, 3),
                "trend": round(trend, 4),
                "status": "active"
            })
        
        return jsonify({"agents": agents}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/evolve/<agent_id>', methods=['POST'])
def evolve_agent(agent_id):
    """에이전트 진화 API"""
    global agent_system
    
    if not agent_system:
        return jsonify({"error": "에이전트 시스템이 초기화되지 않았습니다"}), 400
    
    try:
        # 비동기 진화를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        evolved = loop.run_until_complete(agent_system.safe_evolve_agent(agent_id))
        loop.close()
        
        if evolved:
            return jsonify({
                "success": True,
                "message": f"에이전트 진화 성공",
                "original_id": agent_id,
                "evolved_id": evolved.agent_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "진화에서 개선 사항 없음"
            }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/performance/<agent_id>', methods=['POST'])
def update_performance(agent_id):
    """성능 업데이트 API"""
    global agent_system
    
    if not agent_system:
        return jsonify({"error": "에이전트 시스템이 초기화되지 않았습니다"}), 400
    
    try:
        # 랜덤 성능 데이터 생성 (실제로는 클라이언트에서 전송)
        from advanced_agent_evolution_system import PerformanceMetrics
        
        metrics = PerformanceMetrics(
            accuracy=random.uniform(0.7, 0.95),
            response_time=random.uniform(0.1, 1.0),
            user_satisfaction=random.uniform(0.8, 0.95),
            task_completion_rate=random.uniform(0.85, 0.98),
            error_rate=random.uniform(0.01, 0.05),
            learning_speed=random.uniform(0.6, 0.9),
            adaptability=random.uniform(0.7, 0.9)
        )
        
        success = agent_system.record_performance(agent_id, metrics)
        
        if success:
            perf = agent_system.get_average_performance(agent_id)
            return jsonify({
                "success": True,
                "average_performance": round(perf, 3)
            }), 200
        else:
            return jsonify({"error": "성능 기록 실패"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크 API"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "service": "Agent Evolution API"
    }), 200

@app.route('/health', methods=['GET'])
def health_check_simple():
    """간단한 헬스 체크 API (플러그인용)"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "service": "Agent Evolution API",
        "agents_count": len(agent_system.agents) if agent_system else 0
    }), 200

@app.route('/', methods=['GET'])
def root():
    """루트 경로 - API 정보"""
    return jsonify({
        "service": "Agent Evolution API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/status",
            "/api/agents", 
            "/api/evolve/<agent_id>",
            "/api/performance/<agent_id>",
            "/api/health"
        ],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route('/status', methods=['GET'])
def status_simple():
    """간단한 상태 확인"""
    global agent_system
    return jsonify({
        "status": "running",
        "agents": len(agent_system.agents) if agent_system else 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route('/agents', methods=['GET'])
def agents_simple():
    """간단한 에이전트 목록"""
    global agent_system
    
    if not agent_system:
        return jsonify({"agents": [], "count": 0}), 200
    
    try:
        agents_info = []
        for agent_id, config in agent_system.agents.items():
            perf = agent_system.get_average_performance(agent_id)
            agents_info.append({
                "id": agent_id,
                "type": config.agent_type.value,
                "performance": round(perf, 3),
                "status": "active"
            })
        
        return jsonify({
            "agents": agents_info,
            "count": len(agents_info),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        "error": "Not Found",
        "message": "요청한 URL을 찾을 수 없습니다",
        "available_endpoints": [
            "/",
            "/health",
            "/status", 
            "/agents",
            "/api/status",
            "/api/agents",
            "/api/health"
        ],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 404

def run_background_updates():
    """백그라운드에서 성능 업데이트"""
    global agent_system
    
    while True:
        try:
            if agent_system and agent_system.agents:
                from advanced_agent_evolution_system import PerformanceMetrics
                
                # 각 에이전트의 성능을 랜덤하게 업데이트
                for agent_id in list(agent_system.agents.keys()):
                    metrics = PerformanceMetrics(
                        accuracy=random.uniform(0.75, 0.92),
                        response_time=random.uniform(0.2, 0.9),
                        user_satisfaction=random.uniform(0.82, 0.96),
                        task_completion_rate=random.uniform(0.88, 0.99),
                        error_rate=random.uniform(0.01, 0.04),
                        learning_speed=random.uniform(0.7, 0.9),
                        adaptability=random.uniform(0.75, 0.9)
                    )
                    agent_system.record_performance(agent_id, metrics)
                
                print(f"📊 {time.strftime('%H:%M:%S')} - 성능 데이터 업데이트 완료")
            
        except Exception as e:
            print(f"⚠️ 백그라운드 업데이트 오류: {e}")
        
        time.sleep(30)  # 30초마다 업데이트

if __name__ == '__main__':
    print("🚀 에이전트 API 서버 시작...")
    
    # 에이전트 시스템 초기화
    if init_agents():
        # 백그라운드 업데이트 스레드 시작
        update_thread = threading.Thread(target=run_background_updates, daemon=True)
        update_thread.start()
        
        print("✅ API 서버가 http://localhost:8001 에서 실행 중...")
        print("📊 백그라운드 성능 업데이트 시작...")
        
        # Flask 서버 시작
        app.run(host='0.0.0.0', port=8001, debug=False)
    else:
        print("❌ 에이전트 시스템 초기화 실패")
