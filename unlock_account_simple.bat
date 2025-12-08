@echo off
chcp 65001 >nul
echo ============================================================
echo Oracle 계정 잠금 해제 스크립트 실행
echo ============================================================
echo.
python -u unlock_oracle_account.py
echo.
pause
