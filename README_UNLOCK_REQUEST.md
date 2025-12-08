# Oracle 계정 잠금 해제 요청 가이드

## 한글 깨짐 문제 해결

PowerShell 콘솔에서 한글이 깨져 보이는 경우:

### 방법 1: 파일 직접 열기 (권장)
생성된 `unlock_request_message.txt` 파일을 메모장이나 VS Code로 직접 열어보세요.
- 파일은 UTF-8로 올바르게 저장되어 있습니다.
- 메모장: 파일 열기 → 인코딩 선택 → UTF-8
- VS Code: 자동으로 UTF-8로 인식

### 방법 2: 배치 파일 사용
```cmd
.\send_unlock_request.bat
```

### 방법 3: PowerShell에서 UTF-8 설정
PowerShell을 실행하기 전에:
```powershell
chcp 65001
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
.\send_unlock_request.ps1
```

## 생성된 파일들

1. **unlock_request_message.txt** - 요청 메시지 (UTF-8)
2. **unlock_account_request.sql** - 실행할 SQL 파일
3. **REQUEST_ACCOUNT_UNLOCK.md** - 요청 문서

## 사용 방법

1. `unlock_request_message.txt` 파일을 열어서 내용 확인
2. 내용을 복사해서 DB 관리자에게 전달
3. 또는 `unlock_account_request.sql` 파일을 직접 전달

## 핵심 SQL

```sql
ALTER USER CAMPUS_24K_LG3_DX7_P3_4 ACCOUNT UNLOCK;
```
