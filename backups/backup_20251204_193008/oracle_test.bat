@echo off
REM Oracle DB 연결 테스트 - 배치 파일
REM 사용법: oracle_test.bat

echo ============================================================
echo Oracle DB 연결 테스트
echo ============================================================
echo.

python -c "from api.db.oracle_client import fetch_one; result = fetch_one('SELECT USER, SYSDATE FROM DUAL'); print(f'✅ 연결 성공!'); print(f'   사용자: {result[0]}'); print(f'   서버 시간: {result[1]}')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [테이블 목록 조회 중...]
    python -c "from api.db.oracle_client import fetch_all_dict; tables = fetch_all_dict('SELECT table_name FROM user_tables ORDER BY table_name'); print(f'✅ 발견된 테이블: {len(tables)}개'); [print(f'  - {t[\"TABLE_NAME\"]}') for t in tables]"
) else (
    echo.
    echo ❌ 연결 실패!
)

echo.
echo ============================================================
pause

