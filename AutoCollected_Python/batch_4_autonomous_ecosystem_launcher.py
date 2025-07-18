#!/usr/bin/env python3
"""
🚀 통합 자율 AI 생태계 런처 v3.0
모든 AI 에이전트를 자동으로 실행하고 관리하는 마스터 시스템
"""

import subprocess
import time
import requests
import json
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecosystem_launcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutonomousEcosystemLauncher:
    """🚀 자율 AI 생태계 런처"""
    
    def __init__(self):
        # AI 에이전트 시스템 목록
        self.ai_systems = [
            {
                "name": "Vibe AI Coding System",
                "file": "enhanced_vibe_ai_chat.py",
                "port": 8001,
                "priority": 1,
                "description": "메인 코딩 AI 시스템"
            },
            {
                "name": "Shrimp MCP Evolution",
                "file": "shrimp_evolution_server.py", 
                "port": 8002,
                "priority": 2,
                "description": "자율 진화 시스템"
            },
            {
                "name": "가속화된 무료 LLM",
                "file": "accelerated_free_llm_evolution.py",
                "port": 8003,
                "priority": 3,
                "description": "빠른 진화 시스템"
            },
            {
                "name": "초진화 AI 시스템",
                "file": "ultra_evolution_ai_system.py",
                "port": 8004,
                "priority": 4,
                "description": "차세대 멀티 AI 엔진"
            },
            {
                "name": "자율 진화 에이전트",
                "file": "autonomous_evolution_agent.py",
                "port": 8008,
                "priority": 5,
                "description": "자체 코딩 및 자율 발전"
            }
        ]
        
        self.launched_processes = {}
        self.ecosystem_status = {
            "total_systems": len(self.ai_systems),
            "running_systems": 0,
            "failed_systems": 0,
            "launch_time": datetime.now().isoformat(),
            "ecosystem_health": "initializing"
        }
    
    def launch_all_systems(self):
        """모든 AI 시스템 실행"""
        logger.info("🚀 자율 AI 생태계 런처 v3.0 시작")
        logger.info(f"📊 총 {len(self.ai_systems)}개 AI 시스템 실행 예정")
        
        # 우선순위 순으로 시스템 실행
        for system in sorted(self.ai_systems, key=lambda x: x["priority"]):
            self.launch_system(system)
            time.sleep(3)  # 시스템 간 시작 간격
        
        # 전체 시스템 상태 확인
        time.sleep(10)
        self.check_ecosystem_health()
        
        # 실시간 모니터링 시작
        self.start_monitoring()
    
    def launch_system(self, system):
        """개별 AI 시스템 실행"""
        try:
            logger.info(f"🔄 {system['name']} 실행 중...")
            
            # Python 프로세스로 시스템 실행
            process = subprocess.Popen(
                ["python", system["file"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
            
            self.launched_processes[system["name"]] = {
                "process": process,
                "system_info": system,
                "launch_time": datetime.now().isoformat()
            }
            
            logger.info(f"✅ {system['name']} 실행됨 (PID: {process.pid})")
            
            # 잠시 대기 후 상태 확인
            time.sleep(5)
            if self.check_system_health(system):
                logger.info(f"🌟 {system['name']} 정상 작동 확인")
                self.ecosystem_status["running_systems"] += 1
            else:
                logger.warning(f"⚠️ {system['name']} 상태 확인 필요")
                self.ecosystem_status["failed_systems"] += 1
                
        except Exception as e:
            logger.error(f"❌ {system['name']} 실행 실패: {e}")
            self.ecosystem_status["failed_systems"] += 1
    
    def check_system_health(self, system):
        """개별 시스템 건강 상태 확인"""
        try:
            response = requests.get(f"http://localhost:{system['port']}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def check_ecosystem_health(self):
        """전체 생태계 건강 상태 확인"""
        logger.info("🔍 AI 생태계 건강 상태 종합 확인")
        
        running_count = 0
        total_count = len(self.ai_systems)
        
        for system in self.ai_systems:
            if self.check_system_health(system):
                running_count += 1
                logger.info(f"✅ {system['name']}: 정상 (포트 {system['port']})")
            else:
                logger.warning(f"❌ {system['name']}: 문제 감지 (포트 {system['port']})")
        
        # 생태계 상태 업데이트
        self.ecosystem_status["running_systems"] = running_count
        self.ecosystem_status["failed_systems"] = total_count - running_count
        
        if running_count == total_count:
            self.ecosystem_status["ecosystem_health"] = "excellent"
            logger.info("🎉 모든 AI 시스템이 정상 작동 중입니다!")
        elif running_count >= total_count * 0.8:
            self.ecosystem_status["ecosystem_health"] = "good"
            logger.info(f"✅ 대부분의 AI 시스템이 정상입니다 ({running_count}/{total_count})")
        elif running_count >= total_count * 0.5:
            self.ecosystem_status["ecosystem_health"] = "fair"
            logger.warning(f"⚠️ 일부 AI 시스템에 문제가 있습니다 ({running_count}/{total_count})")
        else:
            self.ecosystem_status["ecosystem_health"] = "poor"
            logger.error(f"🚨 많은 AI 시스템에 문제가 있습니다 ({running_count}/{total_count})")
        
        return running_count, total_count
    
    def start_monitoring(self):
        """실시간 모니터링 시작"""
        logger.info("📊 실시간 AI 생태계 모니터링 시작")
        
        try:
            while True:
                current_time = datetime.now().strftime("%H:%M:%S")
                running, total = self.check_ecosystem_health()
                
                health_emoji = {
                    "excellent": "🟢",
                    "good": "🟡", 
                    "fair": "🟠",
                    "poor": "🔴"
                }.get(self.ecosystem_status["ecosystem_health"], "⚪")
                
                print(f"\r🕒 {current_time} | {health_emoji} 생태계: {running}/{total} | 상태: {self.ecosystem_status['ecosystem_health']}", end='', flush=True)
                
                # 60초마다 상세 상태 출력
                if datetime.now().second == 0:
                    print(f"\n📊 상세 상태 보고:")
                    for system in self.ai_systems:
                        status = "🟢 정상" if self.check_system_health(system) else "🔴 문제"
                        print(f"   {system['name']}: {status}")
                    print()
                
                time.sleep(5)  # 5초마다 모니터링
                
        except KeyboardInterrupt:
            print("\n\n⏹️ 모니터링 종료")
            self.shutdown_ecosystem()
    
    def shutdown_ecosystem(self):
        """AI 생태계 종료"""
        logger.info("🛑 AI 생태계 종료 시작")
        
        for name, process_info in self.launched_processes.items():
            try:
                process = process_info["process"]
                if process.poll() is None:  # 프로세스가 아직 실행 중
                    process.terminate()
                    logger.info(f"🛑 {name} 종료됨")
            except Exception as e:
                logger.error(f"❌ {name} 종료 실패: {e}")
        
        logger.info("🎯 AI 생태계 종료 완료")
    
    def generate_status_report(self):
        """상태 보고서 생성"""
        report = {
            "ecosystem_launcher": "v3.0",
            "timestamp": datetime.now().isoformat(),
            "ecosystem_status": self.ecosystem_status,
            "systems_detail": []
        }
        
        for system in self.ai_systems:
            system_status = {
                "name": system["name"],
                "port": system["port"],
                "description": system["description"],
                "status": "running" if self.check_system_health(system) else "stopped",
                "health_check": f"http://localhost:{system['port']}/health"
            }
            report["systems_detail"].append(system_status)
        
        # 보고서 파일 저장
        with open('ecosystem_status_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

def print_banner():
    """시작 배너 출력"""
    banner = """
🚀🤖🧠🔄⚡🌟🎯🛠️🤝🔍
    
    자율 AI 생태계 런처 v3.0
    Autonomous AI Ecosystem Launcher
    
    ✨ 5개 AI 시스템 자동 실행
    🤖 에이전트 간 자율 협력
    🔄 무료 LLM 기반 자체 코딩
    🛠️ 자동 오류 해결
    📊 실시간 모니터링
    
🚀🤖🧠🔄⚡🌟🎯🛠️🤝🔍
    """
    print(banner)

def main():
    """메인 실행 함수"""
    print_banner()
    
    launcher = AutonomousEcosystemLauncher()
    
    try:
        # 모든 AI 시스템 실행
        launcher.launch_all_systems()
        
        # 상태 보고서 생성
        report = launcher.generate_status_report()
        logger.info("📋 상태 보고서 생성 완료: ecosystem_status_report.json")
        
        # 접속 URL 안내
        print("\n🌐 AI 생태계 접속 URL:")
        print("=" * 50)
        for system in launcher.ai_systems:
            print(f"🔗 {system['name']}: http://localhost:{system['port']}")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의한 종료")
        launcher.shutdown_ecosystem()
    except Exception as e:
        logger.error(f"❌ 런처 실행 오류: {e}")
        launcher.shutdown_ecosystem()

if __name__ == "__main__":
    main()
