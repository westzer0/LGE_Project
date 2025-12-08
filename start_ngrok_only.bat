@echo off
chcp 65001 >nul
echo ========================================
echo  NGROK 터널만 시작하기
echo ========================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM ngrok 경로 확인
set NGROK_PATH=%~dp0ngrok\ngrok.exe
if not exist "%NGROK_PATH%" (
    echo [오류] ngrok을 찾을 수 없습니다.
    echo.
    echo 먼저 설정을 실행하세요:
    echo   powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

REM 포트 8000 확인
echo [확인] 포트 8000에서 서버가 실행 중인지 확인...
netstat -ano | findstr ":8000" >nul
if %errorlevel% neq 0 (
    echo [경고] 포트 8000에서 서버를 찾을 수 없습니다.
    echo Django 서버를 먼저 실행해주세요:
    echo   python manage.py runserver 8000
    echo.
    choice /C YN /M "그래도 ngrok을 시작하시겠습니까"
    if errorlevel 2 exit /b 1
)

REM ngrok 터널 시작
echo.
echo [실행] NGROK 터널 시작 중 (포트 8000)...
echo.
echo Forwarding URL 확인 방법:
echo   - 브라우저에서 http://localhost:4040 열기
echo   - 또는 ngrok Tunnel 창에서 확인
echo.
start "ngrok Tunnel" cmd /k "cd /d %~dp0 && %NGROK_PATH% http 8000"
timeout /t 3 /nobreak >nul
start http://localhost:4040
echo.
echo [완료] ngrok이 실행되었습니다!
echo.
pause
