-- ============================================================
-- MEMBER 테이블의 TASTE 칼럼을 1~120 범위의 난수로 채우기
-- Oracle 11g 호환
-- ============================================================

-- TASTE가 NULL인 모든 회원에 대해 1~120 범위의 난수 할당
UPDATE MEMBER
SET TASTE = TRUNC(DBMS_RANDOM.VALUE(1, 121))
WHERE TASTE IS NULL;

-- 결과 확인
SELECT 
    COUNT(*) as total_members,
    COUNT(TASTE) as members_with_taste,
    MIN(TASTE) as min_taste,
    MAX(TASTE) as max_taste,
    ROUND(AVG(TASTE), 2) as avg_taste
FROM MEMBER;

-- TASTE 값 분포 확인 (1~120 범위 확인)
SELECT 
    CASE 
        WHEN TASTE IS NULL THEN 'NULL'
        WHEN TASTE < 1 THEN '범위 밖 (< 1)'
        WHEN TASTE > 120 THEN '범위 밖 (> 120)'
        ELSE '정상 (1~120)'
    END as taste_status,
    COUNT(*) as count
FROM MEMBER
GROUP BY 
    CASE 
        WHEN TASTE IS NULL THEN 'NULL'
        WHEN TASTE < 1 THEN '범위 밖 (< 1)'
        WHEN TASTE > 120 THEN '범위 밖 (> 120)'
        ELSE '정상 (1~120)'
    END
ORDER BY taste_status;

COMMIT;

