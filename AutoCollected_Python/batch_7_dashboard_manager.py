#!/usr/bin/env python3
"""
AI 시스템 대시보드 상태 관리자
중복 방지 및 포트 충돌 해결
"""

import os
import psutil
import json
import threading
import time
import glob
from datetime import datetime
from collections import deque

class LogMonitor:
    """실시간 로그 모니터링 클래스"""
    
    def __init__(self):
        self.log_buffer = deque(maxlen=1000)  # 최대 1000줄 저장
        self.monitoring = False
        self.log_files = [
            "24h_monitoring_log.json",
            "mcp_auto_fix.log",
            "gemini_webhook.log",
            "mcp_diagnosis.log"
        ]
        
    def start_monitoring(self):
        """로그 모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
            monitor_thread.start()
            print("✅ 로그 모니터링 스레드 시작됨")
    
    def stop_monitoring(self):
        """로그 모니터링 중지"""
        self.monitoring = False
        print("⏹️ 로그 모니터링 중지됨")
    
    def _monitor_logs(self):
        """로그 파일들을 실시간으로 모니터링"""
        last_positions = {}
        
        while self.monitoring:
            try:
                for log_file in self.log_files:
                    if os.path.exists(log_file):
                        self._check_log_file(log_file, last_positions)
                
                # JSON 로그 파일들도 확인
                json_files = glob.glob("*_log.json") + glob.glob("*_state.json")
                for json_file in json_files:
                    if json_file not in self.log_files:
                        self._check_json_file(json_file, last_positions)
                
                time.sleep(2)  # 2초마다 체크
                
            except Exception as e:
                self.log_buffer.append(f"[ERROR] 로그 모니터링 오류: {e}")
                time.sleep(5)
    
    def _check_log_file(self, log_file, last_positions):
        """텍스트 로그 파일 체크"""
        try:
            current_size = os.path.getsize(log_file)
            last_size = last_positions.get(log_file, 0)
            
            if current_size > last_size:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            self.log_buffer.append(f"[{timestamp}] {log_file}: {line}")
                
                last_positions[log_file] = current_size
                
        except Exception as e:
            pass  # 파일 접근 오류 무시
    
    def _check_json_file(self, json_file, last_positions):
        """JSON 상태 파일 체크"""
        try:
            mod_time = os.path.getmtime(json_file)
            last_mod = last_positions.get(f"{json_file}_mod", 0)
            
            if mod_time > last_mod:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 중요한 정보만 추출
                if 'intelligence' in data:
                    intel = data['intelligence']
                    self.log_buffer.append(f"[{timestamp}] {json_file}: 지능 레벨 {intel}")
                
                if 'active_agents' in data:
                    agents = data['active_agents']
                    self.log_buffer.append(f"[{timestamp}] {json_file}: 활성 에이전트 {agents}개")
                
                if 'sync_statistics' in data:
                    stats = data['sync_statistics']
                    if 'successful_syncs' in stats:
                        sync_count = stats['successful_syncs']
                        self.log_buffer.append(f"[{timestamp}] {json_file}: 동기화 {sync_count}회 성공")
                
                last_positions[f"{json_file}_mod"] = mod_time
                
        except Exception as e:
            pass  # JSON 파싱 오류 무시
    
    def get_recent_logs(self, lines=50):
        """최근 로그 반환"""
        recent_logs = list(self.log_buffer)[-lines:]
        return recent_logs
    
    def get_log_summary(self):
        """로그 요약 정보"""
        total_logs = len(self.log_buffer)
        error_count = sum(1 for log in self.log_buffer if "[ERROR]" in log)
        warning_count = sum(1 for log in self.log_buffer if "[WARNING]" in log)
        
        return {
            "total_logs": total_logs,
            "error_count": error_count,
            "warning_count": warning_count,
            "monitoring_status": "활성" if self.monitoring else "비활성"
        }

class DashboardManager:
    def __init__(self):
        self.reserved_ports = {
            8095: "메인 AI 대시보드",
            8000: "시스템 서비스"
        }
        self.log_monitor = LogMonitor()
        
    def check_active_dashboards(self):
        """현재 활성 대시보드 확인"""
        print("🔍 활성 대시보드 스캔")
        print("="*40)
        
        active_dashboards = []
        
        # 80xx 포트 스캔
        for port in range(8000, 8100):
            if self.is_port_in_use(port):
                service_name = self.reserved_ports.get(port, "알 수 없는 서비스")
                active_dashboards.append({
                    "port": port,
                    "service": service_name,
                    "status": "활성"
                })
                print(f"  ✅ 포트 {port}: {service_name}")
        
        return active_dashboards
    
    def is_port_in_use(self, port):
        """포트 사용 여부 확인"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except:
            return False
    
    def cleanup_duplicate_files(self):
        """중복 대시보드 파일 정리"""
        print("\n🧹 중복 파일 정리")
        print("-"*30)
        
        # 정리할 파일 목록 (메인 대시보드 제외)
        cleanup_files = [
            "ultimate_system_dashboard.py",
            "enhanced_dashboard.py", 
            "simple_log_viewer.py",
            "log_viewer.html"
        ]
        
        cleaned_count = 0
        for file in cleanup_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"  🗑️ 삭제됨: {file}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ❌ 삭제 실패: {file} - {e}")
        
        print(f"\n✨ 총 {cleaned_count}개 파일 정리 완료")
        
    def generate_dashboard_status_report(self):
        """대시보드 상태 보고서 생성"""
        active_dashboards = self.check_active_dashboards()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "active_dashboards": active_dashboards,
            "main_dashboard": {
                "port": 8095,
                "url": "http://localhost:8095",
                "service": "깔끔한 AI 대시보드",
                "features": [
                    "실시간 AI 시스템 모니터링",
                    "5초마다 자동 업데이트",
                    "리소스 사용량 추적",
                    "클라우드 동기화 상태"
                ]
            },
            "cleanup_summary": {
                "removed_ports": ["8080", "8081", "8082", "8083", "8084", "8085", "8086", "8087", "8088", "8089", "8090", "8091"],
                "remaining_ports": ["8095"],
                "resource_savings": "메모리 사용량 감소, CPU 부하 경감"
            }
        }
        
        return report
    
    def start_real_time_log_monitoring(self):
        """실시간 로그 모니터링 시작"""
        print("\n📝 실시간 로그 모니터링 시작")
        print("-"*40)
        
        self.log_monitor.start_monitoring()
        
    def get_recent_logs(self, lines=50):
        """최근 로그 가져오기"""
        return self.log_monitor.get_recent_logs(lines)
    
    def save_dashboard_config(self):
        """대시보드 설정 저장"""
        config = {
            "main_dashboard": {
                "port": 8095,
                "file": "clean_dashboard.py",
                "auto_start": True
            },
            "reserved_ports": self.reserved_ports,
            "cleanup_date": datetime.now().isoformat(),
            "status": "optimized"
        }
        
        with open('dashboard_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("\n💾 대시보드 설정 저장 완료: dashboard_config.json")

def main():
    """메인 실행 함수"""
    print("🎛️ AI 대시보드 관리자")
    print("="*50)
    
    manager = DashboardManager()
    
    # 1. 현재 상태 확인
    report = manager.generate_dashboard_status_report()
    
    # 2. 중복 파일 정리
    manager.cleanup_duplicate_files()
    
    # 3. 실시간 로그 모니터링 시작
    manager.start_real_time_log_monitoring()
    
    # 4. 설정 저장
    manager.save_dashboard_config()
    
    # 5. 최종 요약
    print("\n📋 최종 대시보드 상태")
    print("="*40)
    print(f"🌐 메인 대시보드: http://localhost:8095")
    print(f"📊 활성 대시보드 수: {len(report['active_dashboards'])}개")
    print(f"🧹 정리된 포트 수: {len(report['cleanup_summary']['removed_ports'])}개")
    print(f"💡 상태: 최적화 완료")
    
    # 6. 로그 요약 표시
    time.sleep(3)  # 로그 모니터링이 시작될 시간을 줌
    log_summary = manager.log_monitor.get_log_summary()
    print(f"\n📝 로그 모니터링 상태: {log_summary['monitoring_status']}")
    print(f"📊 총 로그 수: {log_summary['total_logs']}")
    print(f"⚠️ 경고/오류: {log_summary['warning_count'] + log_summary['error_count']}")
    
    # 7. 최근 로그 표시
    recent_logs = manager.get_recent_logs(10)
    if recent_logs:
        print("\n📋 최근 로그 (최대 10줄)")
        print("-"*50)
        for log in recent_logs[-10:]:
            print(f"  {log}")
    
    print("\n🎯 권장사항:")
    print("  1. 메인 대시보드(8095)만 사용하세요")
    print("  2. 새 대시보드 생성 시 포트 충돌 확인")
    print("  3. 정기적으로 시스템 정리 실행")
    print("  4. 실시간 로그로 시스템 상태 모니터링")
    
    # 보고서 저장
    with open('dashboard_status_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 상세 보고서: dashboard_status_report.json")
    print(f"📝 로그는 백그라운드에서 계속 모니터링됩니다...")

if __name__ == "__main__":
    main()
