@echo off
chcp 65001 >nul
echo ============================================
echo Django 서버 시작 (DB 연결 없이)
echo ============================================
echo.

REM DB 연결 비활성화
set DISABLE_DB=true
set USE_ORACLE=false

echo [설정] DB 연결이 비활성화되었습니다.
echo         - DISABLE_DB=true
echo         - USE_ORACLE=false
echo.
echo [주의] DB를 사용하는 API는 에러를 반환할 수 있습니다.
echo         정적 파일 서빙, 템플릿 렌더링 등은 정상 작동합니다.
echo.

REM Django 서버 시작
python manage.py runserver 8000

pause
