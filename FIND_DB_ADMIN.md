# DB 관리자 연락처 찾기

## 현재 상황
- **DB 호스트**: `project-db-campus.smhrd.com`
- **기관**: SMHRD 캠퍼스
- **계정**: `campus_24K_LG3_DX7_p3_4`

## 관리자 연락처 찾는 방법

### 방법 1: 프로젝트 담당자에게 문의
- 프로젝트를 할당받은 교수님 또는 담당자에게 문의
- 캠퍼스 시스템 관리팀 연락처 요청

### 방법 2: SMHRD 캠퍼스 시스템 관리팀
- 캠퍼스 홈페이지에서 시스템 관리팀 연락처 확인
- IT 지원 센터 또는 데이터베이스 관리팀 문의

### 방법 3: 프로젝트 팀원에게 문의
- 같은 프로젝트를 진행하는 팀원에게 DB 관리자 연락처 확인
- 프로젝트 슬랙/팀즈 등 협업 도구에서 문의

### 방법 4: DB 호스트 정보 활용
- `project-db-campus.smhrd.com` 도메인 관리자에게 문의
- SMHRD 캠퍼스 IT 부서에 문의

## 요청 시 포함할 정보
1. 계정명: `CAMPUS_24K_LG3_DX7_P3_4`
2. 오류: `ORA-28000: the account is locked`
3. 요청 SQL: `ALTER USER CAMPUS_24K_LG3_DX7_P3_4 ACCOUNT UNLOCK;`
4. 긴급도: 즉시 해제 필요

## 준비된 파일
- `SEND_REQUEST_EMAIL.txt` - 요청 메시지
- `unlock_account_request.sql` - 실행할 SQL 파일
