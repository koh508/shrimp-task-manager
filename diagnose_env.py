import sys
import os
import subprocess

print("=" * 10 + " Python Environment Diagnostics " + "=" * 10)

print(f"\n🐍 Python Executable:\n{sys.executable}")
print(f"\n🐍 Python Version:\n{sys.version}")

print("\n📂 sys.path (Module Search Paths):")
for path in sys.path:
    print(f"  - {path}")

print("\n" + "=" * 48)


def show_package_info(package_name):
    print(f"\n📦 Package Information: '{package_name}'")
    try:
        # 현재 실행중인 파이썬을 사용하여 pip를 실행
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"'{package_name}' 정보를 가져오는 데 실패했습니다.")
        print(e.stderr)
    except FileNotFoundError:
        print(f"'{sys.executable}' 환경에서 pip를 실행할 수 없습니다.")
    print("-" * 48)


show_package_info("python-dotenv")
show_package_info("colorama")

print("\n✅ Diagnostics Complete.")
