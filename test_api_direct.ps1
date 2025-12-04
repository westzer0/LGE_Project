# API 엔드포인트 직접 테스트 스크립트
# PowerShell에서 실행

Write-Host "=== API 엔드포인트 직접 테스트 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 기본 추천 API 테스트
Write-Host "[1/3] 기본 추천 API 테스트" -ForegroundColor Yellow
$body1 = @{
    vibe = "modern"
    household_size = 2
    housing_type = "apartment"
    pyung = 25
    priority = "tech"
    budget_level = "medium"
    budget_amount = 1500000
    categories = @("TV", "LIVING")
    has_pet = $false
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/recommend/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body1
    
    Write-Host "  ✓ 성공: 추천 $($response1.count)개" -ForegroundColor Green
    Write-Host "  Success: $($response1.success)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 실패: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  상세: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# 2. Playbook 추천 API 테스트
Write-Host "[2/3] Playbook 추천 API 테스트" -ForegroundColor Yellow
$body2 = @{
    vibe = "modern"
    household_size = 2
    housing_type = "apartment"
    pyung = 25
    priority = "tech"
    budget_level = "medium"
    budget_amount = 1500000
    categories = @("TV", "LIVING")
    has_pet = $false
    onboarding_data = @{
        cooking = "high"
        laundry = "daily"
        media = "gaming"
    }
    options = @{
        top_n = 3
    }
} | ConvertTo-Json -Depth 3

try {
    $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/recommend/playbook/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body2
    
    Write-Host "  ✓ 성공: 추천 $($response2.count)개" -ForegroundColor Green
    Write-Host "  Success: $($response2.success)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 실패: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  상세: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# 3. 칼럼 기반 추천 API 테스트
Write-Host "[3/3] 칼럼 기반 추천 API 테스트" -ForegroundColor Yellow
$body3 = @{
    vibe = "modern"
    household_size = 4
    housing_type = "apartment"
    pyung = 30
    priority = "tech"
    budget_level = "medium"
    budget_amount = 2000000
    categories = @("TV", "KITCHEN", "LIVING")
    has_pet = $false
    onboarding_data = @{
        cooking = "high"
        laundry = "daily"
        media = "gaming"
    }
} | ConvertTo-Json -Depth 3

try {
    $response3 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/recommend/column-based/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body3
    
    Write-Host "  ✓ 성공: 추천 $($response3.count)개" -ForegroundColor Green
    Write-Host "  Success: $($response3.success)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 실패: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  상세: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== 테스트 완료 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "참고: Django 서버가 실행 중이어야 합니다." -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Yellow

