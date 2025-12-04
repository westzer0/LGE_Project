# Oracle DB 연결 테스트 - PowerShell 스크립트
# 사용법: .\oracle_test.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Oracle DB 연결 테스트" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan

try {
    Write-Host "`n[1단계] 연결 테스트 중..." -ForegroundColor White
    
    $result = python -c "from api.db.oracle_client import fetch_one; result = fetch_one('SELECT USER, SYSDATE FROM DUAL'); print(f'{result[0]}|{result[1]}')" 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $result -match '\|') {
        $parts = $result -split '\|'
        Write-Host "✅ 연결 성공!" -ForegroundColor Green
        Write-Host "   사용자: $($parts[0])" -ForegroundColor Gray
        Write-Host "   서버 시간: $($parts[1])" -ForegroundColor Gray
        
        Write-Host "`n[2단계] 테이블 목록 조회 중..." -ForegroundColor White
        $tables = python -c "from api.db.oracle_client import fetch_all_dict; tables = fetch_all_dict('SELECT table_name FROM user_tables ORDER BY table_name'); print('|'.join([t['TABLE_NAME'] for t in tables]))" 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $tables) {
            $tableList = $tables -split '\|'
            Write-Host "✅ 발견된 테이블: $($tableList.Count)개`n" -ForegroundColor Green
            
            foreach ($table in $tableList) {
                if ($table) {
                    $count = python -c "from api.db.oracle_client import fetch_one; result = fetch_one('SELECT COUNT(*) FROM $table'); print(result[0] if result else 0)" 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  - $table ($count 개 행)" -ForegroundColor Cyan
                    } else {
                        Write-Host "  - $table (행 개수 조회 실패)" -ForegroundColor Yellow
                    }
                }
            }
        } else {
            Write-Host "⚠️ 테이블 목록 조회 실패" -ForegroundColor Yellow
            Write-Host $tables -ForegroundColor Red
        }
        
    } else {
        Write-Host "❌ 연결 실패!" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan



