#!/usr/bin/env python3
"""
🔧 AI 생태계 최적화 및 복구 시스템
메모리 최적화 및 핵심 시스템만 유지
"""

import subprocess
import time
import requests
import psutil
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEcosystemOptimizer:
    """AI 생태계 최적화 관리자"""
    
    def __init__(self):
        self.core_systems = [
            {
                "name": "Vibe AI Coding System",
                "file": "enhanced_vibe_ai_chat.py",
                "port": 8001,
                "priority": 1
            },
            {
                "name": "Shrimp MCP Evolution",
                "file": "shrimp_evolution_server.py", 
                "port": 8002,
                "priority": 2
            },
            {
                "name": "AutoGen Studio Integration",
                "file": "autogen_studio_integration_v5.py",
                "port": 8004,
                "priority": 3
            }
        ]
    
    def get_memory_usage(self):
        """현재 메모리 사용률 확인"""
        memory = psutil.virtual_memory()
        return memory.percent
    
    def cleanup_python_processes(self):
        """불필요한 Python 프로세스 정리"""
        logger.info("🧹 Python 프로세스 정리 시작")
        try:
            # 모든 python.exe 프로세스 종료
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                         capture_output=True, text=True)
            time.sleep(3)
            logger.info("✅ Python 프로세스 정리 완료")
        except Exception as e:
            logger.warning(f"프로세스 정리 중 오류: {e}")
    
    def start_core_system(self, system):
        """핵심 시스템 시작"""
        logger.info(f"🚀 {system['name']} 시작 중...")
        try:
            process = subprocess.Popen(
                ['python', system['file']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5)  # 시스템 초기화 대기
            
            # 헬스 체크
            try:
                response = requests.get(f"http://localhost:{system['port']}/health", timeout=3)
                if response.status_code == 200:
                    logger.info(f"✅ {system['name']} 정상 시작 (포트 {system['port']})")
                    return True
            except:
                # /health가 없으면 기본 포트로 확인
                try:
                    response = requests.get(f"http://localhost:{system['port']}", timeout=3)
                    logger.info(f"✅ {system['name']} 시작됨 (포트 {system['port']})")
                    return True
                except:
                    pass
                    
            logger.warning(f"⚠️ {system['name']} 헬스 체크 실패")
            return False
            
        except Exception as e:
            logger.error(f"❌ {system['name']} 시작 실패: {e}")
            return False
    
    def optimize_ecosystem(self):
        """AI 생태계 최적화 실행"""
        logger.info("🔧 AI 생태계 최적화 시작")
        
        # 1. 메모리 사용률 확인
        memory_usage = self.get_memory_usage()
        logger.info(f"📊 현재 메모리 사용률: {memory_usage:.1f}%")
        
        # 2. 높은 메모리 사용률일 경우 정리
        if memory_usage > 85:
            logger.warning("⚠️ 높은 메모리 사용률 감지 - 프로세스 정리")
            self.cleanup_python_processes()
            time.sleep(5)
        
        # 3. 핵심 시스템만 순차 시작
        started_systems = 0
        for system in self.core_systems:
            if self.start_core_system(system):
                started_systems += 1
                time.sleep(3)  # 시스템 간 간격
            
            # 메모리 재확인
            current_memory = self.get_memory_usage()
            if current_memory > 90:
                logger.warning(f"⚠️ 메모리 한계 도달 ({current_memory:.1f}%) - 추가 시스템 시작 중단")
                break
        
        logger.info(f"🎉 AI 생태계 최적화 완료: {started_systems}/{len(self.core_systems)} 시스템 활성화")
        
        # 4. 최종 상태 리포트
        final_memory = self.get_memory_usage()
        logger.info(f"📊 최종 메모리 사용률: {final_memory:.1f}%")
        
        return started_systems

def main():
    print("🔧 AI 생태계 최적화 시스템 시작")
    optimizer = AIEcosystemOptimizer()
    
    # 최적화 실행
    active_systems = optimizer.optimize_ecosystem()
    
    print(f"\n🎯 최적화 결과:")
    print(f"   ✅ 활성화된 시스템: {active_systems}")
    print(f"   📊 메모리 사용률: {optimizer.get_memory_usage():.1f}%")
    print(f"\n🌐 접속 URL:")
    print(f"   🎨 Vibe AI: http://localhost:8001")
    print(f"   🦐 자율 진화: http://localhost:8002")
    print(f"   🎯 AutoGen Studio: http://localhost:8004")

if __name__ == "__main__":
    main()
