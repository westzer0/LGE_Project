@echo off
chcp 65001 >nul
cd /d "%~dp0"
python oracle_quick.py
echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul

