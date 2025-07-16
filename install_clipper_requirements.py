#!/usr/bin/env python3
"""
옵시디언 AI 클리퍼 필요 패키지 설치 (간단 버전)
"""
import subprocess
import sys


def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 설치 실패: {e}")
        return False


def main():
    print("📦 AI 클리퍼 패키지 설치")
    print("=" * 40)

    # 필수 패키지만 설치
    required_packages = ["watchdog", "requests"]

    for package in required_packages:
        print(f"📥 {package} 설치 중...")
        install_package(package)

    print("\n✅ 설치 완료!")


if __name__ == "__main__":
    main()
