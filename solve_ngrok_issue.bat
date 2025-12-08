@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  ngrok 문제 종합 해결
echo ========================================
echo.

REM 1. ngrok.exe 확인
echo [1/5] ngrok.exe 확인...
if exist "ngrok\ngrok.exe" (
    echo   [OK] ngrok.exe 발견
) else (
    echo   [ERROR] ngrok.exe를 찾을 수 없습니다
    echo   다운로드를 시작합니다...
    powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1
    if !ERRORLEVEL! NEQ 0 (
        echo   [ERROR] 다운로드 실패
        pause
        exit /b 1
    )
)

REM 2. ngrok 버전 확인
echo.
echo [2/5] ngrok 버전 확인...
ngrok\ngrok.exe version 2>nul
if !ERRORLEVEL! EQU 0 (
    echo   [OK] ngrok이 정상적으로 실행됩니다
) else (
    echo   [WARNING] ngrok 실행에 문제가 있을 수 있습니다
)

REM 3. 인증 토큰 확인
echo.
echo [3/5] 인증 토큰 확인...
ngrok\ngrok.exe config check >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   [OK] 인증 토큰이 설정되어 있습니다
) else (
    echo   [ERROR] 인증 토큰이 설정되지 않았습니다
    echo.
    echo   이것이 가장 가능성 높은 문제입니다!
    echo.
    echo   해결 방법:
    echo   1. https://dashboard.ngrok.com/get-started/your-authtoken 접속
    echo   2. 무료 계정으로 가입 (또는 로그인)
    echo   3. 인증 토큰 복사
    echo   4. 아래 명령 실행:
    echo      ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
    echo.
    set /p TOKEN="지금 토큰을 입력하시겠습니까? (토큰 입력 또는 Enter로 건너뛰기): "
    if not "!TOKEN!"=="" (
        echo   토큰 설정 중...
        ngrok\ngrok.exe config add-authtoken !TOKEN!
        if !ERRORLEVEL! EQU 0 (
            echo   [OK] 인증 토큰 설정 완료!
        ) else (
            echo   [ERROR] 인증 토큰 설정 실패
        )
    )
)

REM 4. 포트 8000 확인
echo.
echo [4/5] 포트 8000 확인...
netstat -ano | findstr ":8000" >nul
if !ERRORLEVEL! EQU 0 (
    echo   [WARNING] 포트 8000이 사용 중입니다
    echo   사용 중인 프로세스:
    netstat -ano | findstr ":8000"
) else (
    echo   [OK] 포트 8000이 사용 가능합니다
)

REM 5. 실행 중인 ngrok 프로세스 확인
echo.
echo [5/5] 실행 중인 ngrok 프로세스 확인...
tasklist | findstr "ngrok.exe" >nul
if !ERRORLEVEL! EQU 0 (
    echo   [WARNING] 실행 중인 ngrok 프로세스 발견:
    tasklist | findstr "ngrok.exe"
    echo.
    set /p KILL="기존 프로세스를 종료하시겠습니까? (Y/N): "
    if /i "!KILL!"=="Y" (
        taskkill /F /IM ngrok.exe >nul 2>&1
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
echo 주요 발견 사항:
echo   - 인증 토큰이 설정되지 않은 경우가 가장 흔한 문제입니다
echo   - 다른 로컬에서는 작동하는데 여기서만 안 되는 경우,
echo     대부분 인증 토큰이 사용자별로 설정되어야 하기 때문입니다
echo.
echo 다음 단계:
echo   1. 인증 토큰이 설정되지 않았다면 위의 방법으로 설정
echo   2. 서버 시작: .\start_ngrok.bat
echo      또는: .\start_server_fixed.bat
echo.
pause
