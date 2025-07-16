#!/usr/bin/env python3
"""
안정성 모니터링 시스템 (수정 버전)
"""
import time
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StabilityMonitor:
    """안정성 모니터"""
    
    def __init__(self):
        self.check_interval = 30  # 30초 간격
        self.start_time = time.time()
        self.error_count = 0
        self.max_errors = 5
        
    def check_system_health(self) -> Dict[str, Any]:
        """시스템 상태 확인"""
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'working_directory': os.getcwd(),
                'python_version': self.get_python_version(),
                'disk_info': self.get_disk_info(),
                'memory_info': self.get_memory_info(),
                'file_system_info': self.get_file_system_info(),
                'error_count': self.error_count,
                'overall_status': self.determine_overall_status()
            }
            
            logger.info(f"시스템 상태 확인 완료: {health_data['overall_status']}")
            return health_data
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"시스템 상태 확인 실패: {e}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_count': self.error_count,
                'overall_status': 'error'
            }
    
    def get_python_version(self) -> str:
        """Python 버전 정보"""
        import sys
        return sys.version
    
    def get_disk_info(self) -> Dict[str, Any]:
        """디스크 정보 확인"""
        try:
            import psutil
            disk = psutil.disk_usage('.')
            return {
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3),
                'used_gb': disk.used / (1024**3),
                'usage_percent': disk.percent
            }
        except ImportError:
            return {
                'status': 'psutil_not_available',
                'message': 'psutil 패키지 설치 필요: pip install psutil'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unavailable'
            }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """메모리 정보 확인"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'usage_percent': memory.percent
            }
        except ImportError:
            return {
                'status': 'psutil_not_available',
                'message': 'psutil 패키지 설치 필요: pip install psutil'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unavailable'
            }
    
    def get_file_system_info(self) -> Dict[str, Any]:
        """파일 시스템 정보"""
        try:
            current_dir = os.getcwd()
            
            # Python 파일 개수
            python_files = [f for f in os.listdir('.') if f.endswith('.py')]
            
            # 중요 파일 존재 여부
            important_files = [
                'config.json',
                'run_system.py',
                'simple_dashboard.py'
            ]
            
            file_status = {}
            for file in important_files:
                file_status[file] = os.path.exists(file)
            
            return {
                'current_directory': current_dir,
                'python_files_count': len(python_files),
                'important_files_status': file_status,
                'directory_writable': os.access(current_dir, os.W_OK),
                'directory_readable': os.access(current_dir, os.R_OK)
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unavailable'
            }
    
    def determine_overall_status(self) -> str:
        """전체 상태 판정"""
        if self.error_count >= self.max_errors:
            return 'critical'
        elif self.error_count > 0:
            return 'warning'
        else:
            return 'healthy'
    
    def save_health_report(self, health_data: Dict[str, Any]):
        """건강 상태 리포트 저장"""
        try:
            with open('health_report.json', 'w') as f:
                json.dump(health_data, f, indent=2)
            logger.info("건강 리포트 저장 완료: health_report.json")
        except Exception as e:
            logger.error(f"리포트 저장 실패: {e}")
    
    def print_status_summary(self, health_data: Dict[str, Any]):
        """상태 요약 출력"""
        status = health_data.get('overall_status', 'unknown')
        uptime = health_data.get('uptime_seconds', 0)
        
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '❌',
            'error': '❌'
        }.get(status, '❓')
        
        print(f"{status_emoji} 상태: {status.upper()}")
        print(f"⏱️ 가동시간: {uptime:.1f}초")
        print(f"🔢 오류 횟수: {health_data.get('error_count', 0)}")
        
        # 메모리 정보 출력
        memory_info = health_data.get('memory_info', {})
        if 'usage_percent' in memory_info:
            print(f"🧠 메모리 사용률: {memory_info['usage_percent']:.1f}%")
        
        # 파일 시스템 정보 출력
        fs_info = health_data.get('file_system_info', {})
        if 'python_files_count' in fs_info:
            print(f"📁 Python 파일: {fs_info['python_files_count']}개")
    
    def run_monitoring(self):
        """모니터링 실행"""
        print("🛡️ 안정성 모니터링 시작")
        print("=" * 50)
        
        logger.info("안정성 모니터링 시작")
        
        iteration = 0
        try:
            while True:
                iteration += 1
                
                print(f"\n🔍 체크 #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 30)
                
                # 건강 상태 확인
                health_data = self.check_system_health()
                
                # 상태 요약 출력
                self.print_status_summary(health_data)
                
                # 리포트 저장
                self.save_health_report(health_data)
                
                # 중요한 오류 발생 시 경고
                if health_data.get('overall_status') == 'critical':
                    print("🚨 중요: 시스템이 임계 상태입니다!")
                    logger.critical("시스템이 임계 상태입니다!")
                
                # 대기
                print(f"⏳ {self.check_interval}초 대기 중... (Ctrl+C로 종료)")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 모니터링 종료 (사용자 중단)")
            logger.info("사용자에 의해 모니터링 종료")
        except Exception as e:
            print(f"❌ 모니터링 오류: {e}")
            logger.error(f"모니터링 오류: {e}")
        finally:
            print("✅ 모니터링 정리 완료")
            logger.info("모니터링 정리 완료")

def main():
    """메인 실행 함수"""
    print("🛡️ 안정성 모니터링 시스템")
    print("=" * 50)
    
    monitor = StabilityMonitor()
    
    # 초기 상태 확인
    print("📊 초기 상태 확인 중...")
    initial_health = monitor.check_system_health()
    
    print(f"📊 초기 상태: {initial_health['overall_status'].upper()}")
    
    # 상세 정보 출력
    if initial_health.get('memory_info', {}).get('usage_percent'):
        print(f"🧠 메모리 사용률: {initial_health['memory_info']['usage_percent']:.1f}%")
    
    if initial_health.get('file_system_info', {}).get('python_files_count'):
        print(f"📁 Python 파일: {initial_health['file_system_info']['python_files_count']}개")
    
    # 모니터링 시작
    print(f"\n🔄 모니터링 간격: {monitor.check_interval}초")
    print("📄 상세 리포트: health_report.json")
    
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
