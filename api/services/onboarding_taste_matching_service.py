"""
ONBOARDING_SESSION의 taste_id를 TASTE_CONFIG와 비교하여 업데이트하는 서비스
"""
from typing import Optional, List
from api.db.oracle_client import get_connection, fetch_all_dict


class OnboardingTasteMatchingService:
    """온보딩 세션과 Taste Config를 매칭하여 taste_id를 업데이트하는 서비스"""
    
    @staticmethod
    def update_taste_id_for_session(session_id: str) -> Optional[int]:
        """
        특정 세션의 taste_id를 TASTE_CONFIG와 비교하여 업데이트
        
        Args:
            session_id: 온보딩 세션 ID
            
        Returns:
            업데이트된 taste_id 또는 None (매칭 실패 시)
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. ONBOARDING_SESSION 데이터 조회
                cur.execute("""
                    SELECT 
                        VIBE,
                        HOUSEHOLD_SIZE,
                        HAS_PET,
                        PRIORITY,
                        BUDGET_LEVEL
                    FROM ONBOARDING_SESSION
                    WHERE SESSION_ID = :session_id
                """, {'session_id': session_id})
                
                cols = [c[0] for c in cur.description]
                row = cur.fetchone()
                
                if not row:
                    print(f"[OnboardingTasteMatchingService] 세션을 찾을 수 없습니다: {session_id}", flush=True)
                    return None
                
                session_data = dict(zip(cols, row))
                
                # 2. MAIN_SPACE 정규화 테이블에서 조회
                cur.execute("""
                    SELECT MAIN_SPACE 
                    FROM ONBOARD_SESS_MAIN_SPACES
                    WHERE SESSION_ID = :session_id
                    ORDER BY MAIN_SPACE
                """, {'session_id': session_id})
                main_spaces = [row[0] for row in cur.fetchall()]
                main_space_str = ','.join(sorted(main_spaces)) if main_spaces else None
                
                # 3. TASTE_CONFIG에서 매칭되는 taste_id 찾기
                # 비교 조건:
                # - representative_vibe = VIBE
                # - representative_household_size = HOUSEHOLD_SIZE
                # - representative_main_space = MAIN_SPACE (정렬된 문자열, NULL 처리)
                # - representative_has_pet = HAS_PET (Y/N)
                # - representative_priority = PRIORITY
                # - representative_budget_level = BUDGET_LEVEL
                
                # HAS_PET 변환 (ONBOARDING_SESSION은 'Y'/'N', TASTE_CONFIG도 'Y'/'N')
                has_pet_char = session_data.get('HAS_PET') or 'N'
                
                # MAIN_SPACE가 NULL이거나 빈 문자열일 때는 NULL로 처리
                if not main_space_str:
                    main_space_str = None
                
                # BUDGET_LEVEL 매핑 (ONBOARDING_SESSION → TASTE_CONFIG)
                budget_level = session_data.get('BUDGET_LEVEL')
                budget_level_mapping = {
                    'low': 'low',
                    'budget': 'low',
                    'medium': 'medium',
                    'standard': 'medium',
                    'high': 'high',
                    'high_end': 'high',
                    'premium': 'high',
                    'luxury': 'high'
                }
                budget_level = budget_level_mapping.get(budget_level, budget_level)
                
                # 동적 WHERE 조건 생성 (NULL 처리)
                conditions = [
                    "REPRESENTATIVE_VIBE = :vibe",
                    "REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size",
                    "REPRESENTATIVE_HAS_PET = :has_pet",
                    "REPRESENTATIVE_PRIORITY = :priority",
                    "REPRESENTATIVE_BUDGET_LEVEL = :budget_level",
                    "IS_ACTIVE = 'Y'"
                ]
                
                params = {
                    'vibe': session_data.get('VIBE'),
                    'household_size': session_data.get('HOUSEHOLD_SIZE'),
                    'has_pet': has_pet_char,
                    'priority': session_data.get('PRIORITY'),
                    'budget_level': budget_level
                }
                
                # MAIN_SPACE 조건 추가 (빈 문자열이면 조건에서 제외)
                # TASTE_CONFIG에는 MAIN_SPACE가 항상 값이 있으므로, 
                # ONBOARDING_SESSION의 MAIN_SPACE가 빈 문자열이면 조건에서 제외
                if main_space_str:
                    conditions.append("REPRESENTATIVE_MAIN_SPACE = :main_space")
                    params['main_space'] = main_space_str
                # MAIN_SPACE가 없으면 조건에서 제외 (모든 MAIN_SPACE와 매칭 가능)
                
                where_clause = " AND ".join(conditions)
                
                cur.execute(f"""
                    SELECT TASTE_ID
                    FROM (
                        SELECT TASTE_ID
                        FROM TASTE_CONFIG
                        WHERE {where_clause}
                        ORDER BY TASTE_ID
                    )
                    WHERE ROWNUM <= 1
                """, params)
                
                result = cur.fetchone()
                
                if result:
                    taste_id = int(result[0])
                    
                    # 4. ONBOARDING_SESSION의 TASTE_ID 업데이트
                    cur.execute("""
                        UPDATE ONBOARDING_SESSION
                        SET TASTE_ID = :taste_id
                        WHERE SESSION_ID = :session_id
                    """, {
                        'taste_id': taste_id,
                        'session_id': session_id
                    })
                    conn.commit()
                    
                    print(f"[OnboardingTasteMatchingService] ✅ 세션 {session_id}의 TASTE_ID를 {taste_id}로 업데이트했습니다.", flush=True)
                    return taste_id
                else:
                    print(f"[OnboardingTasteMatchingService] ⚠️ 세션 {session_id}에 매칭되는 TASTE_CONFIG를 찾을 수 없습니다.", flush=True)
                    return None
    
    @staticmethod
    def update_taste_id_for_all_sessions(limit: Optional[int] = None) -> dict:
        """
        모든 온보딩 세션의 taste_id를 업데이트
        
        Args:
            limit: 처리할 최대 세션 수 (None이면 전체)
            
        Returns:
            업데이트 결과 통계
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # TASTE_ID가 NULL이거나 업데이트가 필요한 세션 조회
                if limit:
                    query = """
                        SELECT SESSION_ID
                        FROM (
                            SELECT SESSION_ID
                            FROM ONBOARDING_SESSION
                            WHERE STATUS = 'COMPLETED'
                              AND (TASTE_ID IS NULL OR TASTE_ID = 0)
                            ORDER BY CREATED_AT DESC
                        )
                        WHERE ROWNUM <= :limit
                    """
                    params = {'limit': limit}
                else:
                    query = """
                        SELECT SESSION_ID
                        FROM ONBOARDING_SESSION
                        WHERE STATUS = 'COMPLETED'
                          AND (TASTE_ID IS NULL OR TASTE_ID = 0)
                        ORDER BY CREATED_AT DESC
                    """
                    params = {}
                
                cur.execute(query, params)
                session_ids = [row[0] for row in cur.fetchall()]
                
                updated_count = 0
                failed_count = 0
                
                for session_id in session_ids:
                    try:
                        taste_id = OnboardingTasteMatchingService.update_taste_id_for_session(session_id)
                        if taste_id:
                            updated_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        print(f"[OnboardingTasteMatchingService] ⚠️ 세션 {session_id} 처리 중 오류: {e}", flush=True)
                        failed_count += 1
                
                result = {
                    'total_processed': len(session_ids),
                    'updated': updated_count,
                    'failed': failed_count
                }
                
                print(f"[OnboardingTasteMatchingService] ✅ 업데이트 완료: {result}", flush=True)
                return result
    
    @staticmethod
    def find_matching_taste_config(
        vibe: Optional[str] = None,
        household_size: Optional[int] = None,
        main_space: Optional[str] = None,
        has_pet: Optional[bool] = None,
        priority: Optional[str] = None,
        budget_level: Optional[str] = None
    ) -> List[dict]:
        """
        주어진 온보딩 데이터와 매칭되는 TASTE_CONFIG 목록 조회
        
        Args:
            vibe: 인테리어 무드
            household_size: 가구 인원수
            main_space: 주요 공간 (정렬된 문자열, 쉼표로 구분)
            has_pet: 반려동물 여부
            priority: 우선순위
            budget_level: 예산 범위
            
        Returns:
            매칭되는 TASTE_CONFIG 목록
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 동적 WHERE 조건 생성
                conditions = []
                params = {}
                
                if vibe:
                    conditions.append("REPRESENTATIVE_VIBE = :vibe")
                    params['vibe'] = vibe
                
                if household_size is not None:
                    conditions.append("REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size")
                    params['household_size'] = household_size
                
                if main_space is not None:
                    conditions.append("REPRESENTATIVE_MAIN_SPACE = :main_space")
                    params['main_space'] = main_space
                
                if has_pet is not None:
                    conditions.append("REPRESENTATIVE_HAS_PET = :has_pet")
                    params['has_pet'] = 'Y' if has_pet else 'N'
                
                if priority:
                    conditions.append("REPRESENTATIVE_PRIORITY = :priority")
                    params['priority'] = priority
                
                if budget_level:
                    conditions.append("REPRESENTATIVE_BUDGET_LEVEL = :budget_level")
                    params['budget_level'] = budget_level
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                query = f"""
                    SELECT 
                        TASTE_ID,
                        DESCRIPTION,
                        REPRESENTATIVE_VIBE,
                        REPRESENTATIVE_HOUSEHOLD_SIZE,
                        REPRESENTATIVE_MAIN_SPACE,
                        REPRESENTATIVE_HAS_PET,
                        REPRESENTATIVE_PRIORITY,
                        REPRESENTATIVE_BUDGET_LEVEL
                    FROM TASTE_CONFIG
                    WHERE {where_clause}
                      AND IS_ACTIVE = 'Y'
                    ORDER BY TASTE_ID
                """
                
                cur.execute(query, params)
                cols = [c[0] for c in cur.description]
                results = []
                
                for row in cur.fetchall():
                    result_dict = dict(zip(cols, row))
                    # HAS_PET 변환 ('Y'/'N' → boolean)
                    if result_dict.get('REPRESENTATIVE_HAS_PET') is not None:
                        result_dict['REPRESENTATIVE_HAS_PET'] = result_dict['REPRESENTATIVE_HAS_PET'] == 'Y'
                    results.append(result_dict)
                
                return results


# 싱글톤 인스턴스
onboarding_taste_matching_service = OnboardingTasteMatchingService()

