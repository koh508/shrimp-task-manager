@echo off
chcp 65001 >nul
title 클리핑 형식 소급 수정

echo [클리핑 형식 수정] YAML 필드 추가 후 온유 재임베딩이 자동 예약됩니다.
echo.

python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\link_clipping_fix.py"

echo.
pause
