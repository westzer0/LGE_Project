@echo off
cd /d "%~dp0"
echo Testing ngrok execution...
echo.
ngrok\ngrok.exe version > test_output.txt 2>&1
type test_output.txt
echo.
echo Exit code: %ERRORLEVEL%
echo.
ngrok\ngrok.exe config check > test_config.txt 2>&1
type test_config.txt
echo.
echo Exit code: %ERRORLEVEL%
echo.
