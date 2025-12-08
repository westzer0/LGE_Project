# ngrok 문제 자동 해결 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ngrok 문제 자동 해결" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$ngrokExe = Join-Path $projectRoot "ngrok\ngrok.exe"

# 1. ngrok.exe 확인
if (-not (Test-Path $ngrokExe)) {
    Write-Host "[ERROR] ngrok.exe를 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] ngrok.exe 발견" -ForegroundColor Green
Write-Host ""

# 2. ngrok 설정 디렉토리 생성
$ngrokConfigDir = "$env:LOCALAPPDATA\ngrok"
if (-not (Test-Path $ngrokConfigDir)) {
    Write-Host "[1/3] ngrok 설정 디렉토리 생성 중..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ngrokConfigDir -Force | Out-Null
    Write-Host "  [OK] 디렉토리 생성 완료: $ngrokConfigDir" -ForegroundColor Green
} else {
    Write-Host "[1/3] ngrok 설정 디렉토리 확인 완료" -ForegroundColor Green
}

# 3. 인증 토큰 확인
Write-Host ""
Write-Host "[2/3] 인증 토큰 확인 중..." -ForegroundColor Yellow
$configCheck = & $ngrokExe config check 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] 인증 토큰이 설정되지 않았습니다" -ForegroundColor Red
    Write-Host ""
    Write-Host "  이것이 ngrok이 작동하지 않는 원인입니다!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  해결 방법:" -ForegroundColor Cyan
    Write-Host "  1. https://dashboard.ngrok.com/get-started/your-authtoken 접속" -ForegroundColor White
    Write-Host "  2. 무료 계정으로 가입 (또는 로그인)" -ForegroundColor White
    Write-Host "  3. 인증 토큰 복사" -ForegroundColor White
    Write-Host ""
    
    $token = Read-Host "  인증 토큰을 입력하세요 (Enter로 건너뛰기)"
    if ($token -and $token.Trim() -ne "") {
        Write-Host ""
        Write-Host "  토큰 설정 중..." -ForegroundColor Yellow
        & $ngrokExe config add-authtoken $token.Trim()
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] 인증 토큰 설정 완료!" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] 인증 토큰 설정 실패" -ForegroundColor Red
            Write-Host "  토큰이 올바른지 확인하세요." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  토큰이 입력되지 않았습니다." -ForegroundColor Yellow
        Write-Host "  나중에 다음 명령으로 설정하세요:" -ForegroundColor Cyan
        Write-Host "    .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN" -ForegroundColor White
    }
} else {
    Write-Host "  [OK] 인증 토큰이 설정되어 있습니다" -ForegroundColor Green
}

# 4. 최종 확인
Write-Host ""
Write-Host "[3/3] 최종 확인 중..." -ForegroundColor Yellow
$finalCheck = & $ngrokExe config check 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] ngrok 설정이 완료되었습니다!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  해결 완료!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "이제 ngrok을 사용할 수 있습니다:" -ForegroundColor Yellow
    Write-Host "  .\start_ngrok.bat" -ForegroundColor Cyan
    Write-Host "  또는: .\start_server_fixed.bat" -ForegroundColor Cyan
} else {
    Write-Host "  [WARNING] 아직 인증 토큰이 설정되지 않았습니다" -ForegroundColor Yellow
    Write-Host "  위의 방법으로 인증 토큰을 설정하세요." -ForegroundColor Yellow
}

Write-Host ""
