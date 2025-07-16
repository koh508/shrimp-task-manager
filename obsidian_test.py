import os
import time
from datetime import datetime
from pathlib import Path

# 기본 경로 설정 (사용자 환경에 맞게 변경)
VAULT_PATH = Path("D:/my workspace/OneDrive NEW/GNY")
CLIP_FOLDER = VAULT_PATH / "Clippings"

# 폴더 존재 확인 및 생성
if not CLIP_FOLDER.exists():
    CLIP_FOLDER.mkdir(parents=True, exist_ok=True)
    print("Clippings 폴더를 생성했습니다.")


# 테스트 파일 생성 함수
def create_test_file():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_file_{timestamp}.md"
    filepath = CLIP_FOLDER / filename

    content = f"""# 옵시디언 테스트 파일
- 생성 시간: {datetime.now().isoformat()}
- 내용: 이 파일이 Obsidian에 실제로 남아 있는지 확인합니다.
- 추가 텍스트: 시스템 통합 테스트용.
"""

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 테스트 파일 생성 성공: {filepath}")
        return filepath  # return the full path
    except Exception as e:
        print(f"❌ 파일 생성 실패: {e}")
        return None


# 파일 존재 확인 함수
def check_file_persistence(filepath):
    if filepath.exists():
        print(f"✅ 파일이 Clippings 폴더에 남아 있습니다: {filepath}")
    else:
        print(f"❌ 파일이 Clippings 폴더에서 사라졌습니다. (AI 에이전트가 처리했을 가능성이 높습니다)")


# 실행
if __name__ == "__main__":
    filepath = create_test_file()
    if filepath:
        # 5초 대기 후 확인 (동기화 및 에이전트 처리 시간 고려)
        print("AI 에이전트의 파일 처리 여부를 15초 후 확인합니다...")
        time.sleep(15)
        check_file_persistence(filepath)
