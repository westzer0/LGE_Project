# 서버 상태 확인 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  서버 현황 체크" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 실행 중인 프로세스 확인
Write-Host "[1/4] 실행 중인 프로세스 확인..." -ForegroundColor Yellow
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -match "python"} | Select-Object ProcessName, Id, StartTime
$nodeProcesses = Get-Process | Where-Object {$_.ProcessName -match "node"} | Select-Object ProcessName, Id, StartTime
$ngrokProcesses = Get-Process | Where-Object {$_.ProcessName -match "ngrok"} | Select-Object ProcessName, Id, StartTime

if ($pythonProcesses) {
    Write-Host "  Python 프로세스:" -ForegroundColor Green
    $pythonProcesses | Format-Table -AutoSize
} else {
    Write-Host "  Python 프로세스: 없음" -ForegroundColor Red
}

if ($nodeProcesses) {
    Write-Host "  Node 프로세스:" -ForegroundColor Green
    $nodeProcesses | Format-Table -AutoSize
} else {
    Write-Host "  Node 프로세스: 없음" -ForegroundColor Red
}

if ($ngrokProcesses) {
    Write-Host "  ngrok 프로세스:" -ForegroundColor Green
    $ngrokProcesses | Format-Table -AutoSize
} else {
    Write-Host "  ngrok 프로세스: 없음" -ForegroundColor Red
}

Write-Host ""

# 2. 포트 사용 확인
Write-Host "[2/4] 포트 사용 확인..." -ForegroundColor Yellow
$ports = @(8000, 3000, 5173, 4040)
foreach ($port in $ports) {
    $listening = netstat -ano | Select-String "LISTENING" | Select-String ":$port "
    if ($listening) {
        $pid = ($listening -split '\s+')[-1]
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        $processName = if ($process) { $process.ProcessName } else { "알 수 없음" }
        Write-Host "  포트 $port : 사용 중 (PID: $pid, 프로세스: $processName)" -ForegroundColor Green
    } else {
        Write-Host "  포트 $port : 사용 안 함" -ForegroundColor Red
    }
}

Write-Host ""

# 3. 환경 설정 확인
Write-Host "[3/4] 환경 설정 확인..." -ForegroundColor Yellow

# .env 파일 확인
if (Test-Path ".env") {
    Write-Host "  .env 파일: 존재함" -ForegroundColor Green
    # 중요한 환경 변수 확인 (값은 숨김)
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    if ($envContent) {
        $hasOracle = $envContent | Select-String -Pattern "USE_ORACLE\s*=\s*true" -Quiet
        $hasKakao = $envContent | Select-String -Pattern "KAKAO_REST_API_KEY" -Quiet
        $hasOpenAI = $envContent | Select-String -Pattern "OPENAI_API_KEY" -Quiet
        
        Write-Host "    USE_ORACLE: $(if ($hasOracle) { '설정됨' } else { '미설정 (SQLite 사용)' })" -ForegroundColor $(if ($hasOracle) { 'Green' } else { 'Yellow' })
        Write-Host "    KAKAO API: $(if ($hasKakao) { '설정됨' } else { '미설정' })" -ForegroundColor $(if ($hasKakao) { 'Green' } else { 'Yellow' })
        Write-Host "    OpenAI API: $(if ($hasOpenAI) { '설정됨' } else { '미설정' })" -ForegroundColor $(if ($hasOpenAI) { 'Green' } else { 'Yellow' })
    }
} else {
    Write-Host "  .env 파일: 없음 (env.example 참고)" -ForegroundColor Red
}

# 가상환경 확인
if (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "  Python 가상환경: 존재함" -ForegroundColor Green
} else {
    Write-Host "  Python 가상환경: 없음" -ForegroundColor Yellow
}

# node_modules 확인
if (Test-Path "node_modules") {
    Write-Host "  Node 모듈: 설치됨" -ForegroundColor Green
} else {
    Write-Host "  Node 모듈: 미설정 (npm install 필요)" -ForegroundColor Red
}

# ngrok 확인
if (Test-Path "ngrok\ngrok.exe") {
    Write-Host "  ngrok: 설치됨" -ForegroundColor Green
} else {
    Write-Host "  ngrok: 없음 (setup_ngrok_simple.ps1 실행 필요)" -ForegroundColor Red
}

Write-Host ""

# 4. 서버 연결 테스트
Write-Host "[4/4] 서버 연결 테스트..." -ForegroundColor Yellow

# Django 서버 테스트
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  Django 서버 (8000): 응답함 (상태: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Django 서버 (8000): 응답 없음" -ForegroundColor Red
}

# Vite 서버 테스트
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  Vite 서버 (3000): 응답함 (상태: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Vite 서버 (3000): 응답 없음" -ForegroundColor Red
}

# ngrok 테스트
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    $tunnels = $response.Content | ConvertFrom-Json
    if ($tunnels.tunnels) {
        Write-Host "  ngrok (4040): 실행 중" -ForegroundColor Green
        foreach ($tunnel in $tunnels.tunnels) {
            Write-Host "    터널: $($tunnel.public_url) -> $($tunnel.config.addr)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ngrok (4040): 실행 중이지만 터널 없음" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ngrok (4040): 응답 없음" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  요약" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "백엔드 서버 시작: start_server_fixed.bat" -ForegroundColor Yellow
Write-Host "프론트엔드 서버 시작: npm run dev" -ForegroundColor Yellow
Write-Host "ngrok 설정: setup_ngrok_simple.ps1" -ForegroundColor Yellow
Write-Host ""
