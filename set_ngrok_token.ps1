# ngrok 토큰 설정 스크립트
$projectRoot = $PSScriptRoot
$ngrokExe = Join-Path $projectRoot "ngrok\ngrok.exe"

# 설정 디렉토리 생성
$ngrokConfigDir = "$env:LOCALAPPDATA\ngrok"
if (-not (Test-Path $ngrokConfigDir)) {
    New-Item -ItemType Directory -Path $ngrokConfigDir -Force | Out-Null
}

Write-Host ""
Write-Host "ngrok 인증 토큰 설정" -ForegroundColor Cyan
Write-Host "토큰 발급: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Yellow
Write-Host ""
$token = Read-Host "인증 토큰을 입력하세요"

if ($token -and $token.Trim() -ne "") {
    & $ngrokExe config add-authtoken $token.Trim()
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] 토큰 설정 완료!" -ForegroundColor Green
        & $ngrokExe config check
    } else {
        Write-Host "[ERROR] 토큰 설정 실패" -ForegroundColor Red
    }
} else {
    Write-Host "토큰이 입력되지 않았습니다." -ForegroundColor Yellow
}
