@echo off
chcp 65001 >nul
echo ========================================
echo  로컬 서버 시작 (인터넷 공개)
echo ========================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 필수 패키지 확인 (빠른 확인만)
echo [0/2] 필수 패키지 확인 중...
venv\Scripts\python.exe -c "import requests; import whitenoise; import corsheaders" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [경고] 일부 패키지가 없습니다. 설치 중... (잠시만 기다려주세요)
    venv\Scripts\python.exe -m pip install requests whitenoise django-cors-headers --quiet --disable-pip-version-check
) else (
    echo [OK] 필수 패키지 확인 완료
)

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

REM DB 연결 설정 확인
if "%DISABLE_DB%"=="" (
    echo [정보] DISABLE_DB 환경변수가 설정되지 않았습니다.
    echo       DB 연결을 시도합니다. DB가 잠겨있으면 에러가 발생할 수 있습니다.
    echo       DB 연결 없이 실행하려면: set DISABLE_DB=true
    echo.
)

REM Django 서버 시작
echo [1/2] Django 서버 시작 중...
start "Django Server" cmd /k "call venv\Scripts\activate.bat && venv\Scripts\python.exe manage.py runserver 8000"
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
echo ========================================
echo  서버 시작 완료!
echo ========================================
echo.
echo [중요] 두 개의 새 창이 열렸습니다:
echo.
echo   1. "Django Server" 창
echo      - Django 서버가 실행 중입니다
echo      - 서버 로그를 확인할 수 있습니다
echo      - "Starting development server at http://127.0.0.1:8000/" 메시지가 보이면 정상입니다
echo.
echo   2. "ngrok Tunnel" 창
echo      - ngrok 터널이 실행 중입니다
echo      - "Forwarding https://xxxx-xxx-xxx.ngrok-free.app -> http://localhost:8000" 메시지를 찾으세요
echo      - 이 URL을 복사해서 카카오 개발자 콘솔에 등록하세요
echo.
echo [서버 중지 방법]
echo   - 두 개의 창(Django Server, ngrok Tunnel)을 모두 닫으세요
echo   - 또는 이 창에서 Ctrl+C를 누르세요
echo.
echo [다음 단계]
echo   1. ngrok 창에서 Forwarding URL 확인
echo   2. https://developers.kakao.com 접속
echo   3. 앱 설정 > 플랫폼 > Web 플랫폼 등록
echo   4. 사이트 도메인에 ngrok URL 입력
echo.
echo ========================================
echo  이 창을 닫으려면 아무 키나 누르세요
echo ========================================
pause >nul

