@echo off
cd /d "%~dp0"
echo NGROK 테스트 실행...
echo.
ngrok\ngrok.exe http 8000
pause
