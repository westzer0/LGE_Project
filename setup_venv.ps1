# Python 가상환경 설정 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Python 가상환경 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Python 설치 확인
Write-Host "[1/4] Python 설치 확인..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  $pythonVersion" -ForegroundColor Green
    Write-Host "  [OK] Python 확인 완료" -ForegroundColor Green
} catch {
    Write-Host "  [오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Python을 설치하거나 PATH 환경 변수를 설정해주세요." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host ""

# 2. 가상환경 존재 확인
Write-Host "[2/4] 가상환경 확인..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "  [정보] 가상환경이 이미 존재합니다." -ForegroundColor Cyan
    Write-Host "         위치: $(Get-Location)\venv" -ForegroundColor Cyan
} else {
    Write-Host "  [정보] 가상환경이 없습니다. 생성 중..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [오류] 가상환경 생성에 실패했습니다." -ForegroundColor Red
        Write-Host ""
        exit 1
    }
    Write-Host "  [OK] 가상환경 생성 완료" -ForegroundColor Green
}
Write-Host ""

# 3. 가상환경 활성화
Write-Host "[3/4] 가상환경 활성화..." -ForegroundColor Yellow
$activateScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    try {
        & $activateScript
        Write-Host "  [OK] 가상환경 활성화 완료" -ForegroundColor Green
    } catch {
        Write-Host "  [경고] 가상환경 활성화에 실패했습니다." -ForegroundColor Yellow
        Write-Host "         실행 정책 오류일 수 있습니다. 다음 명령을 실행하세요:" -ForegroundColor Yellow
        Write-Host "         Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [경고] 가상환경 활성화 스크립트를 찾을 수 없습니다." -ForegroundColor Yellow
}
Write-Host ""

# 4. pip 업그레이드 및 패키지 설치
Write-Host "[4/4] pip 업그레이드 및 패키지 설치..." -ForegroundColor Yellow
$pythonExe = ".\venv\Scripts\python.exe"

# pip 업그레이드
Write-Host "  pip 업그레이드 중..." -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip --quiet --disable-pip-version-check 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] pip 업그레이드 완료" -ForegroundColor Green
} else {
    Write-Host "  [경고] pip 업그레이드 실패 (계속 진행)" -ForegroundColor Yellow
}
Write-Host ""

# requirements.txt 확인 및 설치
if (Test-Path "requirements.txt") {
    Write-Host "  [정보] requirements.txt를 찾았습니다. 패키지 설치 중..." -ForegroundColor Cyan
    Write-Host "         (이 작업은 몇 분이 걸릴 수 있습니다)" -ForegroundColor Cyan
    Write-Host ""
    & $pythonExe -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  [OK] 모든 패키지 설치 완료" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  [경고] 일부 패키지 설치에 실패했습니다." -ForegroundColor Yellow
        Write-Host "         수동으로 설치해주세요: pip install -r requirements.txt" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [정보] requirements.txt 파일을 찾을 수 없습니다." -ForegroundColor Cyan
    Write-Host "         패키지는 수동으로 설치해주세요." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  가상환경 설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[사용 방법]" -ForegroundColor Yellow
Write-Host "  1. 가상환경 활성화:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. 가상환경 비활성화:" -ForegroundColor White
Write-Host "     deactivate" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. 서버 시작:" -ForegroundColor White
Write-Host "     .\start_server_fixed.bat" -ForegroundColor Cyan
Write-Host "     또는" -ForegroundColor White
Write-Host "     python manage.py runserver 8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

