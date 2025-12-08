# ngrok 진단 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ngrok 진단 도구" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$ngrokPath = Join-Path $projectRoot "ngrok\ngrok.exe"

# 1. ngrok.exe 존재 확인
Write-Host "[1/6] ngrok.exe 파일 확인..." -ForegroundColor Yellow
if (Test-Path $ngrokPath) {
    Write-Host "  [OK] ngrok.exe 발견: $ngrokPath" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] ngrok.exe를 찾을 수 없습니다: $ngrokPath" -ForegroundColor Red
    Write-Host "  해결방법: powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1" -ForegroundColor Yellow
    exit 1
}

# 2. ngrok 버전 확인
Write-Host "[2/6] ngrok 버전 확인..." -ForegroundColor Yellow
try {
    $version = & $ngrokPath version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] ngrok 버전: $version" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] ngrok 버전 확인 실패" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] ngrok 실행 실패: $_" -ForegroundColor Red
}

# 3. ngrok 인증 토큰 확인
Write-Host "[3/6] ngrok 인증 토큰 확인..." -ForegroundColor Yellow
try {
    $configCheck = & $ngrokPath config check 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] 인증 토큰이 설정되어 있습니다" -ForegroundColor Green
        Write-Host "  $configCheck" -ForegroundColor Gray
    } else {
        Write-Host "  [ERROR] 인증 토큰이 설정되지 않았습니다" -ForegroundColor Red
        Write-Host "  해결방법:" -ForegroundColor Yellow
        Write-Host "    1. https://dashboard.ngrok.com/get-started/your-authtoken 접속" -ForegroundColor Cyan
        Write-Host "    2. 토큰 발급 후 다음 명령 실행:" -ForegroundColor Cyan
        Write-Host "       .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN" -ForegroundColor Cyan
        Write-Host "    또는:" -ForegroundColor Cyan
        Write-Host "       powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_TOKEN" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [ERROR] 인증 토큰 확인 실패: $_" -ForegroundColor Red
}

# 4. 포트 8000 사용 확인
Write-Host "[4/6] 포트 8000 사용 확인..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  [WARNING] 포트 8000이 이미 사용 중입니다" -ForegroundColor Yellow
    Write-Host "  프로세스 ID: $($port8000.OwningProcess)" -ForegroundColor Gray
    $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "  프로세스 이름: $($process.ProcessName)" -ForegroundColor Gray
    }
    Write-Host "  해결방법: 다른 포트 사용하거나 기존 프로세스 종료" -ForegroundColor Cyan
} else {
    Write-Host "  [OK] 포트 8000이 사용 가능합니다" -ForegroundColor Green
}

# 5. 실행 중인 ngrok 프로세스 확인
Write-Host "[5/6] 실행 중인 ngrok 프로세스 확인..." -ForegroundColor Yellow
$ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    Write-Host "  [WARNING] 실행 중인 ngrok 프로세스 발견:" -ForegroundColor Yellow
    foreach ($proc in $ngrokProcesses) {
        Write-Host "    - PID: $($proc.Id), 시작 시간: $($proc.StartTime)" -ForegroundColor Gray
    }
    Write-Host "  해결방법: 기존 ngrok 프로세스를 종료하세요" -ForegroundColor Cyan
} else {
    Write-Host "  [OK] 실행 중인 ngrok 프로세스가 없습니다" -ForegroundColor Green
}

# 6. 방화벽/보안 소프트웨어 확인 (수동)
Write-Host "[6/6] 방화벽 확인..." -ForegroundColor Yellow
Write-Host "  [INFO] Windows 방화벽이 ngrok을 차단할 수 있습니다" -ForegroundColor Cyan
Write-Host "  해결방법: Windows 방화벽 설정에서 ngrok.exe 허용" -ForegroundColor Cyan
Write-Host ""

# 종합 진단 결과
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  진단 완료" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "  1. 위의 오류를 해결하세요" -ForegroundColor Cyan
Write-Host "  2. 서버 시작: .\start_ngrok.bat" -ForegroundColor Cyan
Write-Host "     또는: .\start_server_fixed.bat" -ForegroundColor Cyan
Write-Host ""
