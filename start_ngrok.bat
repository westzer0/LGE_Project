@echo off
echo ========================================
echo  로컬 서버를 인터넷에 공개하기
echo ========================================
echo.

REM Django 서버 시작
echo [1/2] Django 서버 시작 중...
start "Django Server" cmd /k "python manage.py runserver 8000"
timeout /t 3 /nobreak >nul

REM ngrok 터널 시작
echo [2/2] ngrok 터널 시작 중...
echo.
echo ========================================
echo  ngrok 창에서 Forwarding URL을 확인하세요!
echo  예: https://xxxx-xxx-xxx.ngrok-free.app
echo ========================================
echo.
start "ngrok Tunnel" cmd /k "ngrok.exe http 8000"

echo.
echo 완료! 두 개의 창이 열렸습니다:
echo - Django Server: 서버 로그 확인
echo - ngrok Tunnel: 공개 URL 확인
echo.
pause

