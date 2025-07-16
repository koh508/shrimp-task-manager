# Cache Bust: 2025-07-17_v3
import asyncio
import logging
import os
import shutil
import time
import traceback
import json
from websockets.legacy.client import connect
from pathlib import Path
from datetime import datetime

# 추가 변수 (사용자 설정 가능)
TIMEOUT = 20  # 파일 대기 시간 (초)
LOG_LEVEL = logging.INFO  # 로그 레벨 (DEBUG, INFO, ERROR 등)
MCP_RETRY = 3  # MCP 재연결 시도 횟수
TEMP_DIR = Path(os.environ.get('TEMP', '/tmp')) / 'ultra_ai_temp'  # 임시 폴더 경로

# Google Drive 경로 설정
GD_ROOT = Path("D:/Google Drive/GNY")  # 사용자 환경에 맞게 변경

# --- 새로운 폴더/권한 확인 함수 ---
def ensure_path(path_str):
    """주어진 경로가 존재하는지 확인하고, 없으면 생성합니다. 권한 오류 발생 시 예외를 발생시킵니다."""
    p = Path(path_str)
    try:
        p.mkdir(parents=True, exist_ok=True)
        # 로거가 설정되기 전일 수 있으므로 print 사용
        print(f"[OK] 경로 확인/생성 완료: {p}")
        return p
    except PermissionError as e:
        print(f"[CRITICAL] 폴더 생성 권한 오류: {p}. 스크립트를 종료합니다.")
        raise e
    except Exception as e:
        print(f"[ERROR] 폴더 생성 중 예기치 않은 오류: {p} ({e})")
        raise e

# 단일 로깅 설정
def setup_logging(log_dir):
    logger = logging.getLogger()
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ultra_ai_{ts}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        print(f"[OK] 로그 설정 완료. 로그 파일: {log_file}")
        return logger
    except Exception as e:
        # 로깅 설정 실패 시 기본 로깅 사용
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
        logging.error(f"[ERROR] 로그 파일 핸들러 설정 실패: {e}")
        return logging.getLogger()

class ErrorNotifier:
    def __init__(self, error_dir):
        self.error_dir = ensure_path(error_dir)

    def notify_error(self, message):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        err_file = self.error_dir / f"error_{ts}.log"
        err_file.write_text(message, encoding="utf-8")
        logger.error(f"오류가 기록되었습니다: {err_file}")

class MCPClient:
    def __init__(self, error_notifier):
        self.uri = "ws://127.0.0.1:25182/mcp"
        self.websocket = None
        self.error_notifier = error_notifier
        self.is_connected = False

    async def connect(self):
        for attempt in range(MCP_RETRY):
            try:
                self.websocket = await connect(self.uri)
                self.is_connected = True
                logger.info("🎉 MCP에 성공적으로 연결되었습니다.")
                return True
            except Exception as e:
                logger.warning(f"❗ MCP 연결 실패 (시도 {attempt + 1}/{MCP_RETRY}): {e}")
                if attempt < MCP_RETRY - 1:
                    await asyncio.sleep(5)
        logger.error("MCP에 최종적으로 연결하지 못했습니다.")
        self.error_notifier.notify_error("MCP 최종 연결 실패")
        return False

    async def send_task(self, file_content):
        if not self.is_connected:
            logger.warning("MCP가 연결되지 않아 작업을 전송할 수 없습니다. 재연결 시도...")
            if not await self.connect():
                return False

        try:
            task_data = {
                "type": "task",
                "payload": {
                    "tool_code": f'\n```markdown\n{file_content}\n```',
                    "tool_name": "create_goal_and_task_from_text"
                }
            }
            await self.websocket.send(json.dumps(task_data))
            logger.info("✅ MCP에 작업을 성공적으로 전송했습니다.")
            return True
        except Exception as e:
            logger.error(f"MCP 작업 전송 중 오류 발생: {e}")
            self.is_connected = False
            self.error_notifier.notify_error(f"MCP 작업 전송 오류: {e}")
            return False

class StableClipAgent:
    def __init__(self):
        self.clip_dir = ensure_path(GD_ROOT / "Clippings")
        self.proc_dir = ensure_path(GD_ROOT / "Processed")
        self.error_dir = ensure_path(GD_ROOT / "Errors")
        self.log_dir = ensure_path(GD_ROOT / "Logs")
        
        global logger
        logger = setup_logging(self.log_dir)

        self.error_notifier = ErrorNotifier(self.error_dir)
        self.mcp_client = MCPClient(self.error_notifier)
        self.retry_map = {}

    def read_file_content(self, path: Path):
        try:
            return path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.warning(f"❗ 파일 없음: {path}")
            return None
        except Exception as e:
            logger.error(f"파일 읽기 오류: {path}, {e}")
            self.error_notifier.notify_error(f"파일 읽기 오류: {path}\n{traceback.format_exc()}")
            return None

    async def process_single_clip(self, file: Path):
        logger.info(f"- 처리 시작: {file.name}")
        if not self.wait_for_file_ready(file):
            logger.warning(f"파일이 준비되지 않아 건너뜁니다: {file.name}")
            return

        content = self.read_file_content(file)
        if content is None:
            return

        if await self.mcp_client.send_task(content):
            try:
                shutil.move(str(file), str(self.proc_dir / file.name))
                logger.info(f"  -> 처리 완료, 이동: {self.proc_dir / file.name}")
                if file.name in self.retry_map: del self.retry_map[file.name]
            except PermissionError:
                logger.error(f"권한 오류로 파일 이동 실패: {file.name}. 임시 폴더에 복사 시도.")
                try:
                    TEMP_DIR.mkdir(exist_ok=True)
                    shutil.copy(str(file), str(TEMP_DIR / file.name))
                    logger.info(f"임시 폴더로 복사 성공: {TEMP_DIR / file.name}")
                except Exception as copy_e:
                    logger.critical(f"임시 폴더 복사조차 실패: {copy_e}")
            except Exception as e:
                logger.error(f"파일 이동 중 예외 발생: {e}")
                self.retry_map[file.name] = self.retry_map.get(file.name, 0) + 1
                if self.retry_map[file.name] > 3:
                    errfile = self.error_dir / f"error_move_{file.name}.md"
                    errfile.write_text(f"# 파일 이동 반복 실패: {file}\n", encoding="utf-8")
        else:
            logger.error(f"MCP 작업 생성 실패로 파일 이동 안함: {file.name}")

    def wait_for_file_ready(self, path: Path, timeout=TIMEOUT):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with open(path, 'r'): pass
                return True
            except IOError:
                time.sleep(0.5)
        return False

# 메인 실행 로직 (Resilient Loop)
# Triggering new deployment for verification.
async def main():
    try:
        agent = StableClipAgent()
        logger.info("에이전트 초기화 완료.")
    except Exception as e:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
        logging.critical(f"에이전트 초기화 실패: {e}. 스크립트를 종료합니다.")
        return

    if not await agent.mcp_client.connect():
        logger.critical("초기 MCP 연결 실패. 클리핑 처리 루프를 시작하지 않습니다.")
        return

    logger.info("클리핑 처리 루프 시작.")
    while True:
        try:
            files = list(agent.clip_dir.glob('*.md'))
            if not files:
                await asyncio.sleep(10)
                continue

            for file in files:
                await agent.process_single_clip(file)
            
            await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"메인 루프에서 예기치 않은 오류 발생: {e}")
            agent.error_notifier.notify_error(traceback.format_exc())
            await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("사용자에 의해 프로그램이 종료되었습니다.")
