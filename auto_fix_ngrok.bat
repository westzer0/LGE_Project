@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  ngrok 자동 문제 해결
echo ========================================
echo.

REM 1. ngrok.exe 확인
if not exist "ngrok\ngrok.exe" (
    echo [오류] ngrok.exe를 찾을 수 없습니다.
    echo.
    echo ngrok을 다운로드합니다...
    powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1
    if %ERRORLEVEL% NEQ 0 (
        echo [오류] ngrok 다운로드 실패
        pause
        exit /b 1
    )
)

REM 2. 인증 토큰 확인
echo [2/4] 인증 토큰 확인 중...
ngrok\ngrok.exe config check >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [경고] 인증 토큰이 설정되지 않았습니다
    echo.
    echo   인증 토큰을 설정해야 합니다:
    echo   1. https://dashboard.ngrok.com/get-started/your-authtoken 접속
    echo   2. 토큰을 복사한 후 아래 명령 실행:
    echo      ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
    echo.
    set /p TOKEN="토큰을 입력하세요 (Enter로 건너뛰기): "
    if not "!TOKEN!"=="" (
        ngrok\ngrok.exe config add-authtoken !TOKEN!
        if %ERRORLEVEL% EQU 0 (
            echo   [OK] 인증 토큰 설정 완료
        ) else (
            echo   [오류] 인증 토큰 설정 실패
        )
    )
) else (
    echo   [OK] 인증 토큰이 설정되어 있습니다
)

REM 3. 포트 8000 확인
echo.
echo [3/4] 포트 8000 확인 중...
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo   [경고] 포트 8000이 사용 중입니다
    echo   기존 프로세스를 확인하세요:
    netstat -ano | findstr :8000
) else (
    echo   [OK] 포트 8000이 사용 가능합니다
)

REM 4. 실행 중인 ngrok 프로세스 확인
echo.
echo [4/4] 실행 중인 ngrok 프로세스 확인 중...
tasklist | findstr ngrok.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo   [경고] 실행 중인 ngrok 프로세스 발견:
    tasklist | findstr ngrok.exe
    echo.
    set /p KILL="기존 프로세스를 종료하시겠습니까? (Y/N): "
    if /i "!KILL!"=="Y" (
        taskkill /F /IM ngrok.exe
        echo   [OK] ngrok 프로세스 종료됨
    )
) else (
    echo   [OK] 실행 중인 ngrok 프로세스가 없습니다
)

echo.
echo ========================================
echo  진단 완료
echo ========================================
echo.
echo 이제 서버를 시작할 수 있습니다:
echo   .\start_ngrok.bat
echo   또는: .\start_server_fixed.bat
echo.
pause
