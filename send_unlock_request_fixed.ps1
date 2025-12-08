# Oracle 계정 잠금 해제 요청 이메일/메시지 생성 스크립트
# UTF-8 인코딩 설정 (한글 깨짐 방지)
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
if ($PSVersionTable.PSVersion.Major -lt 6) {
    chcp 65001 | Out-Null
}

$requestDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$username = "CAMPUS_24K_LG3_DX7_P3_4"
$dbHost = "project-db-campus.smhrd.com"
$dbPort = "1524"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Oracle 계정 잠금 해제 요청 메시지 생성" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$message = @"
[긴급] Oracle 계정 잠금 해제 요청

안녕하세요,

Oracle 데이터베이스 계정이 잠금 상태로 인해 접속이 불가능합니다.
계정 잠금 해제를 요청드립니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 계정 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 사용자명: $username
• 데이터베이스: MAPPP
• 호스트: ${dbHost}:${dbPort}
• SID: xe

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 실행 요청 SQL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 계정 상태 확인
SELECT username, account_status, lock_date, expiry_date
FROM dba_users
WHERE username = '$username';

-- 계정 잠금 해제
ALTER USER $username ACCOUNT UNLOCK;

-- 해제 후 상태 확인
SELECT username, account_status, lock_date
FROM dba_users
WHERE username = '$username';

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 오류 메시지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORA-28000: the account is locked

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 참고사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 계정 잠금은 잘못된 비밀번호를 여러 번 입력했을 때 발생합니다.
• PASSWORD_LOCK_TIME이 지나면 자동으로 해제되지만, 즉시 해제가 필요한 상황입니다.
• 계정 잠금 해제 후 정상적으로 접속 가능한지 확인 부탁드립니다.

요청일시: $requestDate
요청자: 개발팀

"@

# 메시지 출력 (UTF-8 인코딩으로)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host $message

# 클립보드에 복사
$message | Set-Clipboard
Write-Host ""
Write-Host "✅ 요청 메시지가 클립보드에 복사되었습니다!" -ForegroundColor Green
Write-Host "   이메일이나 메신저에 붙여넣기 하세요." -ForegroundColor Yellow
Write-Host ""

# 파일로 저장 (UTF-8 BOM)
$outputFile = "unlock_request_message.txt"
[System.IO.File]::WriteAllText((Resolve-Path .).Path + "\$outputFile", $message, [System.Text.Encoding]::UTF8)
Write-Host "✅ 요청 메시지가 파일로 저장되었습니다: $outputFile" -ForegroundColor Green
Write-Host ""

# SQL 파일 위치 안내
Write-Host "📄 SQL 파일 위치:" -ForegroundColor Cyan
Write-Host "   - unlock_account_request.sql (상세 SQL)" -ForegroundColor White
Write-Host "   - REQUEST_ACCOUNT_UNLOCK.md (요청 문서)" -ForegroundColor White
Write-Host ""
