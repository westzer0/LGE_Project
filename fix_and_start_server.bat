@echo off
chcp 65001 >nul
echo ========================================
echo  서버 문제 해결 및 시작
echo ========================================
echo.

REM 1. 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    echo [1/4] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else (
    echo [경고] 가상환경이 없습니다.
)

REM 2. SQLite로 전환 (Oracle 문제 회피)
echo [2/4] 데이터베이스 설정 확인...
if not exist ".env" (
    echo .env 파일이 없습니다. SQLite를 사용합니다.
) else (
    echo .env 파일 확인 중...
)

REM 3. 마이그레이션 실행
echo [3/4] 데이터베이스 마이그레이션...
python manage.py migrate --run-syncdb
if errorlevel 1 (
    echo [경고] 마이그레이션에 문제가 있습니다.
    echo SQLite로 전환하여 다시 시도합니다...
    python manage.py migrate
)

REM 4. 서버 시작
echo [4/4] Django 서버 시작...
echo.
echo ========================================
echo  서버가 http://127.0.0.1:8000 에서 실행됩니다
echo  중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.
python manage.py runserver 8000
