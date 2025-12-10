"""
온보딩 데이터를 기반으로 taste를 계산하고 MEMBER 테이블에 저장하는 서비스
"""
from typing import Optional
from api.db.oracle_client import get_connection
from api.utils.taste_classifier import taste_classifier


class TasteCalculationService:
    """Taste 계산 및 저장 서비스"""
    
    @staticmethod
    def calculate_and_save_taste(member_id: str, onboarding_session_id: str = None, onboarding_data: dict = None) -> int:
        """
        온보딩 데이터로부터 taste를 계산하고 MEMBER 테이블에 저장
        
        Args:
            member_id: 회원 ID
            onboarding_session_id: 온보딩 세션 ID (선택적)
            onboarding_data: 온보딩 데이터 딕셔너리 (선택적, session_id가 있으면 DB에서 조회)
        
        Returns:
            계산된 taste_id
        """
        # 1. 온보딩 데이터 가져오기
        if onboarding_data is None:
            if onboarding_session_id:
                onboarding_data = TasteCalculationService._get_onboarding_data_from_session(onboarding_session_id)
            else:
                raise ValueError("onboarding_session_id 또는 onboarding_data가 필요합니다")
        
        # 2. taste 계산
        taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data)
        
        # 3. 검증: 1~1920 범위의 정수로 보장
        taste_id = int(taste_id)
        if taste_id < 1:
            taste_id = 1
        elif taste_id > 1920:
            taste_id = 1920
        
        # 4. MEMBER 테이블에 taste 저장 (NUMBER 타입으로 저장)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE MEMBER
                    SET TASTE = :taste_id
                    WHERE MEMBER_ID = :member_id
                """, {
                    'taste_id': taste_id,
                    'member_id': member_id
                })
                conn.commit()
        
        return taste_id
    
    @staticmethod
    def _get_onboarding_data_from_session(session_id: str) -> dict:
        """
        ONBOARDING_SESSION에서 온보딩 데이터 가져오기
        """
        from api.db.oracle_client import fetch_all_dict
        
        # ONBOARDING_SESSION 조회 (정규화 테이블 사용)
        from api.db.oracle_client import get_connection
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 기본 세션 정보 조회
                cur.execute("""
                    SELECT 
                        SESSION_ID,
                        VIBE,
                        HOUSEHOLD_SIZE,
                        HOUSING_TYPE,
                        PYUNG,
                        BUDGET_LEVEL,
                        PRIORITY,
                        HAS_PET,
                        COOKING,
                        LAUNDRY,
                        MEDIA
                    FROM ONBOARDING_SESSION
                    WHERE SESSION_ID = :session_id
                """, {'session_id': session_id})
                
                cols = [c[0] for c in cur.description]
                row = cur.fetchone()
                
                if not row:
                    raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
                
                session = dict(zip(cols, row))
                
                # ONBOARDING_SESSION 데이터를 onboarding_data 형식으로 변환
                onboarding_data = {
                    'vibe': session.get('VIBE'),
                    'household_size': session.get('HOUSEHOLD_SIZE'),
                    'housing_type': session.get('HOUSING_TYPE'),
                    'pyung': session.get('PYUNG'),
                    'budget_level': session.get('BUDGET_LEVEL'),
                    'priority': session.get('PRIORITY'),
                    'has_pet': session.get('HAS_PET') == 'Y' if session.get('HAS_PET') else False,
                }
                
                # MAIN_SPACE 정규화 테이블에서 읽기
                cur.execute("""
                    SELECT MAIN_SPACE FROM ONBOARD_SESS_MAIN_SPACES
                    WHERE SESSION_ID = :session_id
                    ORDER BY MAIN_SPACE
                """, {'session_id': session_id})
                main_spaces = [row[0] for row in cur.fetchall()]
                onboarding_data['main_space'] = main_spaces if main_spaces else []
                
                # PRIORITY_LIST 정규화 테이블에서 읽기
                cur.execute("""
                    SELECT PRIORITY FROM ONBOARD_SESS_PRIORITIES
                    WHERE SESSION_ID = :session_id
                    ORDER BY PRIORITY_ORDER
                """, {'session_id': session_id})
                priorities = [row[0] for row in cur.fetchall()]
                if priorities:
                    onboarding_data['priority'] = priorities
                else:
                    # 정규화 테이블이 비어있으면 ONBOARDING_SESSION의 PRIORITY 컬럼을 배열로 변환
                    raw_priority = session.get('PRIORITY')
                    if raw_priority:
                        onboarding_data['priority'] = [raw_priority]
                    else:
                        onboarding_data['priority'] = []
                
                # 생활 패턴 (기본 테이블에서 직접 가져오기, NULL일 경우 기본값 설정)
                onboarding_data['cooking'] = session.get('COOKING') or 'sometimes'
                onboarding_data['laundry'] = session.get('LAUNDRY') or 'weekly'
                onboarding_data['media'] = session.get('MEDIA') or 'balanced'
        
        return onboarding_data
    
    @staticmethod
    def get_taste_for_member(member_id: str) -> Optional[int]:
        """
        회원의 taste 조회
        
        Args:
            member_id: 회원 ID
        
        Returns:
            taste_id (1~1920 정수) 또는 None
        """
        from api.db.oracle_client import fetch_one
        
        result = fetch_one("""
            SELECT TASTE FROM MEMBER WHERE MEMBER_ID = :member_id
        """, {'member_id': member_id})
        
        if result and result[0] is not None:
            taste_id = int(result[0])
            # 검증: 1~1920 범위로 보장
            if taste_id < 1:
                return 1
            elif taste_id > 1920:
                return 1920
            return taste_id
        
        return None


# 싱글톤 인스턴스
taste_calculation_service = TasteCalculationService()

