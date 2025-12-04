# Oracle DB 전체 분석 - PowerShell 스크립트
# 사용법: .\oracle_analyze.ps1

Write-Host "Oracle DB 전체 분석을 시작합니다..." -ForegroundColor Yellow
Write-Host "분석 결과는 'ORACLE_DB_ANALYSIS_RESULT.md' 파일에 저장됩니다.`n" -ForegroundColor Gray

python analyze_oracle_complete.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 분석 완료!" -ForegroundColor Green
    Write-Host "결과 파일: ORACLE_DB_ANALYSIS_RESULT.md" -ForegroundColor Cyan
    
    if (Test-Path "ORACLE_DB_ANALYSIS_RESULT.md") {
        Write-Host "`n파일을 열까요? (Y/N): " -NoNewline -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq 'Y' -or $response -eq 'y') {
            notepad "ORACLE_DB_ANALYSIS_RESULT.md"
        }
    }
} else {
    Write-Host "`n❌ 분석 실패!" -ForegroundColor Red
}



