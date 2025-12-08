@echo off
chcp 65001 >nul
echo ========================================
echo  서버 상태 확인
echo ========================================
echo.

echo [1] Django 서버 확인 (포트 8000)...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo   [OK] Django 서버가 실행 중입니다
) else (
    echo   [X] Django 서버가 실행되지 않았습니다
    echo   → 새 터미널에서 실행: python manage.py runserver 8000
)
echo.

echo [2] ngrok 확인...
tasklist | findstr ngrok.exe >nul
if %errorlevel% == 0 (
    echo   [OK] ngrok이 실행 중입니다
    echo   → ngrok 창에서 Forwarding URL을 확인하세요
    echo   → 예: https://xxxx-xxx-xxx.ngrok-free.app
) else (
    echo   [X] ngrok이 실행되지 않았습니다
    echo   → 실행: ngrok\ngrok.exe http 8000
)
echo.

echo ========================================
echo  다음 단계:
echo  1. Django 서버 실행 확인
echo  2. ngrok 창에서 Forwarding URL 복사
echo  3. 카카오 개발자 콘솔에 URL 등록
echo ========================================
pause

