# ngrok 자동 설정 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ngrok 자동 설정 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. ngrok 다운로드
Write-Host "[1/4] ngrok 다운로드 중..." -ForegroundColor Yellow
$ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$downloadPath = "$env:TEMP\ngrok.zip"
$extractPath = "$PSScriptRoot\ngrok"

try {
    Invoke-WebRequest -Uri $ngrokUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "  ✓ 다운로드 완료" -ForegroundColor Green
    
    # 압축 해제
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "  ✓ 압축 해제 완료" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 다운로드 실패: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "수동 다운로드: https://ngrok.com/download" -ForegroundColor Yellow
    exit 1
}

# 2. ngrok 경로 확인
$ngrokExe = Join-Path $extractPath "ngrok.exe"
if (-not (Test-Path $ngrokExe)) {
    Write-Host "  ✗ ngrok.exe를 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

Write-Host "[2/4] ngrok 설치 완료: $ngrokExe" -ForegroundColor Green
Write-Host ""

# 3. 인증 토큰 입력
Write-Host "[3/4] ngrok 인증 토큰 설정" -ForegroundColor Yellow

# 명령줄 인자로 토큰 전달 가능
if ($args.Count -gt 0) {
    $authToken = $args[0]
    Write-Host "  → 토큰을 인자로 받았습니다" -ForegroundColor Green
} else {
    Write-Host "  → https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Cyan
    Write-Host "  → 위 링크에서 토큰을 복사하세요" -ForegroundColor Cyan
    Write-Host ""
    $authToken = Read-Host "ngrok 인증 토큰을 입력하세요"
}

if ([string]::IsNullOrWhiteSpace($authToken)) {
    Write-Host "  ✗ 토큰이 입력되지 않았습니다" -ForegroundColor Red
    exit 1
}

# 토큰 설정
& $ngrokExe config add-authtoken $authToken
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 인증 토큰 설정 완료" -ForegroundColor Green
} else {
    Write-Host "  ✗ 인증 토큰 설정 실패" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] 설정 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "다음 명령어로 서버를 시작하세요:" -ForegroundColor Cyan
Write-Host "  start_server.bat" -ForegroundColor Yellow
Write-Host ""

