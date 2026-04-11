@echo off
chcp 65001 > nul
pip install google-genai watchdog --quiet

echo.
echo  [1/2] 온유 자동요약 모드 백그라운드 실행 중...
start "온유 자동요약" python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\onew_watcher.py"

timeout /t 2 /nobreak > nul

echo  [2/2] 온유 대화 모드 시작...
echo.
python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\obsidian_agent.py"

pause
