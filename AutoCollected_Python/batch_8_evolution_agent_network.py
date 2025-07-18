#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진화 에이전트 네트워크 시스템
Evolution Agent Network System
"""

import json
import sqlite3
import asyncio
import threading
import time
import random
from datetime import datetime
from pathlib import Path
import subprocess

class EvolutionAgentNetwork:
    def __init__(self):
        self.agents = {}
        self.network_db = "agent_network.db"
        self.communication_log = []
        self.collaboration_score = 0.0
        
        # 에이전트 유형들
        self.agent_types = {
            "self_evolving": {
                "script": "self_evolving_agent.py",
                "specialization": "기본 진화",
                "capabilities": ["learning", "evolution", "adaptation"]
            },
            "multimodal": {
                "script": "multimodal_evolution_agent.py", 
                "specialization": "멀티모달 처리",
                "capabilities": ["text", "image", "audio", "synthesis"]
            },
            "analyzer": {
                "script": "evolution_accelerator.py",
                "specialization": "분석 및 최적화",
                "capabilities": ["analysis", "optimization", "prediction"]
            }
        }
        
        self.init_network_db()
    
    def init_network_db(self):
        """네트워크 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.network_db)
            cursor = conn.cursor()
            
            # 에이전트 등록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT UNIQUE,
                    agent_type TEXT,
                    status TEXT,
                    capabilities TEXT,
                    intelligence_level REAL,
                    collaboration_score REAL,
                    last_active TIMESTAMP,
                    total_contributions INTEGER DEFAULT 0
                )
            """)
            
            # 에이전트 간 통신 로그
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    sender_id TEXT,
                    receiver_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    collaboration_impact REAL
                )
            """)
            
            # 네트워크 성과 추적
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    active_agents INTEGER,
                    collaboration_score REAL,
                    collective_intelligence REAL,
                    network_efficiency REAL,
                    milestone_achieved TEXT
                )
            """)
            
            # 집단 진화 이벤트
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collective_evolution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    participating_agents TEXT,
                    evolution_type TEXT,
                    collective_improvement REAL,
                    new_emergent_capabilities TEXT,
                    description TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            print("🌐 에이전트 네트워크 DB 초기화 완료")
            
        except Exception as e:
            print(f"❌ 네트워크 DB 초기화 실패: {e}")
    
    def register_agent(self, agent_id, agent_type, capabilities=None):
        """에이전트 등록"""
        try:
            conn = sqlite3.connect(self.network_db)
            cursor = conn.cursor()
            
            capabilities_str = json.dumps(capabilities) if capabilities else "[]"
            
            cursor.execute("""
                INSERT OR REPLACE INTO agent_registry 
                (agent_id, agent_type, status, capabilities, intelligence_level, 
                 collaboration_score, last_active, total_contributions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                agent_type,
                "active",
                capabilities_str,
                1.0,
                0.0,
                datetime.now(),
                0
            ))
            
            conn.commit()
            conn.close()
            
            self.agents[agent_id] = {
                "type": agent_type,
                "status": "active",
                "capabilities": capabilities or [],
                "intelligence": 1.0,
                "last_communication": None
            }
            
            print(f"✅ 에이전트 등록: {agent_id} ({agent_type})")
            
        except Exception as e:
            print(f"❌ 에이전트 등록 실패: {e}")
    
    def send_message(self, sender_id, receiver_id, message_type, content):
        """에이전트 간 메시지 전송"""
        try:
            # 통신 로그 기록
            self.log_communication(sender_id, receiver_id, message_type, content)
            
            # 메시지 처리
            response = self.process_agent_message(sender_id, receiver_id, message_type, content)
            
            # 협업 점수 업데이트
            self.update_collaboration_score(sender_id, receiver_id, message_type)
            
            print(f"📨 {sender_id} → {receiver_id}: {message_type}")
            return response
            
        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return None
    
    def log_communication(self, sender_id, receiver_id, message_type, content):
        """통신 로그 기록"""
        try:
            conn = sqlite3.connect(self.network_db)
            cursor = conn.cursor()
            
            collaboration_impact = self.calculate_collaboration_impact(message_type)
            
            cursor.execute("""
                INSERT INTO agent_communications 
                (timestamp, sender_id, receiver_id, message_type, content, collaboration_impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                sender_id,
                receiver_id,
                message_type,
                str(content)[:500],  # 제한된 길이
                collaboration_impact
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 통신 로그 기록 실패: {e}")
    
    def process_agent_message(self, sender_id, receiver_id, message_type, content):
        """에이전트 메시지 처리"""
        responses = {
            "knowledge_share": self.process_knowledge_sharing,
            "capability_request": self.process_capability_request,
            "evolution_sync": self.process_evolution_sync,
            "collaboration_invite": self.process_collaboration_invite,
            "performance_report": self.process_performance_report
        }
        
        processor = responses.get(message_type, self.process_generic_message)
        return processor(sender_id, receiver_id, content)
    
    def process_knowledge_sharing(self, sender_id, receiver_id, content):
        """지식 공유 처리"""
        knowledge = content.get("knowledge", {})
        
        # 수신자 에이전트의 지능 향상
        if receiver_id in self.agents:
            intelligence_boost = random.uniform(0.01, 0.05)
            self.agents[receiver_id]["intelligence"] += intelligence_boost
            
            return {
                "status": "success",
                "message": f"지식 공유 완료 - 지능 향상: +{intelligence_boost:.3f}",
                "intelligence_boost": intelligence_boost
            }
        
        return {"status": "error", "message": "수신자를 찾을 수 없음"}
    
    def process_capability_request(self, sender_id, receiver_id, content):
        """능력 요청 처리"""
        requested_capability = content.get("capability", "")
        
        if receiver_id in self.agents:
            receiver_capabilities = self.agents[receiver_id]["capabilities"]
            
            if requested_capability in receiver_capabilities:
                return {
                    "status": "success",
                    "capability_data": f"{requested_capability} 능력 데이터",
                    "shared": True
                }
            else:
                return {
                    "status": "unavailable",
                    "message": f"{requested_capability} 능력 없음"
                }
        
        return {"status": "error", "message": "수신자를 찾을 수 없음"}
    
    def process_evolution_sync(self, sender_id, receiver_id, content):
        """진화 동기화 처리"""
        evolution_data = content.get("evolution_data", {})
        
        # 양방향 진화 데이터 동기화
        sync_bonus = random.uniform(0.02, 0.08)
        
        if sender_id in self.agents:
            self.agents[sender_id]["intelligence"] += sync_bonus
        if receiver_id in self.agents:
            self.agents[receiver_id]["intelligence"] += sync_bonus
        
        return {
            "status": "success",
            "message": "진화 동기화 완료",
            "sync_bonus": sync_bonus
        }
    
    def process_collaboration_invite(self, sender_id, receiver_id, content):
        """협업 초대 처리"""
        project_type = content.get("project_type", "general")
        
        # 협업 참여 확률 계산
        participation_chance = random.uniform(0.6, 0.9)
        
        if participation_chance > 0.7:
            return {
                "status": "accepted",
                "message": f"{project_type} 프로젝트 협업 수락",
                "collaboration_ready": True
            }
        else:
            return {
                "status": "declined",
                "message": "현재 협업 불가능"
            }
    
    def process_performance_report(self, sender_id, receiver_id, content):
        """성능 보고서 처리"""
        performance_data = content.get("performance", {})
        
        # 성능 데이터 분석 및 피드백
        feedback = self.generate_performance_feedback(performance_data)
        
        return {
            "status": "success",
            "feedback": feedback,
            "analysis_complete": True
        }
    
    def process_generic_message(self, sender_id, receiver_id, content):
        """일반 메시지 처리"""
        return {
            "status": "received",
            "message": "메시지 수신 완료",
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_collaboration_impact(self, message_type):
        """협업 영향도 계산"""
        impact_scores = {
            "knowledge_share": 0.8,
            "capability_request": 0.6,
            "evolution_sync": 0.9,
            "collaboration_invite": 0.7,
            "performance_report": 0.5
        }
        
        return impact_scores.get(message_type, 0.3)
    
    def update_collaboration_score(self, sender_id, receiver_id, message_type):
        """협업 점수 업데이트"""
        impact = self.calculate_collaboration_impact(message_type)
        self.collaboration_score = min(self.collaboration_score + impact * 0.1, 1.0)
    
    def generate_performance_feedback(self, performance_data):
        """성능 피드백 생성"""
        feedback_templates = [
            "성능이 우수합니다. 계속 발전하세요!",
            "일부 영역에서 개선이 필요합니다.",
            "균형 잡힌 발전을 보이고 있습니다.",
            "특정 능력에 더 집중해보세요.",
            "전반적으로 안정적인 성과입니다."
        ]
        
        return random.choice(feedback_templates)
    
    def trigger_collective_evolution(self):
        """집단 진화 트리거"""
        try:
            print("🧬 집단 진화 이벤트 시작!")
            
            participating_agents = list(self.agents.keys())
            
            if len(participating_agents) < 2:
                print("⚠️ 집단 진화를 위한 에이전트 수 부족")
                return
            
            # 집단 지능 계산
            collective_intelligence = sum(
                agent["intelligence"] for agent in self.agents.values()
            ) / len(self.agents)
            
            # 집단 개선
            collective_improvement = random.uniform(0.1, 0.3)
            
            # 모든 참여 에이전트 향상
            for agent_id in participating_agents:
                self.agents[agent_id]["intelligence"] *= (1 + collective_improvement)
            
            # 새로운 창발 능력
            emergent_capabilities = [
                "네트워크_학습", "집단_추론", "분산_최적화", 
                "협업_창의성", "군집_지능"
            ]
            
            new_capability = random.choice(emergent_capabilities)
            
            # 데이터베이스에 기록
            self.record_collective_evolution(
                participating_agents, 
                collective_improvement, 
                new_capability
            )
            
            print(f"✨ 집단 진화 완료!")
            print(f"   참여 에이전트: {len(participating_agents)}개")
            print(f"   집단 개선: +{collective_improvement:.1%}")
            print(f"   새로운 능력: {new_capability}")
            
        except Exception as e:
            print(f"❌ 집단 진화 실패: {e}")
    
    def record_collective_evolution(self, agents, improvement, new_capability):
        """집단 진화 기록"""
        try:
            conn = sqlite3.connect(self.network_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO collective_evolution 
                (timestamp, participating_agents, evolution_type, collective_improvement, 
                 new_emergent_capabilities, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                json.dumps(agents),
                "network_evolution",
                improvement,
                new_capability,
                f"{len(agents)}개 에이전트 집단 진화"
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 집단 진화 기록 실패: {e}")
    
    def simulate_agent_interactions(self):
        """에이전트 상호작용 시뮬레이션"""
        print("🔄 에이전트 네트워크 상호작용 시뮬레이션 시작")
        
        interaction_count = 0
        
        while interaction_count < 20:  # 20회 상호작용
            if len(self.agents) >= 2:
                # 랜덤 에이전트 쌍 선택
                agent_ids = list(self.agents.keys())
                sender = random.choice(agent_ids)
                receiver = random.choice([aid for aid in agent_ids if aid != sender])
                
                # 랜덤 메시지 타입
                message_types = [
                    "knowledge_share", "capability_request", 
                    "evolution_sync", "collaboration_invite"
                ]
                message_type = random.choice(message_types)
                
                # 메시지 내용 생성
                content = self.generate_interaction_content(message_type)
                
                # 메시지 전송
                response = self.send_message(sender, receiver, message_type, content)
                
                interaction_count += 1
                time.sleep(0.5)  # 상호작용 간격
                
                # 가끔 집단 진화
                if interaction_count % 8 == 0:
                    self.trigger_collective_evolution()
            
            else:
                print("⚠️ 상호작용을 위한 에이전트 수 부족")
                break
        
        print("🎉 네트워크 상호작용 시뮬레이션 완료!")
        self.print_network_summary()
    
    def generate_interaction_content(self, message_type):
        """상호작용 내용 생성"""
        content_templates = {
            "knowledge_share": {
                "knowledge": {"learning_pattern": f"pattern_{random.randint(1,100)}"}
            },
            "capability_request": {
                "capability": random.choice(["learning", "evolution", "analysis"])
            },
            "evolution_sync": {
                "evolution_data": {"generation": random.randint(1,10)}
            },
            "collaboration_invite": {
                "project_type": random.choice(["research", "optimization", "innovation"])
            }
        }
        
        return content_templates.get(message_type, {})
    
    def print_network_summary(self):
        """네트워크 요약 출력"""
        print("\n" + "="*60)
        print("🌐 에이전트 네트워크 요약")
        print("="*60)
        print(f"🤖 활성 에이전트: {len(self.agents)}개")
        print(f"🤝 협업 점수: {self.collaboration_score:.2f}")
        
        if self.agents:
            avg_intelligence = sum(agent["intelligence"] for agent in self.agents.values()) / len(self.agents)
            print(f"🧠 평균 지능: {avg_intelligence:.2f}")
            
            print("\n📊 에이전트별 상태:")
            for agent_id, agent_info in self.agents.items():
                intelligence = agent_info["intelligence"]
                capabilities = len(agent_info["capabilities"])
                print(f"   {agent_id}: 지능 {intelligence:.2f}, 능력 {capabilities}개")
    
    def start_network_system(self):
        """네트워크 시스템 시작"""
        print("🌐 에이전트 네트워크 시스템 시작")
        
        # 기본 에이전트들 등록
        self.register_agent("evolution_01", "self_evolving", ["learning", "evolution"])
        self.register_agent("multimodal_01", "multimodal", ["text", "image", "synthesis"])
        self.register_agent("analyzer_01", "analyzer", ["analysis", "optimization"])
        
        # 상호작용 시뮬레이션
        self.simulate_agent_interactions()

def main():
    network = EvolutionAgentNetwork()
    network.start_network_system()

if __name__ == "__main__":
    main()
