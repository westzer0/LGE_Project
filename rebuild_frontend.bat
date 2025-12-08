@echo off
echo ========================================
echo React 앱 빌드 시작
echo ========================================
echo.

cd /d "%~dp0"

echo 1. 기존 빌드 파일 삭제 중...
if exist "staticfiles\react" (
    rmdir /s /q "staticfiles\react"
    echo    기존 빌드 파일 삭제 완료
) else (
    echo    빌드 파일 없음
)

echo.
echo 2. React 앱 빌드 중...
call npm run build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 빌드 성공!
    echo ========================================
    echo.
    echo 다음 단계:
    echo 1. Django 서버 재시작
    echo 2. 브라우저에서 http://127.0.0.1:8000/ 확인
    echo 3. 캐시 문제 시 Ctrl+Shift+R로 하드 리프레시
    echo.
) else (
    echo.
    echo ========================================
    echo 빌드 실패!
    echo ========================================
    echo.
    pause
)
