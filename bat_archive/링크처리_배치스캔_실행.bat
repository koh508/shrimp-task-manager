@echo off
chcp 65001 >nul
title 온유 링크 배치 스캔

echo [링크 배치 스캔] 기존 파일 링크 자동 삽입을 시작합니다.
echo 중단하려면 Ctrl+C 를 누르세요.
echo.

python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\link_batch_scan.py"

echo.
pause
