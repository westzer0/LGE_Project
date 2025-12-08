# ngrok 자동 설정 스크립트 (간단 버전)
param(
    [Parameter(Mandatory=$false)]
    [string]$Token
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ngrok Auto Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. ngrok 다운로드
Write-Host "[1/4] Downloading ngrok..." -ForegroundColor Yellow
$ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$downloadPath = "$env:TEMP\ngrok.zip"
$extractPath = "$PSScriptRoot\ngrok"

try {
    Invoke-WebRequest -Uri $ngrokUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "  [OK] Download complete" -ForegroundColor Green
    
    # 압축 해제
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
    Write-Host "  [OK] Extract complete" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Download failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual download: https://ngrok.com/download" -ForegroundColor Yellow
    exit 1
}

# 2. ngrok 경로 확인
$ngrokExe = Join-Path $extractPath "ngrok.exe"
if (-not (Test-Path $ngrokExe)) {
    Write-Host "  [ERROR] ngrok.exe not found" -ForegroundColor Red
    exit 1
}

Write-Host "[2/4] ngrok installed: $ngrokExe" -ForegroundColor Green
Write-Host ""

# 3. 인증 토큰 설정
Write-Host "[3/4] Setting up ngrok auth token..." -ForegroundColor Yellow

if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "  Please visit: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Cyan
    Write-Host ""
    $Token = Read-Host "Enter your ngrok auth token"
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "  [ERROR] Token is required" -ForegroundColor Red
    exit 1
}

# 토큰 설정
& $ngrokExe config add-authtoken $Token
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Auth token configured" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Failed to configure auth token" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Run start_server.bat" -ForegroundColor Cyan
Write-Host ""

