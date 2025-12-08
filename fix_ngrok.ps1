# ngrok 문제 해결 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ngrok 문제 해결 도구" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$ngrokPath = Join-Path $projectRoot "ngrok\ngrok.exe"

# 1. ngrok.exe 존재 확인
Write-Host "[1/5] ngrok.exe 파일 확인..." -ForegroundColor Yellow
if (Test-Path $ngrokPath) {
    Write-Host "  [OK] ngrok.exe 발견: $ngrokPath" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] ngrok.exe를 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "  ngrok을 다운로드합니다..." -ForegroundColor Yellow
    
    # ngrok 다운로드
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $downloadPath = "$env:TEMP\ngrok.zip"
    $extractPath = Join-Path $projectRoot "ngrok"
    
    try {
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $downloadPath -UseBasicParsing
        if (Test-Path $extractPath) {
            Remove-Item $extractPath -Recurse -Force
        }
        New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
        Expand-Archive -Path $downloadPath -DestinationPath $extractPath -Force
        Write-Host "  [OK] ngrok 다운로드 완료" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] 다운로드 실패: $_" -ForegroundColor Red
        exit 1
    }
}

# 2. ngrok 버전 확인
Write-Host "[2/5] ngrok 버전 확인..." -ForegroundColor Yellow
try {
    $versionOutput = & $ngrokPath version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] ngrok 버전 확인 성공" -ForegroundColor Green
        Write-Host "  $versionOutput" -ForegroundColor Gray
    } else {
        Write-Host "  [WARNING] ngrok 버전 확인 실패 (Exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-Host "  출력: $versionOutput" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [ERROR] ngrok 실행 실패: $_" -ForegroundColor Red
}

# 3. ngrok 인증 토큰 확인 및 설정
Write-Host "[3/5] ngrok 인증 토큰 확인..." -ForegroundColor Yellow
try {
    $configOutput = & $ngrokPath config check 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] 인증 토큰이 설정되어 있습니다" -ForegroundColor Green
        Write-Host "  $configOutput" -ForegroundColor Gray
    } else {
        Write-Host "  [ERROR] 인증 토큰이 설정되지 않았습니다" -ForegroundColor Red
        Write-Host "  출력: $configOutput" -ForegroundColor Gray
        
        # .env 파일에서 토큰 확인
        $envFile = Join-Path $projectRoot ".env"
        $ngrokToken = $null
        if (Test-Path $envFile) {
            $envContent = Get-Content $envFile -Raw
            if ($envContent -match "NGROK.*TOKEN.*=.*([^\r\n]+)") {
                $ngrokToken = $matches[1].Trim()
            }
        }
        
        if ($ngrokToken) {
            Write-Host "  .env 파일에서 토큰을 찾았습니다. 설정 중..." -ForegroundColor Yellow
            & $ngrokPath config add-authtoken $ngrokToken
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] 인증 토큰 설정 완료" -ForegroundColor Green
            } else {
                Write-Host "  [ERROR] 인증 토큰 설정 실패" -ForegroundColor Red
            }
        } else {
            Write-Host "  해결방법:" -ForegroundColor Yellow
            Write-Host "    1. https://dashboard.ngrok.com/get-started/your-authtoken 접속" -ForegroundColor Cyan
            Write-Host "    2. 토큰 발급 후 다음 명령 실행:" -ForegroundColor Cyan
            Write-Host "       .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "  [ERROR] 인증 토큰 확인 실패: $_" -ForegroundColor Red
}

# 4. 포트 8000 확인
Write-Host "[4/5] 포트 8000 사용 확인..." -ForegroundColor Yellow
try {
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($port8000) {
        Write-Host "  [WARNING] 포트 8000이 이미 사용 중입니다" -ForegroundColor Yellow
        $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  프로세스: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [OK] 포트 8000이 사용 가능합니다" -ForegroundColor Green
    }
} catch {
    Write-Host "  [INFO] 포트 확인 실패 (권한 문제일 수 있음)" -ForegroundColor Yellow
}

# 5. 실행 중인 ngrok 프로세스 확인
Write-Host "[5/5] 실행 중인 ngrok 프로세스 확인..." -ForegroundColor Yellow
$ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    Write-Host "  [WARNING] 실행 중인 ngrok 프로세스 발견:" -ForegroundColor Yellow
    foreach ($proc in $ngrokProcesses) {
        Write-Host "    - PID: $($proc.Id)" -ForegroundColor Gray
    }
    $kill = Read-Host "  기존 프로세스를 종료하시겠습니까? (Y/N)"
    if ($kill -eq "Y" -or $kill -eq "y") {
        foreach ($proc in $ngrokProcesses) {
            Stop-Process -Id $proc.Id -Force
            Write-Host "    [OK] 프로세스 $($proc.Id) 종료됨" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  [OK] 실행 중인 ngrok 프로세스가 없습니다" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  진단 완료" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "  서버 시작: .\start_ngrok.bat" -ForegroundColor Cyan
Write-Host "  또는: .\start_server_fixed.bat" -ForegroundColor Cyan
Write-Host ""
