@echo off
chcp 65001 >nul
echo 백엔드 로직 시각화 리포트 생성 (500개 테스트)
echo.
echo 500개 테스트 시나리오로 리포트를 생성합니다...
echo 예상 소요 시간: 약 5-10분
echo.

python generate_visual_report.py --tests 500

echo.
echo ========================================
echo 리포트 생성 완료!
echo ========================================
echo.
echo HTML 파일을 브라우저에서 열어 확인하세요.
echo 파일명: backend_verification_report_YYYYMMDD_HHMMSS.html
echo.
pause

