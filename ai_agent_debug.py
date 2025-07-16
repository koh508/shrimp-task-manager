import os
from pathlib import Path
import time
import logging
import shutil

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("D:/my workspace/OneDrive NEW/GNY/ai_agent_debug.log"), logging.StreamHandler()]
)

# 경로 설정
vault_path = Path("D:/my workspace/OneDrive NEW/GNY")
clippings_dir = vault_path / "Clippings"
processed_dir = vault_path / "Processed"
status_file = vault_path / "AI_Agent_Status.md"
error_dir = vault_path / "AI_Agent_Error"
reports_dir = vault_path / "AI_WS_Reports"

# 파일 감지 테스트
def test_file_detection():
    logging.info("파일 감지 테스트 시작")
    
    # 모든 필요한 폴더 확인
    for folder_name in ["Clippings", "Processed", "AI_WS_Reports", "AI_Agent_Error"]:
        folder = vault_path / folder_name
        if folder.exists():
            logging.info(f"✅ {folder_name} 폴더 존재함")
        else:
            logging.error(f"❌ {folder_name} 폴더 없음")
            try:
                folder.mkdir(parents=True, exist_ok=True)
                logging.info(f"  → {folder_name} 폴더 생성됨")
            except Exception as e:
                logging.error(f"  → {folder_name} 폴더 생성 실패: {str(e)}")
            
    # 클리핑 폴더에 있는 파일 목록
    files = list(clippings_dir.glob("*.md"))
    logging.info(f"Clippings 폴더 내 파일 수: {len(files)}")
    for file in files:
        logging.info(f"- {file.name}")
    
    # 상태 파일 업데이트 시도
    try:
        with open(status_file, "w", encoding="utf-8") as f:
            f.write("# AI Agent 실시간 대시보드\n\n")
            f.write(f"- 상태: 테스트 중\n")
            f.write(f"- 루프 라운드: 1\n")
            f.write(f"- 최근 처리: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 처리건수: {len(files)}\n")
            f.write(f"- 에러건수: 0\n")
            f.write(f"- 평균처리시간: 0.10초\n\n")
            f.write("## 최근 에러 5건\n")
        logging.info("✅ 상태 파일 업데이트 성공")
    except Exception as e:
        logging.error(f"❌ 상태 파일 업데이트 실패: {str(e)}")

    # 테스트 파일 처리 시도
    if files:
        try:
            test_file = files[0]
            dest_file = processed_dir / test_file.name
            shutil.copy2(test_file, dest_file)
            logging.info(f"✅ 테스트 파일 처리 성공: {test_file.name}")
            
            # 보고서 생성 시도
            report_file = reports_dir / f"처리보고서_{time.strftime('%Y%m%d%H%M%S')}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(f"# 파일 처리 보고서\n\n")
                f.write(f"- 파일명: {test_file.name}\n")
                f.write(f"- 처리 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- 결과: 성공\n")
            logging.info(f"✅ 보고서 생성 성공: {report_file.name}")
            
        except Exception as e:
            logging.error(f"❌ 테스트 파일 처리 실패: {str(e)}")
            
            # 에러 로그 생성 시도
            try:
                error_file = error_dir / f"에러로그_{time.strftime('%Y%m%d%H%M%S')}.md"
                with open(error_file, "w", encoding="utf-8") as f:
                    f.write(f"# 에러 로그\n\n")
                    f.write(f"- 파일명: {test_file.name}\n")
                    f.write(f"- 에러 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"- 에러 내용: {str(e)}\n")
                logging.info(f"✅ 에러 로그 생성 성공: {error_file.name}")
            except Exception as e2:
                logging.error(f"❌ 에러 로그 생성 실패: {str(e2)}")
    else:
        logging.warning("처리할 파일이 없습니다.")
        
# 테스트 실행
if __name__ == "__main__":
    logging.info("===== AI 에이전트 디버깅 테스트 시작 =====")
    test_file_detection()
    logging.info("===== AI 에이전트 디버깅 테스트 완료 =====")