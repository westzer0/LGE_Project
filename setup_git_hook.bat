@echo off
echo Git pre-commit hook 설정 중...

if not exist ".git\hooks" (
    echo .git\hooks 디렉토리가 없습니다. Git 저장소가 아닙니다.
    pause
    exit /b 1
)

copy /Y pre-commit_template.txt .git\hooks\pre-commit >nul
if exist .git\hooks\pre-commit (
    echo ✅ Git pre-commit hook이 설정되었습니다.
    echo 이제 커밋 시 자동으로 프론트엔드 스타일이 검증됩니다.
) else (
    echo ❌ Git hook 설정 실패
)

pause
