@echo off
echo ========================================
echo Django 서버 시작
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 가상환경 활성화 중...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo [오류] 가상환경 활성화 실패!
    echo 가상환경이 올바르게 설치되어 있는지 확인하세요.
    pause
    exit /b 1
)

echo [2/3] Django 설치 확인 중...
python -m pip show django >nul 2>&1

if errorlevel 1 (
    echo.
    echo [오류] Django가 설치되지 않았습니다!
    echo 다음 명령어로 설치하세요: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [3/3] 서버 시작 중...
echo.
echo ========================================
echo 서버가 시작되었습니다!
echo 브라우저에서 http://127.0.0.1:8000/ 접속
echo 종료하려면 CTRL+C를 누르세요
echo ========================================
echo.

python manage.py runserver

pause


