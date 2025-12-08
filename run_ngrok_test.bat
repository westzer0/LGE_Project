@echo off
cd /d "%~dp0"
echo Testing ngrok...
echo.

echo [1] Checking ngrok.exe...
if exist "ngrok\ngrok.exe" (
    echo   OK: ngrok.exe found
) else (
    echo   ERROR: ngrok.exe not found
    pause
    exit /b 1
)

echo.
echo [2] Running ngrok version...
ngrok\ngrok.exe version > test_output.txt 2>&1
type test_output.txt
echo Exit code: %ERRORLEVEL%
echo.

echo [3] Running ngrok config check...
ngrok\ngrok.exe config check > test_output.txt 2>&1
type test_output.txt
echo Exit code: %ERRORLEVEL%
echo.

echo [4] Testing ngrok http (will run for 3 seconds)...
start /B ngrok\ngrok.exe http 8000 > test_ngrok_run.txt 2>&1
timeout /t 3 /nobreak >nul
taskkill /F /IM ngrok.exe >nul 2>&1
echo.
echo Output:
type test_ngrok_run.txt
echo.

del test_output.txt test_ngrok_run.txt 2>nul
pause
