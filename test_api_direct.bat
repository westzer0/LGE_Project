@echo off
chcp 65001 >nul
echo API 엔드포인트 직접 테스트
echo.
echo 참고: Django 서버가 실행 중이어야 합니다.
echo   python manage.py runserver
echo.
pause

powershell -ExecutionPolicy Bypass -File test_api_direct.ps1

pause

