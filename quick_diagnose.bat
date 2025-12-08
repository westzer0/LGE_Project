@echo off
cd /d "%~dp0"
echo ========================================
echo  ngrok 빠른 진단
echo ========================================
echo.
echo [1] ngrok.exe 확인...
if exist "ngrok\ngrok.exe" (
    echo   OK - ngrok.exe 발견
) else (
    echo   ERROR - ngrok.exe 없음
    goto :end
)

echo.
echo [2] ngrok 버전 확인...
ngrok\ngrok.exe version
if %ERRORLEVEL% NEQ 0 (
    echo   ERROR - ngrok 실행 실패 (코드: %ERRORLEVEL%)
) else (
    echo   OK - ngrok 실행 성공
)

echo.
echo [3] 인증 토큰 확인...
ngrok\ngrok.exe config check
if %ERRORLEVEL% NEQ 0 (
    echo   ERROR - 인증 토큰 미설정 (코드: %ERRORLEVEL%)
    echo.
    echo   이것이 문제입니다!
    echo   해결: ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
) else (
    echo   OK - 인증 토큰 설정됨
)

:end
echo.
echo ========================================
pause
