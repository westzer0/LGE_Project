# Git pre-commit hook 설정 스크립트 (PowerShell)

Write-Host "Git pre-commit hook 설정 중..." -ForegroundColor Cyan

if (-not (Test-Path ".git\hooks")) {
    Write-Host ".git\hooks 디렉토리가 없습니다. Git 저장소가 아닙니다." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "pre-commit_template.txt")) {
    Write-Host "pre-commit_template.txt 파일을 찾을 수 없습니다." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Git hook 파일 복사
Copy-Item "pre-commit_template.txt" -Destination ".git\hooks\pre-commit" -Force

if (Test-Path ".git\hooks\pre-commit") {
    Write-Host "✅ Git pre-commit hook이 설정되었습니다." -ForegroundColor Green
    Write-Host "이제 커밋 시 자동으로 프론트엔드 스타일이 검증됩니다." -ForegroundColor Green
} else {
    Write-Host "❌ Git hook 설정 실패" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
