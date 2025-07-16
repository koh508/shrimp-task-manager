@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: MCP 서버 주소 설정
set "MCP_SERVER=https://shrimp-mcp-production.up.railway.app"

:: 에이전트 이름 설정
set "AGENT_NAME=HeroicAge"

:: 에이전트 엔드포인트 (로컬 테스트용)
set "AGENT_ENDPOINT=http://localhost:9000"

:: 로그 디렉토리 생성
if not exist "logs" mkdir logs

:: 에이전트 실행
echo [%date% %time%] Starting HeroicAge Agent with Cloud MCP...
set PYTHONIOENCODING=utf-8
python main.py

:: 에러 발생 시 일시 정지
if errorlevel 1 pause
