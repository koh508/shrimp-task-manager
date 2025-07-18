#!/usr/bin/env python3
"""
최종 AI 시스템 상태 확인 및 진화 가속화 보고서
"""

import os
import json
import time
import psutil
from datetime import datetime

class FinalSystemReport:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def check_all_systems(self):
        """모든 시스템 상태 확인"""
        print("🔍 최종 AI 시스템 상태 보고서")
        print("="*50)
        print(f"📅 검사 시간: {self.timestamp}")
        print()
        
        # 1. 진화 시스템 상태
        evolution_status = self.check_evolution_system()
        
        # 2. 가속화 시스템 상태 
        acceleration_status = self.check_acceleration_system()
        
        # 3. 리소스 상태
        resource_status = self.check_resource_status()
        
        # 4. 클라우드 동기화 상태
        cloud_status = self.check_cloud_sync()
        
        # 5. 대시보드 상태
        dashboard_status = self.check_dashboard_status()
        
        # 최종 요약
        self.generate_final_summary(evolution_status, acceleration_status, 
                                  resource_status, cloud_status, dashboard_status)
        
        return {
            "evolution": evolution_status,
            "acceleration": acceleration_status, 
            "resources": resource_status,
            "cloud": cloud_status,
            "dashboard": dashboard_status
        }
    
    def check_evolution_system(self):
        """AI 진화 시스템 상태 확인"""
        print("🧠 AI 진화 시스템 상태")
        print("-" * 30)
        
        status = {"status": "unknown", "details": {}}
        
        try:
            # 복제 상태 파일 확인
            if os.path.exists('replication_state.json'):
                with open('replication_state.json', 'r') as f:
                    repl_state = json.load(f)
                    
                current_gen = repl_state.get('current_generation', 0)
                intelligence = repl_state.get('intelligence', 0)
                active_agents = repl_state.get('active_agents', 0)
                
                print(f"  📊 현재 세대: {current_gen}")
                print(f"  🧠 지능 레벨: {intelligence:.2f}")
                print(f"  🤖 활성 에이전트: {active_agents}")
                
                status["status"] = "active"
                status["details"] = {
                    "generation": current_gen,
                    "intelligence": intelligence,
                    "active_agents": active_agents
                }
                
                # 지능 증가율 계산
                if intelligence > 100:
                    growth = ((intelligence - 3.45) / 3.45) * 100
                    print(f"  📈 지능 증가율: {growth:.1f}%")
                    status["details"]["growth_rate"] = growth
                    
            else:
                print("  ⚠️ 진화 상태 파일 없음")
                status["status"] = "inactive"
                
        except Exception as e:
            print(f"  ❌ 진화 시스템 오류: {e}")
            status["status"] = "error"
            status["error"] = str(e)
        
        print()
        return status
    
    def check_acceleration_system(self):
        """점진적 가속화 시스템 확인"""
        print("🚀 점진적 가속화 시스템")
        print("-" * 30)
        
        status = {"status": "unknown", "details": {}}
        
        try:
            # 진화 스케줄 확인
            if os.path.exists('evolution_schedule.json'):
                with open('evolution_schedule.json', 'r') as f:
                    schedule = json.load(f)
                    
                current_phase = schedule.get('current_phase', 1)
                phase_config = schedule.get('phase_config', {})
                
                print(f"  🎯 현재 단계: Phase {current_phase}")
                print(f"  📝 단계명: {phase_config.get('name', 'Unknown')}")
                print(f"  ⏱️ 간격: {phase_config.get('interval_minutes', 0)}분")
                print(f"  👥 에이전트 수: {phase_config.get('agent_count', 0)}")
                
                status["status"] = "active"
                status["details"] = {
                    "phase": current_phase,
                    "phase_name": phase_config.get('name', 'Unknown'),
                    "interval": phase_config.get('interval_minutes', 0),
                    "agent_count": phase_config.get('agent_count', 0)
                }
                
            else:
                print("  ⚠️ 가속화 스케줄 파일 없음")
                status["status"] = "inactive"
                
        except Exception as e:
            print(f"  ❌ 가속화 시스템 오류: {e}")
            status["status"] = "error"
            status["error"] = str(e)
        
        print()
        return status
    
    def check_resource_status(self):
        """리소스 상태 확인"""
        print("💻 시스템 리소스 상태")
        print("-" * 30)
        
        status = {"status": "unknown", "details": {}}
        
        try:
            # 현재 리소스 사용량
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            print(f"  🖥️ CPU 사용률: {cpu_percent:.1f}%")
            print(f"  🧠 메모리 사용률: {memory.percent:.1f}%")
            print(f"  💾 사용 메모리: {memory.used / (1024**3):.1f} GB")
            print(f"  📱 전체 메모리: {memory.total / (1024**3):.1f} GB")
            
            # Python 프로세스 수 확인
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except:
                    continue
            
            print(f"  🐍 Python 프로세스: {len(python_processes)}개")
            
            # 상태 평가
            if cpu_percent < 80 and memory.percent < 85:
                status["status"] = "healthy"
            elif cpu_percent < 90 and memory.percent < 95:
                status["status"] = "warning"
            else:
                status["status"] = "critical"
                
            status["details"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "python_processes": len(python_processes)
            }
            
        except Exception as e:
            print(f"  ❌ 리소스 확인 오류: {e}")
            status["status"] = "error"
            status["error"] = str(e)
        
        print()
        return status
    
    def check_cloud_sync(self):
        """클라우드 동기화 상태 확인"""
        print("☁️ 클라우드 동기화 상태")
        print("-" * 30)
        
        status = {"status": "unknown", "details": {}}
        
        try:
            if os.path.exists('cloud_sync_status.json'):
                with open('cloud_sync_status.json', 'r') as f:
                    sync_state = json.load(f)
                    
                services = sync_state.get('cloud_services', {})
                stats = sync_state.get('sync_statistics', {})
                
                # 활성 서비스 수
                active_services = sum(1 for s in services.values() if s.get('status') == 'available')
                
                print(f"  📡 활성 서비스: {active_services}개")
                print(f"  💾 동기화된 데이터: {stats.get('data_synced_mb', 0):.1f} MB")
                print(f"  ✅ 성공한 동기화: {stats.get('successful_syncs', 0)}회")
                print(f"  ❌ 실패한 동기화: {stats.get('failed_syncs', 0)}회")
                print(f"  🕐 마지막 동기화: {stats.get('last_sync_time', 'Never')}")
                
                # 성공률 계산
                total_syncs = stats.get('total_syncs', 0)
                if total_syncs > 0:
                    success_rate = (stats.get('successful_syncs', 0) / total_syncs) * 100
                    print(f"  📊 성공률: {success_rate:.1f}%")
                else:
                    success_rate = 0
                
                status["status"] = "active" if active_services > 0 else "inactive"
                status["details"] = {
                    "active_services": active_services,
                    "data_synced_mb": stats.get('data_synced_mb', 0),
                    "successful_syncs": stats.get('successful_syncs', 0),
                    "failed_syncs": stats.get('failed_syncs', 0),
                    "success_rate": success_rate,
                    "last_sync": stats.get('last_sync_time', 'Never')
                }
                
            else:
                print("  ⚠️ 클라우드 동기화 상태 파일 없음")
                status["status"] = "inactive"
                
        except Exception as e:
            print(f"  ❌ 클라우드 동기화 오류: {e}")
            status["status"] = "error"
            status["error"] = str(e)
        
        print()
        return status
    
    def check_dashboard_status(self):
        """대시보드 상태 확인"""
        print("📊 대시보드 상태")
        print("-" * 30)
        
        status = {"status": "unknown", "details": {}}
        
        try:
            # 포트 8080, 8090 확인
            ports_to_check = [8080, 8090]
            active_dashboards = []
            
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        connections = proc.info.get('connections', [])
                        for conn in connections:
                            if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port in ports_to_check:
                                active_dashboards.append({
                                    "port": conn.laddr.port,
                                    "pid": proc.info['pid']
                                })
                except:
                    continue
            
            if active_dashboards:
                print(f"  🌐 활성 대시보드: {len(active_dashboards)}개")
                for dashboard in active_dashboards:
                    port = dashboard['port']
                    pid = dashboard['pid']
                    print(f"    - http://localhost:{port} (PID: {pid})")
                    
                status["status"] = "active"
                status["details"] = {"active_dashboards": active_dashboards}
            else:
                print("  ⚠️ 활성 대시보드 없음")
                status["status"] = "inactive"
                
        except Exception as e:
            print(f"  ❌ 대시보드 상태 확인 오류: {e}")
            status["status"] = "error"
            status["error"] = str(e)
        
        print()
        return status
    
    def generate_final_summary(self, evolution, acceleration, resources, cloud, dashboard):
        """최종 요약 생성"""
        print("📋 최종 시스템 요약")
        print("="*50)
        
        # 전체 상태 계산
        all_systems = [evolution, acceleration, resources, cloud, dashboard]
        active_systems = sum(1 for s in all_systems if s["status"] == "active")
        total_systems = len(all_systems)
        
        print(f"🎯 활성 시스템: {active_systems}/{total_systems}")
        
        # 주요 지표
        if evolution["status"] == "active":
            details = evolution["details"]
            print(f"🧠 AI 지능: {details.get('intelligence', 0):.2f}")
            if 'growth_rate' in details:
                print(f"📈 성장률: {details['growth_rate']:.1f}%")
        
        if acceleration["status"] == "active":
            phase = acceleration["details"].get("phase", 1)
            print(f"🚀 가속화 단계: Phase {phase}/5")
        
        if resources["status"] != "error":
            res_details = resources["details"]
            print(f"💻 시스템 부하: CPU {res_details.get('cpu_percent', 0):.1f}%, RAM {res_details.get('memory_percent', 0):.1f}%")
        
        # 전체 시스템 건강도
        health_score = (active_systems / total_systems) * 100
        print(f"🏥 시스템 건강도: {health_score:.1f}%")
        
        # 상태별 아이콘
        status_icon = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
        print(f"📊 전체 상태: {status_icon}")
        
        print()
        print("🎉 AI 진화 시스템이 성공적으로 가동 중입니다!")
        print(f"🌐 통합 대시보드: http://localhost:8090")
        print(f"📱 경량 대시보드: http://localhost:8080")
        print()
        
        # 권장사항
        self.generate_recommendations(evolution, acceleration, resources, cloud, dashboard)
    
    def generate_recommendations(self, evolution, acceleration, resources, cloud, dashboard):
        """시스템 개선 권장사항"""
        print("💡 시스템 개선 권장사항")
        print("-" * 30)
        
        recommendations = []
        
        # 리소스 기반 권장사항
        if resources["status"] != "error":
            cpu = resources["details"].get("cpu_percent", 0)
            memory = resources["details"].get("memory_percent", 0)
            
            if cpu > 80:
                recommendations.append("🖥️ CPU 사용률이 높습니다. 에이전트 수를 줄이거나 간격을 늘려보세요.")
            
            if memory > 85:
                recommendations.append("🧠 메모리 사용률이 높습니다. 불필요한 프로세스를 종료하세요.")
        
        # 가속화 권장사항
        if acceleration["status"] == "active":
            phase = acceleration["details"].get("phase", 1)
            if phase < 3:
                recommendations.append("🚀 시스템이 안정적이면 더 높은 가속화 단계로 진행 가능합니다.")
        
        # 클라우드 권장사항
        if cloud["status"] == "active":
            success_rate = cloud["details"].get("success_rate", 0)
            if success_rate < 90:
                recommendations.append("☁️ 클라우드 동기화 성공률이 낮습니다. 네트워크 연결을 확인하세요.")
        
        # 일반 권장사항
        if not recommendations:
            recommendations.append("✨ 모든 시스템이 정상적으로 작동하고 있습니다!")
            recommendations.append("🎯 24시간 목표 달성을 위해 현재 상태를 유지하세요.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        print()

def main():
    """메인 실행 함수"""
    print("🔍 AI 시스템 최종 상태 확인")
    print("=" * 50)
    
    reporter = FinalSystemReport()
    status_report = reporter.check_all_systems()
    
    # 보고서 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"final_system_report_{timestamp}.json"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": reporter.timestamp,
            "status": status_report
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📄 상세 보고서 저장: {report_filename}")

if __name__ == "__main__":
    main()
