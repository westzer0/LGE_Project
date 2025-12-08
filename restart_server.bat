@echo off
chcp 65001 >nul
echo ========================================
echo  Django 서버 재시작
echo ========================================
echo.

echo [1/2] 기존 Django 서버 종료 중...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Django Server*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/2] Django 서버 시작 중...
start "Django Server" cmd /k "python manage.py runserver 8000"

echo.
echo 완료! 서버가 재시작되었습니다.
echo 이제 ngrok URL로 접속해보세요:
echo   https://braeden-unaromatic-zola.ngrok-free.dev
echo.
pause

