#!/usr/bin/env python3
"""
포괄적인 시스템 테스트 (완전 버전)
"""
import json
import os
import sys
import time
from datetime import datetime


def test_system_files():
    """시스템 파일 테스트"""
    print("📋 시스템 파일 테스트")
    print("-" * 40)

    # 현재 디렉토리의 모든 Python 파일 확인
    python_files = [f for f in os.listdir(".") if f.endswith(".py")]

    # 중요 파일들
    important_files = ["run_system.py", "simple_dashboard.py", "debug_utils.py", "smoke_test.py"]

    results = {}
    for file in important_files:
        exists = os.path.exists(file)
        results[file] = exists
        status = "✅" if exists else "❌"
        print(f"   {status} {file}")

    print(f"\n📊 총 Python 파일: {len(python_files)}개")

    # 설정 파일 확인
    config_files = ["config.json", "clipper_config.json"]
    for file in config_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "⚠️"
        print(f"   {status} {file}")

    return results


def test_python_environment():
    """Python 환경 테스트"""
    print("\n🐍 Python 환경 테스트")
    print("-" * 40)

    print(f"   Python 버전: {sys.version}")
    print(f"   실행 경로: {sys.executable}")
    print(f"   작업 디렉토리: {os.getcwd()}")
    print(f"   플랫폼: {sys.platform}")

    # 메모리 사용량 (가능한 경우)
    try:
        import psutil

        memory = psutil.virtual_memory()
        print(f"   메모리 사용률: {memory.percent:.1f}%")
    except ImportError:
        print("   메모리 정보: psutil 없음")

    return True


def test_package_imports():
    """패키지 임포트 테스트"""
    print("\n📦 패키지 임포트 테스트")
    print("-" * 40)

    packages = [
        ("json", "json"),
        ("os", "os"),
        ("sys", "sys"),
        ("time", "time"),
        ("datetime", "datetime"),
        ("pathlib", "pathlib"),
        ("requests", "requests"),
        ("github", "github"),
        ("watchdog", "watchdog"),
    ]

    results = {}
    for display_name, package_name in packages:
        try:
            __import__(package_name)
            results[display_name] = True
            print(f"   ✅ {display_name}")
        except ImportError:
            results[display_name] = False
            print(f"   ❌ {display_name}")

    return results


def test_github_connection():
    """GitHub 연결 테스트"""
    print("\n🔗 GitHub 연결 테스트")
    print("-" * 40)

    try:
        from github import Github

        # 환경 변수 또는 설정 파일에서 토큰 로드
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("   ⚠️ GITHUB_TOKEN 환경 변수 없음")
            print("   💡 데모 모드로 진행")
            return False

        g = Github(token)
        user = g.get_user()
        print(f"   ✅ GitHub 사용자: {user.login}")

        # Rate limit 확인
        rate_limit = g.get_rate_limit()
        print(f"   📊 API 사용량: {rate_limit.core.remaining}/{rate_limit.core.limit}")

        return True

    except Exception as e:
        print(f"   ❌ GitHub 연결 실패: {e}")
        return False


def run_mini_performance_test():
    """간단한 성능 테스트"""
    print("\n⚡ 간단한 성능 테스트")
    print("-" * 40)

    # 파일 I/O 테스트
    test_file = "test_performance.tmp"

    try:
        # 쓰기 테스트
        start_time = time.time()
        with open(test_file, "w") as f:
            for i in range(1000):
                f.write(f"테스트 라인 {i}\n")
        write_time = time.time() - start_time

        # 읽기 테스트
        start_time = time.time()
        with open(test_file, "r") as f:
            lines = f.readlines()
        read_time = time.time() - start_time

        # 정리
        os.remove(test_file)

        print(f"   ✅ 파일 쓰기: {write_time:.3f}초")
        print(f"   ✅ 파일 읽기: {read_time:.3f}초")
        print(f"   ✅ 읽은 라인 수: {len(lines)}")

        return True

    except Exception as e:
        print(f"   ❌ 성능 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🧪 포괄적인 시스템 테스트")
    print("=" * 60)

    # 테스트 실행
    file_results = test_system_files()
    env_results = test_python_environment()
    package_results = test_package_imports()
    github_results = test_github_connection()
    performance_results = run_mini_performance_test()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    # 파일 테스트 결과
    file_success = sum(file_results.values())
    file_total = len(file_results)
    print(f"📁 파일 테스트: {file_success}/{file_total} 성공")

    # 패키지 테스트 결과
    package_success = sum(package_results.values())
    package_total = len(package_results)
    print(f"📦 패키지 테스트: {package_success}/{package_total} 성공")

    # 기타 테스트 결과
    print(f"🐍 환경 테스트: ✅ 완료")
    print(f"🔗 GitHub 연결: {'✅' if github_results else '⚠️'} {'성공' if github_results else '데모 모드'}")
    print(
        f"⚡ 성능 테스트: {'✅' if performance_results else '❌'} {'성공' if performance_results else '실패'}"
    )

    # 전체 성공률 계산
    total_tests = file_total + package_total + 3  # 환경, GitHub, 성능
    successful_tests = (
        file_success
        + package_success
        + 1
        + (1 if github_results else 0)
        + (1 if performance_results else 0)
    )

    overall_success = (successful_tests / total_tests) * 100
    print(f"\n🎯 전체 성공률: {overall_success:.1f}%")

    # 상태 판정
    if overall_success >= 90:
        print("🎉 시스템 상태: 우수")
    elif overall_success >= 70:
        print("⚠️ 시스템 상태: 양호")
    elif overall_success >= 50:
        print("⚠️ 시스템 상태: 보통")
    else:
        print("❌ 시스템 상태: 개선 필요")

    # 개선 제안
    print(f"\n💡 개선 제안:")

    if package_results.get("github", False):
        print("   ✅ GitHub 연동 준비 완료")
    else:
        print("   📝 GitHub 연동: pip install pygithub")

    if not github_results:
        print("   🔑 GitHub 토큰 설정 필요")


if __name__ == "__main__":
    main()
