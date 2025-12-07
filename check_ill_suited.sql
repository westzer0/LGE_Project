-- Oracle SQL Developer에서 실행할 쿼리

-- 1. ILL_SUITED_CATEGORIES 컬럼 확인
SELECT column_name, data_type, data_length, nullable
FROM user_tab_columns 
WHERE table_name = 'TASTE_CONFIG' 
  AND column_name LIKE '%ILL%'
ORDER BY column_id;

-- 2. 모든 컬럼 목록 확인 (ILL_SUITED_CATEGORIES 포함)
SELECT column_name, data_type, data_length
FROM user_tab_columns 
WHERE table_name = 'TASTE_CONFIG' 
ORDER BY column_id;

-- 3. ILL_SUITED_CATEGORIES 컬럼이 있는지 직접 확인
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM user_tab_columns 
            WHERE table_name = 'TASTE_CONFIG' 
            AND column_name = 'ILL_SUITED_CATEGORIES'
        ) THEN 'ILL_SUITED_CATEGORIES 컬럼이 존재합니다.'
        ELSE 'ILL_SUITED_CATEGORIES 컬럼이 존재하지 않습니다.'
    END AS status
FROM dual;



