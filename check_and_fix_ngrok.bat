@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  ngrok 문제 확인 및 해결
echo ========================================
echo.

REM ngrok.exe 확인
if not exist "ngrok\ngrok.exe" (
    echo [ERROR] ngrok.exe를 찾을 수 없습니다.
    echo.
    echo ngrok을 다운로드합니다...
    powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1
    pause
    exit /b 1
)

echo [OK] ngrok.exe 발견
echo.

REM 인증 토큰 확인
echo 인증 토큰 확인 중...
ngrok\ngrok.exe config check >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] 인증 토큰이 설정되지 않았습니다!
    echo.
    echo 이것이 ngrok이 작동하지 않는 가장 흔한 원인입니다.
    echo.
    echo 해결 방법:
    echo 1. https://dashboard.ngrok.com/get-started/your-authtoken 접속
    echo 2. 무료 계정으로 가입 (또는 로그인)
    echo 3. 인증 토큰 복사
    echo 4. 아래에 토큰을 입력하세요
    echo.
    set /p TOKEN="인증 토큰을 입력하세요: "
    if not "!TOKEN!"=="" (
        echo.
        echo 토큰 설정 중...
        ngrok\ngrok.exe config add-authtoken !TOKEN!
        if !ERRORLEVEL! EQU 0 (
            echo [OK] 인증 토큰 설정 완료!
            echo.
            echo 이제 ngrok을 사용할 수 있습니다.
        ) else (
            echo [ERROR] 인증 토큰 설정 실패
            echo 토큰이 올바른지 확인하세요.
        )
    ) else (
        echo 토큰이 입력되지 않았습니다.
    )
) else (
    echo [OK] 인증 토큰이 설정되어 있습니다.
)

echo.
echo ========================================
echo  테스트: ngrok 실행
echo ========================================
echo.
echo ngrok을 5초간 실행하여 테스트합니다...
echo (Django 서버가 실행 중이 아니어도 테스트 가능)
echo.

start /B ngrok\ngrok.exe http 8000 > ngrok_test_output.txt 2>&1
timeout /t 5 /nobreak >nul
taskkill /F /IM ngrok.exe >nul 2>&1

if exist ngrok_test_output.txt (
    echo ngrok 실행 결과:
    type ngrok_test_output.txt
    echo.
    
    REM 에러 메시지 확인
    findstr /i "error" ngrok_test_output.txt >nul
    if !ERRORLEVEL! EQU 0 (
        echo [WARNING] 에러 메시지가 발견되었습니다.
        echo 위의 에러 메시지를 확인하세요.
    ) else (
        findstr /i "authtoken\|authentication\|token" ngrok_test_output.txt >nul
        if !ERRORLEVEL! EQU 0 (
            echo [ERROR] 인증 토큰 관련 오류가 있습니다.
            echo 인증 토큰을 다시 설정하세요.
        ) else (
            echo [OK] ngrok이 정상적으로 실행되었습니다!
        )
    )
    
    del ngrok_test_output.txt
) else (
    echo [WARNING] 출력 파일을 생성할 수 없습니다.
)

echo.
echo ========================================
echo  완료
echo ========================================
echo.
echo 다음 단계:
echo   .\start_ngrok.bat 또는 .\start_server_fixed.bat 실행
echo.
pause
