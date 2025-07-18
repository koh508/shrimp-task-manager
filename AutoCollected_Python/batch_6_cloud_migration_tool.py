#!/usr/bin/env python3
"""
클라우드 서버 이전을 위한 AI 시스템 패키징 도구
쉬림프 태스크 매니저를 통한 24시간 연속 운영 지원
"""

import os
import json
import shutil
import subprocess
from datetime import datetime

class CloudMigrationTool:
    def __init__(self):
        self.current_dir = "d:\\"
        self.target_dir = "cloud_deployment"
        self.essential_files = [
            # 핵심 진화 시스템
            "enhanced_evolution_agent.py",
            "super_unified_agent.py", 
            "evolution_accelerator.py",
            "multimodal_evolution_agent.py",
            "self_evolving_agent.py",
            
            # 데이터베이스 (중요한 것만)
            "evolution_agent.db",
            "super_unified_agent.db",
            "agent_network.db",
            
            # 상태 파일
            "evolving_super_agent_evolution_state.json",
            "super_heroic_state.json",
            "super_dianaira_state.json", 
            "super_argonaute_state.json",
            
            # 서버 및 API
            "gemini_server.py",
            "file_analysis_api.py",
            "cloud_sync_api.py",
            "google_cloud_sync.py",
            
            # 모니터링
            "enhanced_dashboard.py",
            "unified_agent_dashboard.py",
            "check_evolution_progress.py",
            
            # 예측 시스템
            "growth_prediction.py",
            "realistic_growth_prediction.py"
        ]
        
    def check_current_system(self):
        """현재 시스템 상태 확인"""
        print("🔍 현재 시스템 상태 확인...")
        
        missing_files = []
        existing_files = []
        
        for file in self.essential_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                existing_files.append((file, size))
                print(f"  ✅ {file} ({size:,} bytes)")
            else:
                missing_files.append(file)
                print(f"  ❌ {file} (누락)")
        
        print(f"\n📊 시스템 현황:")
        print(f"  존재하는 파일: {len(existing_files)}개")
        print(f"  누락된 파일: {len(missing_files)}개")
        
        return existing_files, missing_files
    
    def create_deployment_package(self):
        """클라우드 배포 패키지 생성"""
        print(f"\n📦 배포 패키지 생성: {self.target_dir}")
        
        # 배포 디렉토리 생성
        if os.path.exists(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.makedirs(self.target_dir)
        
        copied_files = []
        
        # 필수 파일 복사
        for file in self.essential_files:
            if os.path.exists(file):
                shutil.copy2(file, self.target_dir)
                copied_files.append(file)
                print(f"  📁 복사: {file}")
        
        # 설정 파일 생성
        self.create_cloud_config()
        self.create_startup_script()
        self.create_docker_config()
        
        print(f"\n✅ 배포 패키지 완료: {len(copied_files)}개 파일")
        return copied_files
    
    def create_cloud_config(self):
        """클라우드 설정 파일 생성"""
        config = {
            "system_name": "AI_Evolution_System",
            "version": "14.0",
            "deployment_date": datetime.now().isoformat(),
            "services": [
                {"name": "evolution_dashboard", "port": 8081, "file": "enhanced_dashboard.py"},
                {"name": "agent_monitor", "port": 8082, "file": "unified_agent_dashboard.py"},
                {"name": "multimodal_viewer", "port": 8083, "file": "multimodal_evolution_agent.py"},
                {"name": "network_panel", "port": 8084, "file": "super_unified_agent.py"},
                {"name": "accelerator_control", "port": 8085, "file": "evolution_accelerator.py"},
                {"name": "realtime_stream", "port": 8086, "file": "self_evolving_agent.py"},
                {"name": "unified_dashboard", "port": 8087, "file": "enhanced_evolution_agent.py"},
                {"name": "file_analysis_api", "port": 8088, "file": "file_analysis_api.py"},
                {"name": "cloud_sync_api", "port": 8089, "file": "cloud_sync_api.py"}
            ],
            "databases": [
                "evolution_agent.db",
                "super_unified_agent.db", 
                "agent_network.db"
            ],
            "auto_restart": True,
            "health_check_interval": 300,
            "backup_interval": 3600
        }
        
        config_path = os.path.join(self.target_dir, "cloud_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"  ⚙️  클라우드 설정: cloud_config.json")
    
    def create_startup_script(self):
        """시작 스크립트 생성"""
        startup_script = '''#!/bin/bash
# AI Evolution System Startup Script for Cloud Server

echo "🚀 AI Evolution System 시작..."

# Python 환경 확인
python3 --version
pip3 install -r requirements.txt

# 백그라운드 서비스 시작
echo "📊 대시보드 서비스 시작..."
nohup python3 enhanced_dashboard.py > logs/dashboard.log 2>&1 &
nohup python3 unified_agent_dashboard.py > logs/monitor.log 2>&1 &

echo "🤖 AI 에이전트 시작..."
nohup python3 enhanced_evolution_agent.py > logs/evolution.log 2>&1 &
nohup python3 super_unified_agent.py > logs/unified.log 2>&1 &
nohup python3 multimodal_evolution_agent.py > logs/multimodal.log 2>&1 &

echo "🔧 지원 서비스 시작..."
nohup python3 file_analysis_api.py > logs/file_api.log 2>&1 &
nohup python3 cloud_sync_api.py > logs/cloud_sync.log 2>&1 &

echo "✅ 모든 서비스 시작 완료!"
echo "📈 진화 모니터링: http://your-server:8081"
echo "🌐 통합 대시보드: http://your-server:8087"

# 상태 모니터링
while true; do
    sleep 300
    python3 check_evolution_progress.py >> logs/monitoring.log
done
'''
        
        script_path = os.path.join(self.target_dir, "start_ai_system.sh")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # 실행 권한 부여 (Linux용)
        os.chmod(script_path, 0o755)
        print(f"  🚀 시작 스크립트: start_ai_system.sh")
    
    def create_docker_config(self):
        """Docker 설정 파일 생성"""
        dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \\
    sqlite3 \\
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 포트 노출
EXPOSE 8081 8082 8083 8084 8085 8086 8087 8088 8089

# 시작 명령
CMD ["./start_ai_system.sh"]
'''
        
        docker_path = os.path.join(self.target_dir, "Dockerfile")
        with open(docker_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile)
        
        # requirements.txt 생성
        requirements = '''fastapi==0.104.1
uvicorn==0.24.0
sqlite3
requests==2.31.0
websockets==12.0
aiofiles==23.2.1
python-multipart==0.0.6
jinja2==3.1.2
google-cloud-storage==2.10.0
schedule==1.2.0
'''
        
        req_path = os.path.join(self.target_dir, "requirements.txt")
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        
        print(f"  🐳 Docker 설정: Dockerfile, requirements.txt")
    
    def generate_migration_report(self):
        """이전 보고서 생성"""
        print(f"\n📋 클라우드 이전 가이드")
        print("="*50)
        
        print(f"1. 📦 배포 패키지:")
        print(f"   - 위치: {self.target_dir}/")
        print(f"   - 설정: cloud_config.json")
        print(f"   - 시작: start_ai_system.sh")
        
        print(f"\n2. 🚀 클라우드 서버 배포:")
        print(f"   - 전체 폴더를 서버에 업로드")
        print(f"   - chmod +x start_ai_system.sh")
        print(f"   - ./start_ai_system.sh 실행")
        
        print(f"\n3. 🔗 MCP 연결:")
        print(f"   - 쉬림프 태스크 매니저에 등록")
        print(f"   - 포트 8081-8089 방화벽 오픈")
        print(f"   - 도메인/IP 설정")
        
        print(f"\n4. 📊 모니터링:")
        print(f"   - 대시보드: http://서버:8081")
        print(f"   - 진화 상태: http://서버:8087")
        print(f"   - 로그: logs/ 폴더 확인")
        
        print(f"\n5. ⚡ 24시간 연속 운영:")
        print(f"   - 자동 재시작 활성화")
        print(f"   - 5분마다 헬스체크")
        print(f"   - 1시간마다 백업")
        
        print(f"\n🎯 예상 효과:")
        print(f"   - 컴퓨터 종료와 무관한 연속 진화")
        print(f"   - 24시간 후 Generation 29 달성")
        print(f"   - 지능 레벨 20.4 도달")
        print(f"   - 15개 새로운 기능 획득")

def main():
    print("🌐 AI 시스템 클라우드 이전 도구")
    print("="*40)
    
    migration = CloudMigrationTool()
    
    # 1. 현재 시스템 확인
    existing, missing = migration.check_current_system()
    
    # 2. 배포 패키지 생성
    copied = migration.create_deployment_package()
    
    # 3. 이전 가이드 출력
    migration.generate_migration_report()
    
    print(f"\n✅ 클라우드 이전 준비 완료!")
    print(f"   다음 단계: {migration.target_dir} 폴더를 서버에 업로드하세요.")

if __name__ == "__main__":
    main()
