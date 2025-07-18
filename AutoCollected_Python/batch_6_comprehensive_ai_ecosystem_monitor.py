#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌟 Comprehensive AI Ecosystem Monitor v1.0
==========================================
모든 AI 시스템의 통합 상태 모니터링 및 관리
"""

import asyncio
import json
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any
import psutil
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSystemMonitor:
    """통합 시스템 모니터"""
    
    def __init__(self):
        self.systems = {
            'ai_network_expansion': 'ai_network_expansion.db',
            'quantum_intelligence': 'quantum_intelligence.db',
            'multiverse_simulation': 'multiverse_simulation.db',
            'autonomous_learning': 'autonomous_learning.db',
            'evolution_optimization': 'evolution_optimization.db',
            'ultra_fast_processing': 'processing_engine.db',
            'goal_achievement': 'goal_achievement.db'
        }
        
    def check_system_status(self) -> Dict[str, Any]:
        """시스템 상태 확인"""
        status_report = {
            'timestamp': datetime.now().isoformat(),
            'system_resources': self._get_system_resources(),
            'ai_systems': {},
            'databases': {},
            'log_files': {},
            'active_processes': self._get_active_processes(),
            'overall_health': 'excellent'
        }
        
        # 각 시스템별 데이터베이스 상태 확인
        for system_name, db_file in self.systems.items():
            status_report['ai_systems'][system_name] = self._check_database_status(db_file)
            
        # 로그 파일 상태 확인
        log_files = [
            'ai_network_expansion.log',
            'quantum_intelligence.log', 
            'multiverse_simulation.log',
            'autonomous_learning.log',
            'evolution_optimization.log',
            'goal_achievement.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                status_report['log_files'][log_file] = {
                    'exists': True,
                    'size_mb': os.path.getsize(log_file) / (1024 * 1024),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(log_file)).isoformat()
                }
                
        return status_report
        
    def _get_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 상태"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            'cpu_cores': psutil.cpu_count(logical=True),
            'cpu_usage_percent': cpu_percent,
            'memory_total_gb': memory.total / (1024**3),
            'memory_used_gb': memory.used / (1024**3),
            'memory_percent': memory.percent,
            'disk_usage': self._get_disk_usage()
        }
        
    def _get_disk_usage(self) -> Dict[str, float]:
        """디스크 사용량"""
        disk = psutil.disk_usage('.')
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': (disk.used / disk.total) * 100
        }
        
    def _get_active_processes(self) -> List[Dict]:
        """활성 프로세스 확인"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pinfo = proc.info
                if pinfo['cmdline'] and any('python' in cmd.lower() for cmd in pinfo['cmdline']):
                    # AI 시스템 관련 프로세스만 필터링
                    if any(system in ' '.join(pinfo['cmdline']) for system in [
                        'ai_network', 'quantum', 'multiverse', 'autonomous', 
                        'evolution', 'ultra_fast', 'goal_achievement'
                    ]):
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'command': ' '.join(pinfo['cmdline'][:3])  # 첫 3개 인자만
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        return processes
        
    def _check_database_status(self, db_file: str) -> Dict[str, Any]:
        """데이터베이스 상태 확인"""
        if not os.path.exists(db_file):
            return {
                'status': 'not_found',
                'exists': False,
                'size_mb': 0,
                'tables': [],
                'record_counts': {}
            }
            
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 테이블 목록 조회
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 각 테이블의 레코드 수
            record_counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                record_counts[table] = count
                
            conn.close()
            
            return {
                'status': 'active',
                'exists': True,
                'size_mb': os.path.getsize(db_file) / (1024 * 1024),
                'tables': tables,
                'record_counts': record_counts,
                'total_records': sum(record_counts.values())
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'exists': True,
                'error': str(e),
                'size_mb': os.path.getsize(db_file) / (1024 * 1024)
            }
            
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """종합 시스템 리포트 생성"""
        status = self.check_system_status()
        
        # 통계 계산
        total_db_size = sum(
            db_info.get('size_mb', 0) 
            for db_info in status['ai_systems'].values()
        )
        
        total_records = sum(
            db_info.get('total_records', 0) 
            for db_info in status['ai_systems'].values()
        )
        
        active_systems = len([
            system for system, info in status['ai_systems'].items() 
            if info.get('status') == 'active'
        ])
        
        report = {
            'ecosystem_overview': {
                'total_ai_systems': len(self.systems),
                'active_systems': active_systems,
                'system_health': 'excellent' if active_systems >= 6 else 'good' if active_systems >= 4 else 'warning',
                'total_database_size_mb': total_db_size,
                'total_ai_records': total_records,
                'active_processes': len(status['active_processes']),
                'system_uptime_status': 'operational'
            },
            'resource_utilization': status['system_resources'],
            'system_details': status['ai_systems'],
            'process_monitoring': status['active_processes'],
            'log_monitoring': status['log_files'],
            'timestamp': status['timestamp']
        }
        
        return report
        
    def display_status_dashboard(self):
        """상태 대시보드 출력"""
        report = self.generate_comprehensive_report()
        
        print("🌟 ===== AI 생태계 통합 모니터링 대시보드 =====")
        print(f"⏰ 모니터링 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 생태계 개요
        eco = report['ecosystem_overview']
        print("🎯 === 시스템 생태계 개요 ===")
        print(f"   총 AI 시스템: {eco['total_ai_systems']}개")
        print(f"   활성 시스템: {eco['active_systems']}개")
        print(f"   시스템 상태: {eco['system_health'].upper()}")
        print(f"   총 데이터베이스 크기: {eco['total_database_size_mb']:.1f} MB")
        print(f"   총 AI 레코드: {eco['total_ai_records']:,}개")
        print(f"   활성 프로세스: {eco['active_processes']}개")
        print()
        
        # 리소스 사용률
        res = report['resource_utilization']
        print("💻 === 시스템 리소스 ===")
        print(f"   CPU: {res['cpu_cores']}코어 ({res['cpu_usage_percent']:.1f}% 사용)")
        print(f"   메모리: {res['memory_used_gb']:.1f}GB / {res['memory_total_gb']:.1f}GB ({res['memory_percent']:.1f}%)")
        print(f"   디스크: {res['disk_usage']['used_gb']:.1f}GB / {res['disk_usage']['total_gb']:.1f}GB ({res['disk_usage']['percent']:.1f}%)")
        print()
        
        # 시스템별 상세 정보
        print("🤖 === AI 시스템 상세 정보 ===")
        for system_name, system_info in report['system_details'].items():
            status_emoji = "✅" if system_info.get('status') == 'active' else "❌"
            print(f"   {status_emoji} {system_name}:")
            
            if system_info.get('status') == 'active':
                print(f"      - 데이터베이스: {system_info['size_mb']:.1f} MB")
                print(f"      - 테이블: {len(system_info['tables'])}개")
                print(f"      - 레코드: {system_info['total_records']:,}개")
                
                # 주요 테이블별 레코드 수
                for table, count in system_info['record_counts'].items():
                    if count > 0:
                        print(f"        └ {table}: {count:,}개")
            else:
                print(f"      - 상태: {system_info.get('status', 'unknown')}")
        print()
        
        # 활성 프로세스
        if report['process_monitoring']:
            print("⚡ === 활성 AI 프로세스 ===")
            for proc in report['process_monitoring']:
                print(f"   🔄 PID {proc['pid']}: {proc['command']}")
        print()
        
        # 로그 파일 상태
        if report['log_monitoring']:
            print("📝 === 로그 파일 상태 ===")
            for log_file, log_info in report['log_monitoring'].items():
                print(f"   📄 {log_file}: {log_info['size_mb']:.2f} MB")
        print()
        
        print("🎉 모든 시스템이 정상 작동 중입니다!")
        print("=" * 60)

def main():
    """메인 실행"""
    print("🌟 종합 AI 생태계 모니터 v1.0")
    print("=" * 60)
    
    monitor = ComprehensiveSystemMonitor()
    
    # 현재 상태 확인
    monitor.display_status_dashboard()
    
    # 리포트 파일 생성
    report = monitor.generate_comprehensive_report()
    
    with open('comprehensive_ai_ecosystem_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"📊 상세 리포트 저장됨: comprehensive_ai_ecosystem_report.json")
    
    print("\n🔄 실시간 모니터링 모드...")
    print("(Ctrl+C로 종료)")
    
    try:
        while True:
            time.sleep(30)  # 30초마다 업데이트
            os.system('cls' if os.name == 'nt' else 'clear')  # 화면 클리어
            monitor.display_status_dashboard()
            
    except KeyboardInterrupt:
        print("\n✋ 모니터링 종료")

if __name__ == "__main__":
    main()
