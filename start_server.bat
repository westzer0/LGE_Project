@echo off
chcp 65001 >nul
echo ========================================
echo  로컬 서버 시작 (인터넷 공개)
echo ========================================
echo.

REM ngrok 경로 확인
set NGROK_PATH=%~dp0ngrok\ngrok.exe
if not exist "%NGROK_PATH%" (
    echo [오류] ngrok을 찾을 수 없습니다.
    echo.
    echo 먼저 설정을 실행하세요:
    echo   powershell -ExecutionPolicy Bypass -File setup_ngrok.ps1
    echo.
    pause
    exit /b 1
)

REM Django 서버 시작
echo [1/2] Django 서버 시작 중...
start "Django Server" cmd /k "python manage.py runserver 8000"
timeout /t 3 /nobreak >nul

REM ngrok 터널 시작
echo [2/2] ngrok 터널 시작 중...
echo.
echo ========================================
echo  중요: ngrok 창에서 Forwarding URL을 확인하세요!
echo  예: https://xxxx-xxx-xxx.ngrok-free.app
echo ========================================
echo.
echo 이 URL을 카카오 개발자 콘솔에 등록하세요:
echo   https://developers.kakao.com
echo.
start "ngrok Tunnel" cmd /k "%NGROK_PATH% http 8000"

echo.
echo 완료! 두 개의 창이 열렸습니다:
echo   - Django Server: 서버 로그 확인
echo   - ngrok Tunnel: 공개 URL 확인 (복사하세요!)
echo.
echo 서버를 중지하려면 두 창을 모두 닫으세요.
echo.
pause

