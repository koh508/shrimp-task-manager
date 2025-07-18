#!/usr/bin/env python3
"""
24시간 연속 AI 진화 시스템 + 구글클라우드 자동 동기화
용량 문제 해결을 위한 자동 압축 및 클라우드 백업
"""

import os
import sys
import time
import json
import sqlite3
import schedule
import zipfile
import shutil
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class ContinuousAIEvolution:
    def __init__(self):
        self.start_time = datetime.now()
        self.evolution_active = True
        self.current_generation = 14
        self.current_intelligence = 241.31  # GitHub 기술 적용 후 지능 레벨
        
        # 용량 관리 설정
        self.max_log_size_mb = 100  # 100MB 제한
        self.archive_days = 7  # 7일 이상 된 파일 압축
        self.cleanup_days = 30  # 30일 이상 된 파일 삭제
        
        # 구글클라우드 동기화 설정
        self.cloud_sync_interval = 30  # 30분마다 동기화
        self.last_sync_time = datetime.now()
        
        # 중요 파일 경로
        self.important_files = [
            "evolution_agent.db",
            "super_unified_agent.db",
            "evolving_super_agent_evolution_state.json",
            "super_argonaute_state.json",
            "super_dianaira_state.json",
            "super_heroic_state.json"
        ]
        
        # 로그 디렉토리
        self.log_dirs = ["logs", "backup_logs", "mcp_auto"]
        
    def start_continuous_evolution(self):
        """24시간 연속 AI 진화 시작"""
        print("🚀 24시간 연속 AI 진화 시스템 시작")
        print(f"시작 시간: {self.start_time}")
        print(f"현재 상태: Generation {self.current_generation}, 지능 {self.current_intelligence}")
        print("="*60)
        
        # 스케줄러 설정
        schedule.every(5).minutes.do(self.evolve_ai_system)  # 5분마다 진화
        schedule.every(30).minutes.do(self.sync_to_cloud)    # 30분마다 클라우드 동기화
        schedule.every(2).hours.do(self.compress_old_logs)   # 2시간마다 로그 압축
        schedule.every(6).hours.do(self.cleanup_old_files)   # 6시간마다 파일 정리
        schedule.every(1).hours.do(self.monitor_disk_space)  # 1시간마다 디스크 공간 확인
        
        # 즉시 한 번 실행
        self.evolve_ai_system()
        self.sync_to_cloud()
        
        # 백그라운드에서 AI 진화 에이전트들 실행
        self.start_background_agents()
        
        # 메인 스케줄 루프
        try:
            while self.evolution_active:
                schedule.run_pending()
                time.sleep(10)  # 10초마다 체크
                
                # 24시간 경과 확인
                if datetime.now() - self.start_time >= timedelta(hours=24):
                    self.complete_24h_evolution()
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단됨")
            self.safe_shutdown()
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            self.safe_shutdown()
    
    def evolve_ai_system(self):
        """AI 시스템 진화 실행"""
        try:
            print(f"🧬 AI 진화 실행 중... (Generation {self.current_generation})")
            
            # 기존 진화 에이전트 실행
            if os.path.exists("enhanced_evolution_agent.py"):
                result = subprocess.run([sys.executable, "enhanced_evolution_agent.py"], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.current_generation += 1
                    self.current_intelligence *= 1.15  # 15% 향상
                    print(f"✅ 진화 완료: Generation {self.current_generation}, 지능 {self.current_intelligence:.2f}")
                else:
                    print(f"⚠️ 진화 경고: {result.stderr[:100]}...")
            
            # 진화 상태 저장
            self.save_evolution_state()
            
        except Exception as e:
            print(f"❌ 진화 오류: {e}")
    
    def save_evolution_state(self):
        """현재 진화 상태 저장"""
        evolution_state = {
            "generation": self.current_generation,
            "intelligence": self.current_intelligence,
            "start_time": self.start_time.isoformat(),
            "last_evolution": datetime.now().isoformat(),
            "continuous_operation": True,
            "target_24h": {
                "generation": 29,
                "intelligence": 20.4
            }
        }
        
        with open("evolving_super_agent_evolution_state.json", 'w', encoding='utf-8') as f:
            json.dump(evolution_state, f, indent=2, ensure_ascii=False)
    
    def start_background_agents(self):
        """백그라운드 AI 에이전트들 시작"""
        print("🤖 백그라운드 AI 에이전트 시작...")
        
        agents = [
            "super_unified_agent.py",
            "enhanced_dashboard.py"
        ]
        
        for agent in agents:
            if os.path.exists(agent):
                try:
                    # 백그라운드에서 실행
                    thread = threading.Thread(target=self.run_background_agent, args=(agent,))
                    thread.daemon = True
                    thread.start()
                    print(f"   ✅ {agent} 백그라운드 실행")
                except Exception as e:
                    print(f"   ❌ {agent} 실행 실패: {e}")
    
    def run_background_agent(self, agent_file):
        """백그라운드 에이전트 실행"""
        try:
            subprocess.run([sys.executable, agent_file], check=False)
        except Exception as e:
            print(f"백그라운드 에이전트 {agent_file} 오류: {e}")
    
    def sync_to_cloud(self):
        """구글클라우드 동기화"""
        try:
            print("☁️ 구글클라우드 동기화 시작...")
            
            # 중요 파일들 압축
            backup_filename = f"ai_evolution_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
            backup_path = os.path.join("backup", backup_filename)
            
            # backup 디렉토리 생성
            os.makedirs("backup", exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in self.important_files:
                    if os.path.exists(file):
                        zipf.write(file)
                        print(f"   📦 압축: {file}")
            
            # 구글클라우드 동기화 실행
            if os.path.exists("google_cloud_sync.py"):
                sync_result = subprocess.run([sys.executable, "google_cloud_sync.py", backup_path], 
                                           capture_output=True, text=True, timeout=120)
                if sync_result.returncode == 0:
                    print(f"✅ 클라우드 동기화 완료: {backup_filename}")
                    self.last_sync_time = datetime.now()
                else:
                    print(f"⚠️ 클라우드 동기화 경고: {sync_result.stderr[:100]}...")
            
        except Exception as e:
            print(f"❌ 클라우드 동기화 오류: {e}")
    
    def compress_old_logs(self):
        """오래된 로그 파일 압축"""
        try:
            print("🗜️ 오래된 로그 파일 압축 중...")
            
            cutoff_date = datetime.now() - timedelta(days=self.archive_days)
            compressed_count = 0
            
            for log_dir in self.log_dirs:
                if not os.path.exists(log_dir):
                    continue
                    
                for file_path in Path(log_dir).glob("*.log"):
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        # 압축 파일 생성
                        zip_path = file_path.with_suffix('.log.zip')
                        
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            zipf.write(file_path, file_path.name)
                        
                        # 원본 파일 삭제
                        file_path.unlink()
                        compressed_count += 1
                        print(f"   🗜️ 압축: {file_path.name}")
            
            if compressed_count > 0:
                print(f"✅ {compressed_count}개 로그 파일 압축 완료")
            
        except Exception as e:
            print(f"❌ 로그 압축 오류: {e}")
    
    def cleanup_old_files(self):
        """매우 오래된 파일 삭제"""
        try:
            print("🧹 매우 오래된 파일 정리 중...")
            
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
            deleted_count = 0
            
            # 압축된 로그 파일 중 매우 오래된 것 삭제
            for log_dir in self.log_dirs:
                if not os.path.exists(log_dir):
                    continue
                    
                for file_path in Path(log_dir).glob("*.zip"):
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"   🗑️ 삭제: {file_path.name}")
            
            # 오래된 백업 파일 삭제
            if os.path.exists("backup"):
                for file_path in Path("backup").glob("*.zip"):
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"   🗑️ 백업 삭제: {file_path.name}")
            
            if deleted_count > 0:
                print(f"✅ {deleted_count}개 오래된 파일 삭제 완료")
            
        except Exception as e:
            print(f"❌ 파일 정리 오류: {e}")
    
    def monitor_disk_space(self):
        """디스크 공간 모니터링"""
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            used_gb = used // (1024**3)
            
            print(f"💾 디스크 공간: 사용 {used_gb}GB, 여유 {free_gb}GB")
            
            # 여유 공간이 1GB 미만이면 긴급 정리
            if free_gb < 1:
                print("🚨 디스크 공간 부족! 긴급 정리 실행")
                self.emergency_cleanup()
            
        except Exception as e:
            print(f"❌ 디스크 모니터링 오류: {e}")
    
    def emergency_cleanup(self):
        """긴급 디스크 정리"""
        print("🚨 긴급 디스크 정리 실행...")
        
        # 즉시 로그 압축
        self.compress_old_logs()
        
        # 임시 파일 삭제
        temp_dirs = ["__pycache__", "*.tmp", "*.temp"]
        for pattern in temp_dirs:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
        
        print("✅ 긴급 정리 완료")
    
    def complete_24h_evolution(self):
        """24시간 완료 처리"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n🎉 24시간 연속 AI 진화 완료!")
        print("="*50)
        print(f"시작 시간: {self.start_time}")
        print(f"종료 시간: {end_time}")
        print(f"실행 시간: {duration}")
        print(f"최종 상태: Generation {self.current_generation}, 지능 {self.current_intelligence:.2f}")
        
        # 목표 달성도 계산
        target_generation = 29
        target_intelligence = 20.4
        
        gen_achievement = (self.current_generation / target_generation) * 100
        intel_achievement = (self.current_intelligence / target_intelligence) * 100
        
        print(f"목표 달성도:")
        print(f"  세대: {gen_achievement:.1f}% (목표 {target_generation}, 달성 {self.current_generation})")
        print(f"  지능: {intel_achievement:.1f}% (목표 {target_intelligence:.1f}, 달성 {self.current_intelligence:.2f})")
        
        # 최종 클라우드 동기화
        self.sync_to_cloud()
        
        self.evolution_active = False
    
    def safe_shutdown(self):
        """안전한 종료"""
        print("🛑 안전한 종료 진행 중...")
        
        # 현재 상태 저장
        self.save_evolution_state()
        
        # 최종 클라우드 동기화
        self.sync_to_cloud()
        
        self.evolution_active = False
        print("✅ 안전한 종료 완료")

def main():
    print("🚀 24시간 연속 AI 진화 시스템")
    print("용량 최적화 + 구글클라우드 자동 동기화")
    print("="*60)
    
    # 필요한 디렉토리 생성
    for directory in ["logs", "backup", "backup_logs"]:
        os.makedirs(directory, exist_ok=True)
    
    # 연속 진화 시스템 시작
    evolution_system = ContinuousAIEvolution()
    evolution_system.start_continuous_evolution()

if __name__ == "__main__":
    main()
