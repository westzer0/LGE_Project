# 빠른 서버 문제 해결 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  서버 문제 빠른 해결" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "c:\Users\134\Desktop\DX Project"
Set-Location $projectPath

# 1. SQLite로 전환 (Oracle 문제 회피)
Write-Host "[1/5] 데이터베이스 설정 확인..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  .env 파일이 없습니다. SQLite를 사용합니다." -ForegroundColor Green
} else {
    # .env 파일에 USE_ORACLE=false 추가 (없으면)
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    if ($envContent -notmatch "USE_ORACLE") {
        Add-Content ".env" "`nUSE_ORACLE=false"
        Write-Host "  .env에 USE_ORACLE=false 추가됨" -ForegroundColor Green
    }
}

# 2. 가상환경 확인
Write-Host "[2/5] 가상환경 확인..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "  ✓ 가상환경 존재" -ForegroundColor Green
    $pythonExe = ".\venv\Scripts\python.exe"
} else {
    Write-Host "  ⚠ 시스템 Python 사용" -ForegroundColor Yellow
    $pythonExe = "python"
}

# 3. Django 설치 확인
Write-Host "[3/5] Django 설치 확인..." -ForegroundColor Yellow
$djangoCheck = & $pythonExe -c "import django; print(django.get_version())" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Django 설치됨: $djangoCheck" -ForegroundColor Green
} else {
    Write-Host "  ✗ Django 미설치 - 설치 중..." -ForegroundColor Red
    & $pythonExe -m pip install django
}

# 4. 마이그레이션
Write-Host "[4/5] 데이터베이스 마이그레이션..." -ForegroundColor Yellow
& $pythonExe manage.py migrate --run-syncdb 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 마이그레이션 완료" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 마이그레이션 경고 (계속 진행)" -ForegroundColor Yellow
}

# 5. 서버 시작
Write-Host "[5/5] Django 서버 시작..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  서버가 http://127.0.0.1:8000 에서 실행됩니다" -ForegroundColor Green
Write-Host "  중지하려면 Ctrl+C를 누르세요" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& $pythonExe manage.py runserver 8000
