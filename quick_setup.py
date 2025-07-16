#!/usr/bin/env python3
"""
빠른 실행 스크립트 - 문제 없이 바로 실행
"""
import subprocess
import sys
import os
from datetime import datetime

def quick_setup():
    """빠른 설정 및 실행"""
    print("🚀 통합 시스템 빠른 설정")
    print("=" * 40)
    
    # 1. 필수 패키지 확인
    required_packages = ['flask', 'requests', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    # 2. 누락된 패키지 설치
    if missing_packages:
        print(f"\n📦 누락된 패키지 설치 중: {missing_packages}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)
    
    # 3. 간단한 대시보드 실행
    dashboard_code = '''
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return """
    🚀 통합 시스템 대시보드
    시스템 상태: 정상
    현재 시간: {}
    
        setInterval(() => {
            document.getElementById('time').textContent = new Date().toLocaleString();
        }, 1000);
    
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': '테스트 모드'
    })

if __name__ == '__main__':
    print("🌐 대시보드 시작: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
'''
    
    # 4. 대시보드 파일 생성
    with open('quick_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(dashboard_code)
    
    print("\n✅ 빠른 설정 완료!")
    print("📋 실행 옵션:")
    print("1. python quick_dashboard.py")
    print("2. 브라우저에서 http://localhost:5000 접속")

if __name__ == "__main__":
    quick_setup()
