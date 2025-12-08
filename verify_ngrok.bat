@echo off
cd /d "%~dp0"
echo ngrok 설정 확인...
echo.
.\ngrok\ngrok.exe config check
echo.
echo Exit code: %ERRORLEVEL%
if %ERRORLEVEL% EQU 0 (
    echo [OK] ngrok 설정 완료!
) else (
    echo [ERROR] 설정에 문제가 있습니다.
)
pause
