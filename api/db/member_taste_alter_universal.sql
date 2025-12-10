-- ============================================================
-- MEMBER 테이블 TASTE 칼럼 수정 (범용 SQL - SQLite/Oracle/PostgreSQL 호환)
-- TASTE를 1~1920 범위의 정수로 보장
-- ============================================================
-- 이 파일은 표준 SQL을 사용하여 여러 데이터베이스에서 동작합니다.
-- 데이터베이스별 특수 기능은 사용하지 않습니다.

-- 주의: 실행 전에 데이터 백업을 권장합니다.

-- ============================================================
-- 1. TASTE 칼럼 추가 (없는 경우)
-- ============================================================
-- SQLite: ALTER TABLE ADD COLUMN 지원
-- Oracle: ALTER TABLE ADD COLUMN 지원 (11g 이상)
-- PostgreSQL: ALTER TABLE ADD COLUMN 지원

-- TASTE 칼럼이 이미 있으면 이 명령은 실패합니다 (무시하세요)
-- ALTER TABLE MEMBER ADD COLUMN TASTE INTEGER;

-- ============================================================
-- 2. 기존 데이터 정리 (범위를 벗어난 값 처리)
-- ============================================================

-- 범위를 벗어난 값은 NULL로 설정
UPDATE MEMBER 
SET TASTE = NULL 
WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920);

-- 또는 범위 내 값으로 변환 (나머지 연산 사용)
-- UPDATE MEMBER 
-- SET TASTE = (ABS(TASTE) % 1920) + 1
-- WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920);

-- ============================================================
-- 3. 제약조건 추가 (데이터베이스별로 다름)
-- ============================================================

-- SQLite: CHECK 제약조건은 ALTER TABLE로 추가 불가
--         테이블 생성 시에만 추가 가능
--         따라서 애플리케이션 레벨에서 검증 필요

-- Oracle: CHECK 제약조건 추가 가능
-- ALTER TABLE MEMBER ADD CONSTRAINT CHK_TASTE_RANGE 
-- CHECK (TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 1920));

-- PostgreSQL: CHECK 제약조건 추가 가능
-- ALTER TABLE MEMBER ADD CONSTRAINT CHK_TASTE_RANGE 
-- CHECK (TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 1920));

-- ============================================================
-- 4. 데이터 확인
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
GROUP BY 
    CASE 
        WHEN TASTE IS NULL THEN 'NULL'
        WHEN TASTE < 1 THEN '범위 밖 (< 1)'
        WHEN TASTE > 1920 THEN '범위 밖 (> 1920)'
        ELSE '정상 (1~1920)'
    END
ORDER BY taste_status;

-- 통계 확인
SELECT 
    COUNT(*) as total_members,
    COUNT(TASTE) as members_with_taste,
    MIN(TASTE) as min_taste,
    MAX(TASTE) as max_taste,
    ROUND(AVG(TASTE), 2) as avg_taste
FROM MEMBER;

