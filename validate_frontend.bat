@echo off
chcp 65001 >nul
echo 🔍 프론트엔드 스타일 검증 시작...
echo.

python validate_frontend_style.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 검증 실패! FRONTEND_STYLE_GUIDE.md를 참고하여 수정하세요.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ 모든 검증 통과!
    pause
    exit /b 0
)
