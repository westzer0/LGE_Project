-- ============================================================
-- MEMBER 테이블 TASTE 칼럼 수정 (SQLite 호환)
-- TASTE를 1~1920 범위의 정수(INTEGER)로 보장
-- ============================================================

-- SQLite는 ALTER TABLE이 제한적이므로 다음 단계로 진행:
-- 1. 기존 TASTE 칼럼이 있으면 백업 테이블 생성
-- 2. 새 테이블 생성 (TASTE 칼럼 포함)
-- 3. 데이터 복사
-- 4. 기존 테이블 삭제 및 새 테이블 이름 변경

-- 주의: 이 스크립트는 MEMBER 테이블의 구조를 변경합니다.
-- 실행 전에 데이터 백업을 권장합니다.

-- ============================================================
-- 방법 1: 간단한 방법 (TASTE 칼럼이 이미 INTEGER인 경우)
-- ============================================================

-- TASTE 칼럼이 없으면 추가 (SQLite는 ALTER TABLE ADD COLUMN 지원)
-- 이미 있으면 에러가 발생하므로 무시하세요.

-- TASTE 칼럼 추가 (INTEGER, NULL 허용)
-- ALTER TABLE MEMBER ADD COLUMN TASTE INTEGER;

-- 기존 TASTE 값이 범위를 벗어나면 NULL로 설정
UPDATE MEMBER 
SET TASTE = NULL 
WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920);

-- ============================================================
-- 방법 2: 완전한 재생성 (TASTE 칼럼 타입 변경이 필요한 경우)
-- ============================================================

-- 1. 백업 테이블 생성
-- CREATE TABLE MEMBER_BACKUP AS SELECT * FROM MEMBER;

-- 2. 새 테이블 생성 (TASTE 칼럼 포함)
-- CREATE TABLE MEMBER_NEW (
--     -- 기존 MEMBER 테이블의 모든 칼럼을 여기에 정의
--     -- 예시:
--     -- ID INTEGER PRIMARY KEY,
--     -- USERNAME TEXT,
--     -- EMAIL TEXT,
     --     -- TASTE INTEGER CHECK(TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 1920)),
--     -- ... 기타 칼럼들
-- );

-- 3. 데이터 복사 (TASTE 값 정규화)
-- INSERT INTO MEMBER_NEW 
-- SELECT 
--     *,
--     CASE 
--         WHEN TASTE IS NULL THEN NULL
     --         WHEN TASTE < 1 OR TASTE > 1920 THEN NULL
--         ELSE TASTE
--     END AS TASTE
-- FROM MEMBER_BACKUP;

-- 4. 기존 테이블 삭제 및 새 테이블 이름 변경
-- DROP TABLE MEMBER;
-- ALTER TABLE MEMBER_NEW RENAME TO MEMBER;

-- ============================================================
-- 방법 3: Python/Django를 통한 마이그레이션 (권장)
-- ============================================================
-- Django migration을 사용하면 SQLite와 Oracle 모두에서 동작합니다.
-- python manage.py makemigrations
-- python manage.py migrate

-- ============================================================
-- 데이터 확인 쿼리
-- ============================================================

-- TASTE 값 분포 확인
SELECT 
    CASE 
        WHEN TASTE IS NULL THEN 'NULL'
        WHEN TASTE < 1 THEN '범위 밖 (< 1)'
        WHEN TASTE > 1920 THEN '범위 밖 (> 1920)'
        ELSE '정상 (1~1920)'
    END as taste_status,
    COUNT(*) as count
FROM MEMBER
GROUP BY taste_status
ORDER BY taste_status;

-- 통계 확인
SELECT 
    COUNT(*) as total_members,
    COUNT(TASTE) as members_with_taste,
    MIN(TASTE) as min_taste,
    MAX(TASTE) as max_taste,
    ROUND(AVG(TASTE), 2) as avg_taste
FROM MEMBER;

