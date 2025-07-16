#!/usr/bin/env python3
"""
디버깅 유틸리티 모음
"""
import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

class DebugHelper:
    """디버깅 도우미 클래스"""
    
    @staticmethod
    def check_environment():
        """환경 상태 체크"""
        print("🔍 환경 상태 점검")
        print("-" * 40)
        
        # Python 정보
        print(f"🐍 Python 버전: {sys.version}")
        print(f"📁 실행 경로: {sys.executable}")
        print(f"💻 플랫폼: {sys.platform}")
        print(f"📂 작업 디렉토리: {os.getcwd()}")
        
        # 환경 변수 확인
        env_vars = ["GITHUB_TOKEN", "REPO_NAME", "RAILWAY_TOKEN", "MCP_SERVER_URL"]
        print("\n🔑 환경 변수:")
        for var in env_vars:
            value = os.getenv(var)
            status = "✅ 설정됨" if value and value != "demo_token" else "⚠️ 미설정"
            print(f"   {var}: {status}")
        
        # 필수 파일 확인
        required_files = [
            "github_mutual_development_system_demo.py",
            "integrated_development_system.py",
            "railway_deploy.py",
            "system_test_and_debug.py"
        ]
        
        print("\n📁 필수 파일:")
        for file in required_files:
            exists = "✅ 존재" if os.path.exists(file) else "❌ 없음"
            print(f"   {file}: {exists}")
    
    @staticmethod
    def test_imports():
        """패키지 임포트 테스트"""
        print("\n📦 패키지 임포트 테스트")
        print("-" * 40)
        
        packages = [
            ("github", "PyGithub"),
            ("requests", "Requests"),
            ("json", "JSON (내장)"),
            ("asyncio", "AsyncIO (내장)"),
            ("pathlib", "Pathlib (내장)"),
            ("datetime", "DateTime (내장)")
        ]
        
        for package, name in packages:
            try:
                __import__(package)
                print(f"✅ {name}: 임포트 성공")
            except ImportError as e:
                print(f"❌ {name}: 임포트 실패 - {e}")
                print(f"   해결방법: pip install {package}")
    
    @staticmethod
    def github_debug():
        """GitHub 연결 디버깅"""
        print("\n🔧 GitHub 연결 디버깅")
        print("-" * 40)
        
        token = os.getenv('GITHUB_TOKEN')
        repo_name = os.getenv('REPO_NAME')
        
        if not token or token == 'demo_token':
            print("❌ GITHUB_TOKEN이 설정되지 않음")
            print("해결방법:")
            print("1. GitHub → Settings → Developer settings → Personal access tokens")
            print("2. 'Generate new token' 클릭")
            print("3. 필요한 권한 선택 (repo, issues, actions)")
            print("4. 토큰 생성 후 환경 변수 설정:")
            print("   Windows: set GITHUB_TOKEN=your_token_here")
            print("   Linux/Mac: export GITHUB_TOKEN=your_token_here")
            return
        
        if not repo_name or repo_name == 'demo/repo':
            print("❌ REPO_NAME이 설정되지 않음")
            print("해결방법:")
            print("   Windows: set REPO_NAME=username/repository")
            print("   Linux/Mac: export REPO_NAME=username/repository")
            return
        
        try:
            from github import Github
            g = Github(token)
            user = g.get_user()
            print(f"✅ GitHub 인증 성공: {user.login}")
            
            try:
                repo = g.get_repo(repo_name)
                print(f"✅ 저장소 접근 성공: {repo.full_name}")
                print(f"   Private: {repo.private}")
                print(f"   Description: {repo.description}")
            except Exception as e:
                print(f"❌ 저장소 접근 실패: {e}")
                print("해결방법:")
                print("1. 저장소 이름 확인")
                print("2. 저장소 접근 권한 확인")
                print("3. 토큰 권한 확인")
                
        except Exception as e:
            print(f"❌ GitHub 연결 실패: {e}")
            print("해결방법:")
            print("1. 토큰 유효성 확인")
            print("2. 네트워크 연결 확인")
            print("3. 토큰 권한 확인")
    
    @staticmethod
    def railway_debug():
        """Railway 연결 디버깅"""
        print("\n🚂 Railway 연결 디버깅")
        print("-" * 40)
        
        # Railway CLI 확인
        import subprocess
        try:
            result = subprocess.run(['railway', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Railway CLI 설치됨: {result.stdout.strip()}")
            else:
                print("❌ Railway CLI 설치되지 않음")
                print("해결방법:")
                print("   npm install -g @railway/cli")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Railway CLI 없음")
            print("해결방법:")
            print("1. Node.js 설치")
            print("2. npm install -g @railway/cli")
            print("3. railway login")
        
        # Railway 토큰 확인
        token = os.getenv('RAILWAY_TOKEN')
        if not token or token == 'demo_token':
            print("⚠️ RAILWAY_TOKEN 미설정 (데모 모드)")
            print("실제 배포를 위한 설정 방법:")
            print("1. Railway 계정 생성 (https://railway.app)")
            print("2. 프로젝트 생성")
            print("3. API 토큰 발급")
            print("4. 환경 변수 설정")
        else:
            print("✅ Railway 토큰 설정됨")
    
    @staticmethod
    def create_env_file():
        """환경 변수 파일 생성"""
        print("\n📝 환경 변수 파일 생성")
        print("-" * 40)
        
        env_content = """# GitHub 설정
GITHUB_TOKEN=your_github_token_here
REPO_NAME=username/repository

# Railway 설정 (선택사항)
RAILWAY_TOKEN=your_railway_token_here

# MCP 설정 (선택사항)
MCP_SERVER_URL=http://localhost:8080
"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        print("✅ .env.example 파일 생성됨")
        print("💡 이 파일을 .env로 복사하고 실제 값으로 수정하세요")
        print("⚠️ .env 파일은 절대 Git에 커밋하지 마세요!")
    
    @staticmethod
    def quick_fix_guide():
        """자주 발생하는 문제 해결 가이드"""
        print("\n🛠️ 자주 발생하는 문제 해결 가이드")
        print("=" * 50)
        
        problems = [
            {
                "problem": "ImportError: No module named 'github'",
                "solution": "pip install pygithub requests"
            },
            {
                "problem": "GitHub 인증 실패",
                "solution": "1. 토큰 유효성 확인\n2. 토큰 권한 확인 (repo, issues)\n3. 환경 변수 설정 확인"
            },
            {
                "problem": "저장소 접근 실패",
                "solution": "1. 저장소 이름 확인 (username/repo)\n2. 저장소 접근 권한 확인\n3. Private 저장소인 경우 토큰 권한 확인"
            },
            {
                "problem": "Railway 배포 실패",
                "solution": "1. Railway CLI 설치\n2. railway login 실행\n3. 프로젝트 생성 및 연결"
            },
            {
                "problem": "환경 변수 설정 문제",
                "solution": "1. .env 파일 사용\n2. 시스템 환경 변수 설정\n3. IDE 환경 변수 설정"
            }
        ]
        
        for i, item in enumerate(problems, 1):
            print(f"\n{i}. {item['problem']}")
            print(f"해결방법: {item['solution']}")
    
    @staticmethod
    def run_mini_test():
        """간단한 미니 테스트 실행"""
        print("\n⚡ 미니 테스트 실행")
        print("-" * 40)
        
        tests = [
            ("Python 환경", lambda: sys.version_info >= (3, 7)),
            ("현재 디렉토리 쓰기 권한", lambda: os.access('.', os.W_OK)),
            ("GitHub 모듈", lambda: __import__('github') is not None),
            ("Requests 모듈", lambda: __import__('requests') is not None),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                status = "✅ 통과" if result else "❌ 실패"
                print(f"{status} {test_name}")
            except Exception as e:
                print(f"❌ {test_name}: {e}")

def main():
    """메인 디버깅 함수"""
    print("🔧 통합 시스템 디버깅 도구")
    print("=" * 50)
    
    helper = DebugHelper()
    
    # 기본 점검
    helper.check_environment()
    helper.test_imports()
    helper.github_debug()
    helper.railway_debug()
    
    # 유틸리티 실행
    helper.create_env_file()
    helper.quick_fix_guide()
    helper.run_mini_test()
    
    print("\n🎯 다음 단계:")
    print("1. 필요한 패키지 설치")
    print("2. 환경 변수 설정")
    print("3. python system_test_and_debug.py 실행")
    print("4. 문제 발생 시 생성된 디버그 로그 확인")

if __name__ == "__main__":
    main()
