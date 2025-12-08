@echo off
chcp 65001 >nul
echo ========================================
echo  Django 서버 시작 (간단 버전)
echo ========================================
echo.

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo [1/3] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else (
    echo [경고] 가상환경이 없습니다. 시스템 Python을 사용합니다.
)

REM 데이터베이스 마이그레이션 (선택사항)
echo [2/3] 데이터베이스 마이그레이션 확인...
python manage.py migrate --run-syncdb 2>nul
if errorlevel 1 (
    echo [경고] 마이그레이션 실패 (계속 진행)
)

REM 서버 시작
echo [3/3] Django 서버 시작...
echo.
echo 서버가 http://127.0.0.1:8000 에서 실행됩니다.
echo 중지하려면 Ctrl+C를 누르세요.
echo.
python manage.py runserver 8000

pause
