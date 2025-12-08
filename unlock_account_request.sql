-- ============================================================
-- Oracle 계정 잠금 해제 요청 SQL
-- ============================================================
-- 사용자: CAMPUS_24K_LG3_DX7_P3_4
-- 데이터베이스: MAPPP (project-db-campus.smhrd.com:1524)
-- 오류: ORA-28000 (the account is locked)
-- ============================================================

-- [1단계] 계정 상태 확인
SELECT 
    username,
    account_status,
    lock_date,
    expiry_date,
    created,
    profile
FROM dba_users
WHERE username = 'CAMPUS_24K_LG3_DX7_P3_4';

-- [2단계] 계정 잠금 해제
ALTER USER CAMPUS_24K_LG3_DX7_P3_4 ACCOUNT UNLOCK;

-- [3단계] 해제 후 상태 확인
SELECT 
    username,
    account_status,
    lock_date
FROM dba_users
WHERE username = 'CAMPUS_24K_LG3_DX7_P3_4';

-- [4단계] (선택사항) 프로파일 설정 확인
-- FAILED_LOGIN_ATTEMPTS와 PASSWORD_LOCK_TIME 확인
SELECT 
    profile,
    resource_name,
    limit
FROM dba_profiles
WHERE profile = (
    SELECT profile 
    FROM dba_users 
    WHERE username = 'CAMPUS_24K_LG3_DX7_P3_4'
)
AND resource_name IN ('FAILED_LOGIN_ATTEMPTS', 'PASSWORD_LOCK_TIME');

-- ============================================================
-- 참고: 계정 잠금 해제 후 정상 접속 가능한지 확인 부탁드립니다.
-- ============================================================
