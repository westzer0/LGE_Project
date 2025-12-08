@echo off
chcp 65001 >nul
echo ============================================================
echo Oracle 계정 잠금 해제 요청 메시지 생성
echo ============================================================
echo.
powershell -ExecutionPolicy Bypass -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; & '%~dp0send_unlock_request.ps1'"
echo.
pause
