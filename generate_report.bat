@echo off
chcp 65001 >nul
echo 백엔드 로직 시각화 리포트 생성
echo.

python generate_visual_report.py --tests 100

echo.
echo 리포트가 생성되었습니다!
echo HTML 파일을 브라우저에서 열어 확인하세요.
echo.
pause

