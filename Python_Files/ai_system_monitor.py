#!/usr/bin/env python3
"""
🔍 AI 시스템 실행 상태 모니터링 도구
실시간으로 자기진화 AI 시스템의 상태를 체크하고 필요시 재시작
"""

import psutil
import sqlite3
import time
import subprocess
import os
from datetime import datetime, timedelta
import json

class AISystemMonitor:
    """AI 시스템 실행 상태 모니터"""
    
    def __init__(self):
        self.process_name = "self_evolving_ai.py"
        self.db_file = "self_evolution.db"
        self.monitor_interval = 30  # 30초마다 체크
        
    def check_system_status(self):
        """시스템 전반적 상태 체크"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'process_running': self.is_process_running(),
            'database_active': self.check_database_activity(),
            'recent_evolution': self.check_recent_evolution(),
            'file_generation': self.check_file_generation(),
            'system_resources': self.get_system_resources()
        }
        
        return status
    
    def is_process_running(self):
        """AI 프로세스가 실행 중인지 확인"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if self.process_name in cmdline:
                            return {
                                'running': True,
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.cpu_percent(),
                                'memory_mb': proc.memory_info().rss / 1024 / 1024
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {'running': False}
            
        except Exception as e:
            return {'running': False, 'error': str(e)}
    
    def check_database_activity(self):
        """데이터베이스 활동 확인"""
        try:
            if not os.path.exists(self.db_file):
                return {'active': False, 'reason': 'database_not_found'}
            
            # 파일 수정 시간 확인
            mod_time = os.path.getmtime(self.db_file)
            mod_datetime = datetime.fromtimestamp(mod_time)
            time_diff = datetime.now() - mod_datetime
            
            # 최근 5분 이내 수정이면 활성
            is_active = time_diff < timedelta(minutes=5)
            
            return {
                'active': is_active,
                'last_modified': mod_datetime.isoformat(),
                'minutes_ago': int(time_diff.total_seconds() / 60)
            }
            
        except Exception as e:
            return {'active': False, 'error': str(e)}
    
    def check_recent_evolution(self):
        """최근 진화 활동 확인"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 총 진화 수 확인
            cursor.execute('SELECT COUNT(*) FROM evolution_log')
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                conn.close()
                return {'has_evolution': False, 'total_generations': 0}
            
            # 최근 진화 확인
            cursor.execute('''SELECT generation, intelligence_level, performance_gain, timestamp 
                            FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT 1''')
            latest = cursor.fetchone()
            
            # 최근 5세대 성능 트렌드
            cursor.execute('''SELECT performance_gain FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT 5''')
            recent_gains = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'has_evolution': True,
                'total_generations': total_count,
                'latest_generation': latest[0],
                'current_intelligence': latest[1],
                'latest_performance': latest[2],
                'latest_timestamp': latest[3],
                'recent_performance_trend': sum(recent_gains) / len(recent_gains) if recent_gains else 0
            }
            
        except Exception as e:
            return {'has_evolution': False, 'error': str(e)}
    
    def check_file_generation(self):
        """AI 생성 파일 확인"""
        try:
            # evolved_ai_gen_ 패턴 파일들 찾기
            evolved_files = [f for f in os.listdir('.') 
                           if f.startswith('evolved_ai_gen_') and f.endswith('.py')]
            
            if not evolved_files:
                return {'files_generated': False, 'count': 0}
            
            # 최신 파일 찾기
            evolved_files.sort()
            latest_file = evolved_files[-1]
            
            # 파일 크기와 수정 시간
            file_size = os.path.getsize(latest_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            
            return {
                'files_generated': True,
                'count': len(evolved_files),
                'latest_file': latest_file,
                'latest_file_size': file_size,
                'latest_file_time': mod_time.isoformat(),
                'minutes_since_last': int((datetime.now() - mod_time).total_seconds() / 60)
            }
            
        except Exception as e:
            return {'files_generated': False, 'error': str(e)}
    
    def get_system_resources(self):
        """시스템 리소스 상태"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'disk_percent': (disk.used / disk.total) * 100
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_health_report(self):
        """시스템 건강 상태 보고서 생성"""
        status = self.check_system_status()
        
        print("🔍 AI 시스템 상태 모니터링 리포트")
        print("=" * 60)
        print(f"📅 검사 시간: {status['timestamp']}")
        print()
        
        # 프로세스 상태
        process = status['process_running']
        if process['running']:
            print(f"✅ AI 프로세스: 실행 중 (PID: {process['pid']})")
            print(f"   CPU: {process['cpu_percent']:.1f}%, 메모리: {process['memory_mb']:.1f}MB")
        else:
            print("❌ AI 프로세스: 중지됨")
        print()
        
        # 데이터베이스 상태
        db = status['database_active']
        if db['active']:
            print(f"✅ 데이터베이스: 활성 ({db['minutes_ago']}분 전 업데이트)")
        else:
            print(f"⚠️ 데이터베이스: 비활성 ({db.get('reason', 'unknown')})")
        print()
        
        # 진화 상태
        evolution = status['recent_evolution']
        if evolution['has_evolution']:
            print(f"✅ 진화 시스템: 활성")
            print(f"   총 세대: {evolution['total_generations']}")
            print(f"   현재 세대: {evolution['latest_generation']}")
            print(f"   지능 레벨: {evolution['current_intelligence']:.1f}")
            print(f"   최근 성능: {evolution['latest_performance']:.1f}")
            print(f"   성능 트렌드: {evolution['recent_performance_trend']:.1f}")
        else:
            print("⚠️ 진화 시스템: 진화 기록 없음")
        print()
        
        # 파일 생성 상태
        files = status['file_generation']
        if files['files_generated']:
            print(f"✅ 코드 생성: 활성 ({files['count']}개 파일)")
            print(f"   최신 파일: {files['latest_file']}")
            print(f"   파일 크기: {files['latest_file_size']} bytes")
            print(f"   생성 시간: {files['minutes_since_last']}분 전")
        else:
            print("⚠️ 코드 생성: 파일 없음")
        print()
        
        # 시스템 리소스
        resources = status['system_resources']
        if 'error' not in resources:
            print(f"📊 시스템 리소스:")
            print(f"   CPU: {resources['cpu_percent']:.1f}%")
            print(f"   메모리: {resources['memory_percent']:.1f}% (사용 가능: {resources['memory_available_gb']:.1f}GB)")
            print(f"   디스크: {resources['disk_percent']:.1f}% (사용 가능: {resources['disk_free_gb']:.1f}GB)")
        
        print("=" * 60)
        
        # 전반적 건강도 평가
        health_score = self.calculate_health_score(status)
        health_grade = self.get_health_grade(health_score)
        
        print(f"🏥 전반적 건강도: {health_score}/100 ({health_grade})")
        
        # 권장사항
        recommendations = self.get_recommendations(status)
        if recommendations:
            print("\n💡 권장사항:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return status, health_score
    
    def calculate_health_score(self, status):
        """건강도 점수 계산"""
        score = 0
        
        # 프로세스 실행 (30점)
        if status['process_running']['running']:
            score += 30
        
        # 데이터베이스 활성 (25점)
        if status['database_active']['active']:
            score += 25
        
        # 진화 활동 (25점)
        if status['recent_evolution']['has_evolution']:
            score += 25
        
        # 파일 생성 (20점)
        if status['file_generation']['files_generated']:
            files = status['file_generation']
            if files['minutes_since_last'] < 60:  # 1시간 이내
                score += 20
            elif files['minutes_since_last'] < 180:  # 3시간 이내
                score += 10
        
        return min(score, 100)
    
    def get_health_grade(self, score):
        """건강도 등급"""
        if score >= 90:
            return "🟢 최상"
        elif score >= 70:
            return "🟡 양호"
        elif score >= 50:
            return "🟠 보통"
        else:
            return "🔴 주의"
    
    def get_recommendations(self, status):
        """상태 기반 권장사항"""
        recommendations = []
        
        if not status['process_running']['running']:
            recommendations.append("AI 시스템을 시작하세요: python self_evolving_ai.py")
        
        if not status['database_active']['active']:
            recommendations.append("데이터베이스 연결을 확인하세요")
        
        if not status['recent_evolution']['has_evolution']:
            recommendations.append("진화 시스템이 초기화되지 않았습니다. 시스템 재시작을 고려하세요")
        
        if not status['file_generation']['files_generated']:
            recommendations.append("코드 생성이 비활성화되어 있습니다. LLM 연결을 확인하세요")
        
        resources = status['system_resources']
        if 'error' not in resources:
            if resources['cpu_percent'] > 80:
                recommendations.append("CPU 사용률이 높습니다. 다른 프로세스를 종료하는 것을 고려하세요")
            
            if resources['memory_percent'] > 85:
                recommendations.append("메모리 사용률이 높습니다. 시스템 재시작을 고려하세요")
            
            if resources['disk_free_gb'] < 1:
                recommendations.append("디스크 공간이 부족합니다. 파일을 정리하세요")
        
        return recommendations
    
    def auto_restart_system(self):
        """자동 시스템 재시작"""
        try:
            print("🔄 AI 시스템 자동 재시작 시도...")
            
            # 기존 프로세스 종료
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if self.process_name in cmdline:
                            print(f"🛑 기존 프로세스 종료 (PID: {proc.info['pid']})")
                            proc.terminate()
                            proc.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 새 프로세스 시작
            print("🚀 새 AI 시스템 시작...")
            subprocess.Popen(['python', 'self_evolving_ai.py'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            print("✅ AI 시스템 재시작 완료")
            return True
            
        except Exception as e:
            print(f"❌ 재시작 실패: {e}")
            return False

if __name__ == "__main__":
    monitor = AISystemMonitor()
    
    # 상태 체크
    status, health_score = monitor.generate_health_report()
    
    # 건강도가 낮으면 재시작 제안
    if health_score < 50:
        response = input("\n❓ 시스템 건강도가 낮습니다. 자동 재시작을 시도하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            monitor.auto_restart_system()
    
    # 상태를 JSON 파일로도 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status_file = f"ai_system_status_{timestamp}.json"
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 상태 정보 저장: {status_file}")
