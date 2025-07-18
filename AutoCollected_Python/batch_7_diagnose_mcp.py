import socket
import subprocess
import sys
import os
import platform
import logging
from typing import Tuple, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_diagnosis.log')
    ]
)
logger = logging.getLogger("MCP-Diagnosis")

def check_port(host: str, port: int) -> bool:
    """포트가 열려있는지 확인"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.error(f"포트 확인 중 오류 발생: {e}")
        return False

def check_firewall(port: int) -> bool:
    """Windows 방화벽에서 포트가 열려있는지 확인"""
    if platform.system() != 'Windows':
        logger.info("Windows가 아닌 시스템에서는 방화벽 확인을 건너뜁니다.")
        return True
    
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True, text=True, check=True
        )
        return str(port) in result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"방화벽 확인 중 오류: {e}")
        return False

def check_process_using_port(port: int) -> Optional[str]:
    """특정 포트를 사용 중인 프로세스 확인"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['netstat', '-ano', '|', 'findstr', f':{port}'],
                capture_output=True, text=True, shell=True
            )
            if result.returncode == 0 and str(port) in result.stdout:
                pid = result.stdout.strip().split()[-1]
                proc_info = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True, text=True, check=True
                )
                return proc_info.stdout
    except Exception as e:
        logger.error(f"프로세스 확인 중 오류: {e}")
    return None

def main():
    host = '127.0.0.1'
    port = 8080
    
    logger.info("="*50)
    logger.info("MCP 서버 진단 시작")
    logger.info(f"대상: {host}:{port}")
    logger.info("="*50)
    
    # 1. 포트 확인
    logger.info("\n1. 포트 상태 확인 중...")
    if check_port(host, port):
        logger.info(f"✅ {host}:{port} 포트가 열려 있습니다.")
    else:
        logger.error(f"❌ {host}:{port} 포트에 연결할 수 없습니다.")
        logger.info("\n1.1 포트를 사용 중인 프로세스 확인 중...")
        proc_info = check_process_using_port(port)
        if proc_info:
            logger.info(f"포트 {port}를 사용 중인 프로세스:\n{proc_info}")
        else:
            logger.info("해당 포트를 사용 중인 프로세스를 찾을 수 없습니다.")
    
    # 2. 방화벽 확인
    logger.info("\n2. 방화벽 확인 중...")
    if check_firewall(port):
        logger.info(f"✅ 방화벽에서 {port} 포트가 허용되어 있습니다.")
    else:
        logger.warning(f"⚠️ 방화벽에서 {port} 포트가 차단되었을 수 있습니다.")
    
    # 3. MCP 서버 프로세스 확인
    logger.info("\n3. MCP 서버 프로세스 확인 중...")
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
            capture_output=True, text=True, check=True
        )
        logger.info("실행 중인 Python 프로세스:")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"프로세스 확인 중 오류: {e}")
    
    logger.info("\n진단이 완료되었습니다. 'mcp_diagnosis.log' 파일을 확인하세요.")

if __name__ == "__main__":
    main()
