@echo off
chcp 65001 > nul
title 온유 텔레그램 봇

for /f "usebackq tokens=*" %%A in (`powershell -Command "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY','User')"`) do set GEMINI_API_KEY=%%A
for /f "usebackq tokens=*" %%A in (`powershell -Command "[System.Environment]::GetEnvironmentVariable('TELEGRAM_BOT_TOKEN','User')"`) do set TELEGRAM_BOT_TOKEN=%%A

if "%GEMINI_API_KEY%"=="" (
    echo [오류] GEMINI_API_KEY 없음
    pause & exit /b 1
)
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo [오류] TELEGRAM_BOT_TOKEN 없음
    pause & exit /b 1
)

echo 온유 텔레그램 봇 시작 중...
python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\onew_telegram_bot.py"
pause
