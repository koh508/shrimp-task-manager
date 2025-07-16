from integrated_launcher import IntegratedSystemLauncher

print("--- 의존성 확인 기능 테스트 시작 ---")
launcher = IntegratedSystemLauncher()
success = launcher.check_dependencies()
print(f"\n--- 테스트 종료. 결과: {'성공' if success else '실패'} ---")
