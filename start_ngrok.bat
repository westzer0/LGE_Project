@echo off
chcp 65001 >nul
echo ========================================
echo  NGROK으로 로컬 서버를 인터넷에 공개하기
echo ========================================
echo.
echo [설명]
echo   - python manage.py runserver: 로컬에서만 접근 가능 (localhost:8000)
echo   - NGROK: 로컬 서버를 외부에서 접근 가능한 공개 URL로 변환
echo   - 둘 다 필요합니다! (서버 실행 + NGROK 터널링)
echo.
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
    echo 또는 수동으로:
    echo   1. https://ngrok.com/download 에서 다운로드
    echo   2. ngrok 폴더에 압축 해제
    echo   3. https://dashboard.ngrok.com/get-started/your-authtoken 에서 토큰 발급
    echo   4. ngrok\ngrok.exe config add-authtoken YOUR_TOKEN 실행
    echo.
    pause
    exit /b 1
)

REM 포트 확인 (8000 포트가 사용 중인지 체크)
netstat -ano | findstr ":8000" >nul
if %errorlevel% == 0 (
    echo [경고] 포트 8000이 이미 사용 중입니다.
    echo 기존 서버를 종료하거나 다른 포트를 사용하세요.
    echo.
    choice /C YN /M "계속 진행하시겠습니까"
    if errorlevel 2 exit /b 1
)

REM Django 서버 시작
echo [1/2] Django 서버 시작 중 (포트 8000)...
echo.
start "Django Server" cmd /k "cd /d %~dp0 && python manage.py runserver 8000"
timeout /t 5 /nobreak >nul

REM ngrok 터널 시작
echo [2/2] NGROK 터널 시작 중...
echo.
start "ngrok Tunnel" cmd /k "cd /d %~dp0 && %NGROK_PATH% http 8000"
timeout /t 8 /nobreak >nul

REM Forwarding URL 자동 가져오기 시도
echo.
echo [3/3] Forwarding URL 확인 중...
echo.
python get_ngrok_url.py 2>nul
if errorlevel 1 (
    echo.
    echo ========================================
    echo  수동으로 URL 확인하기
    echo ========================================
    echo.
    echo 방법 1: 웹 인터페이스 (가장 쉬움!)
    echo   - 브라우저를 열고 http://localhost:4040 입력
    echo   - 화면에서 Forwarding URL 확인
    echo.
    echo 방법 2: NGROK 창에서 확인
    echo   - "ngrok Tunnel" 창을 찾으세요
    echo   - "Forwarding" 줄을 찾으세요
    echo   - 예: Forwarding https://xxxx-xxx-xxx.ngrok-free.app
    echo.
    start http://localhost:4040
)

echo.
echo ========================================
echo  완료! 두 개의 창이 열렸습니다:
echo ========================================
echo   1. Django Server 창: 서버 로그 확인
echo   2. ngrok Tunnel 창: NGROK 상태 확인
echo.
echo  Forwarding URL 확인 방법:
echo   - 브라우저에서 http://localhost:4040 열기 (자동으로 열렸을 수 있음)
echo   - 또는 show_ngrok_url.bat 실행
echo.
pause

