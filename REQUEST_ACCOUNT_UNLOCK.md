# Oracle 계정 잠금 해제 요청

## 요청 내용
Oracle 데이터베이스 계정이 잠금 상태(ORA-28000)로 인해 접속이 불가능합니다. 계정 잠금 해제를 요청드립니다.

## 계정 정보
- **사용자명**: `CAMPUS_24K_LG3_DX7_P3_4`
- **데이터베이스**: `MAPPP`
- **호스트**: `project-db-campus.smhrd.com`
- **포트**: `1524`
- **SID**: `xe`

## 실행 요청 SQL

```sql
-- 계정 상태 확인
SELECT username, account_status, lock_date, expiry_date
FROM dba_users
WHERE username = 'CAMPUS_24K_LG3_DX7_P3_4';

-- 계정 잠금 해제
ALTER USER CAMPUS_24K_LG3_DX7_P3_4 ACCOUNT UNLOCK;

-- 해제 후 상태 확인
SELECT username, account_status, lock_date
FROM dba_users
WHERE username = 'CAMPUS_24K_LG3_DX7_P3_4';
```

## 오류 메시지
```
ORA-28000: the account is locked
28000. 00000 -  "The account is locked."
*Cause:    The wrong password was entered multiple consecutive times as
           specified by the profile parameter FAILED_LOGIN_ATTEMPTS, or the
           DBA locked the account, or the user is a common user locked in
           the root container.
*Action:   Wait for the PASSWORD_LOCK_TIME or contact the DBA.
```

## 참고사항
- 계정 잠금은 잘못된 비밀번호를 여러 번 입력했을 때 발생합니다.
- `PASSWORD_LOCK_TIME`이 지나면 자동으로 해제되지만, 즉시 해제가 필요한 상황입니다.
- 계정 잠금 해제 후 정상적으로 접속 가능한지 확인 부탁드립니다.

---
**요청일**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**요청자**: 개발팀
