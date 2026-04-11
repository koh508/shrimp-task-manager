@echo off
chcp 65001 > nul
title Onew Main

REM -- Kill existing sub-processes to prevent zombies --
wmic process where "name='python.exe' and commandline like '%%link_batch_scan%%'" delete >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%onew_telegram_bot%%'" delete >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%telegram_collector%%'" delete >nul 2>&1
timeout /t 2 /nobreak > nul

REM -- Start sub-processes --
start /min "LinkBatchScan"     python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\link_batch_scan.py"
start /min "OnewTelegramBot"   python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\onew_telegram_bot.py"
start /min "TelegramCollector" python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\telegram_collector.py"
timeout /t 3 /nobreak > nul

REM -- Main agent auto-restart loop --
:RESTART_LOOP

if exist "C:\Users\User\Documents\Obsidian Vault\SYSTEM\stop.flag" (
    del "C:\Users\User\Documents\Obsidian Vault\SYSTEM\stop.flag"
    echo Onew stopped by flag.
    pause
    exit /b 0
)

echo.
echo [Onew] %date% %time% - Starting...
echo -----------------------------------

python "C:\Users\User\Documents\Obsidian Vault\SYSTEM\obsidian_agent.py"

if exist "C:\Users\User\Documents\Obsidian Vault\SYSTEM\stop.flag" (
    del "C:\Users\User\Documents\Obsidian Vault\SYSTEM\stop.flag"
    echo Onew stopped by flag.
    pause
    exit /b 0
)

echo.
echo [Onew] %date% %time% - Crashed. Restarting in 10s...
timeout /t 10 /nobreak > nul
goto RESTART_LOOP
