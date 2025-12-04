-- ============================================================
-- 온보딩 테이블 칼럼 추가 (기존 테이블 업데이트용)
-- Oracle 11g 호환
-- ============================================================

-- ONBOARDING_SESSION 테이블에 추가 칼럼 추가
ALTER TABLE ONBOARDING_SESSION ADD (
    HAS_PET CHAR(1),  -- Step 2: 반려동물 여부 (Y/N)
    MAIN_SPACE CLOB,  -- Step 3: 주요 공간 (JSON 배열 문자열, 다중 선택)
    COOKING VARCHAR2(20),  -- Step 4: 요리 빈도
    LAUNDRY VARCHAR2(20),  -- Step 4: 세탁 빈도
    MEDIA VARCHAR2(20),  -- Step 4: 미디어 사용 패턴
    PRIORITY_LIST CLOB  -- Step 5: 우선순위 목록 (JSON 배열 문자열, 다중 선택)
);

-- 기존 데이터 업데이트 (RECOMMENDATION_RESULT에서 추출)
-- 주의: 이 스크립트는 RECOMMENDATION_RESULT가 JSON 형식일 때만 작동합니다.

-- HAS_PET 업데이트
UPDATE ONBOARDING_SESSION
SET HAS_PET = CASE 
    WHEN RECOMMENDATION_RESULT LIKE '%"pet":"yes"%' OR RECOMMENDATION_RESULT LIKE '%"has_pet":true%' THEN 'Y'
    WHEN RECOMMENDATION_RESULT LIKE '%"pet":"no"%' OR RECOMMENDATION_RESULT LIKE '%"has_pet":false%' THEN 'N'
    ELSE NULL
END
WHERE RECOMMENDATION_RESULT IS NOT NULL;

-- MAIN_SPACE 업데이트 (JSON 배열 추출)
-- 주의: Oracle 11g에서는 JSON 함수가 제한적이므로, 
-- 필요시 애플리케이션 레벨에서 업데이트하는 것을 권장합니다.

-- COOKING, LAUNDRY, MEDIA 업데이트
UPDATE ONBOARDING_SESSION
SET COOKING = CASE 
    WHEN RECOMMENDATION_RESULT LIKE '%"cooking":"rarely"%' THEN 'rarely'
    WHEN RECOMMENDATION_RESULT LIKE '%"cooking":"sometimes"%' THEN 'sometimes'
    WHEN RECOMMENDATION_RESULT LIKE '%"cooking":"often"%' THEN 'often'
    ELSE NULL
END
WHERE RECOMMENDATION_RESULT IS NOT NULL;

UPDATE ONBOARDING_SESSION
SET LAUNDRY = CASE 
    WHEN RECOMMENDATION_RESULT LIKE '%"laundry":"weekly"%' THEN 'weekly'
    WHEN RECOMMENDATION_RESULT LIKE '%"laundry":"few_times"%' THEN 'few_times'
    WHEN RECOMMENDATION_RESULT LIKE '%"laundry":"daily"%' THEN 'daily'
    ELSE NULL
END
WHERE RECOMMENDATION_RESULT IS NOT NULL;

UPDATE ONBOARDING_SESSION
SET MEDIA = CASE 
    WHEN RECOMMENDATION_RESULT LIKE '%"media":"ott"%' THEN 'ott'
    WHEN RECOMMENDATION_RESULT LIKE '%"media":"gaming"%' THEN 'gaming'
    WHEN RECOMMENDATION_RESULT LIKE '%"media":"tv"%' THEN 'tv'
    WHEN RECOMMENDATION_RESULT LIKE '%"media":"none"%' THEN 'none'
    ELSE NULL
END
WHERE RECOMMENDATION_RESULT IS NOT NULL;

-- PRIORITY_LIST 업데이트
-- 주의: JSON 배열 추출은 복잡하므로, 애플리케이션 레벨에서 업데이트하는 것을 권장합니다.

COMMIT;

-- ============================================================
-- 참고: JSON 데이터 추출이 복잡한 경우
-- ============================================================
-- Oracle 11g에서는 JSON 함수가 제한적이므로,
-- 애플리케이션 레벨에서 RECOMMENDATION_RESULT를 파싱하여
-- 위 칼럼들을 업데이트하는 것을 권장합니다.
--
-- Python 예시:
-- from api.services.onboarding_db_service import onboarding_db_service
-- from api.db.oracle_client import get_connection
-- import json
--
-- with get_connection() as conn:
--     with conn.cursor() as cur:
--         cur.execute("SELECT SESSION_ID, RECOMMENDATION_RESULT FROM ONBOARDING_SESSION")
--         for row in cur:
--             session_id, result_json = row
--             if result_json:
--                 result = json.loads(result_json)
--                 cur.execute("""
--                     UPDATE ONBOARDING_SESSION SET
--                         HAS_PET = :has_pet,
--                         MAIN_SPACE = :main_space,
--                         COOKING = :cooking,
--                         LAUNDRY = :laundry,
--                         MEDIA = :media,
--                         PRIORITY_LIST = :priority_list
--                     WHERE SESSION_ID = :session_id
--                 """, {
--                     'session_id': session_id,
--                     'has_pet': 'Y' if result.get('has_pet') or result.get('pet') == 'yes' else 'N',
--                     'main_space': json.dumps(result.get('main_space', []), ensure_ascii=False) if result.get('main_space') else None,
--                     'cooking': result.get('cooking'),
--                     'laundry': result.get('laundry'),
--                     'media': result.get('media'),
--                     'priority_list': json.dumps(result.get('priority', []), ensure_ascii=False) if result.get('priority') else None
--                 })
--         conn.commit()

