-- ============================================================
-- MEMBER 테이블의 TASTE 칼럼을 1~1920 범위의 난수로 채우기 (SQLite 호환)
-- ============================================================

-- SQLite는 DBMS_RANDOM이 없으므로 다른 방법 사용
-- Python이나 애플리케이션 레벨에서 처리하는 것을 권장합니다.

-- ============================================================
-- 방법 1: Python 스크립트 사용 (권장)
-- ============================================================
-- Python의 random 모듈을 사용하여 업데이트:
-- import sqlite3
-- import random
-- 
-- conn = sqlite3.connect('db.sqlite3')
-- cursor = conn.cursor()
-- cursor.execute("UPDATE MEMBER SET TASTE = ? WHERE TASTE IS NULL", 
--                (random.randint(1, 1920),))
-- conn.commit()

-- ============================================================
-- 방법 2: SQLite의 abs(random()) 사용 (제한적)
-- ============================================================

-- TASTE가 NULL인 모든 회원에 대해 1~1920 범위의 난수 할당
-- SQLite의 random()은 -9223372036854775808 ~ 9223372036854775807 범위의 정수를 반환
-- 이를 1~1920 범위로 변환: (abs(random()) % 1920) + 1

UPDATE MEMBER
SET TASTE = (abs(random()) % 1920) + 1
WHERE TASTE IS NULL;

-- ============================================================
-- 방법 3: 고정된 순환 값 할당 (테스트용)
-- ============================================================
-- 각 행에 순차적으로 1~1920 값을 할당 (난수는 아님)
-- UPDATE MEMBER
-- SET TASTE = ((rowid - 1) % 1920) + 1
-- WHERE TASTE IS NULL;

-- ============================================================
-- 결과 확인
-- ============================================================

-- 통계 확인
SELECT 
    COUNT(*) as total_members,
    COUNT(TASTE) as members_with_taste,
    MIN(TASTE) as min_taste,
    MAX(TASTE) as max_taste,
    ROUND(AVG(TASTE), 2) as avg_taste
FROM MEMBER;

-- TASTE 값 분포 확인 (1~1920 범위 확인)
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

-- TASTE 값별 개수 확인 (1~1920 각 값의 분포)
SELECT 
    TASTE,
    COUNT(*) as count
FROM MEMBER
WHERE TASTE IS NOT NULL
GROUP BY TASTE
ORDER BY TASTE;

