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
        
        # 3. MEMBER 테이블에 taste 저장
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
        
        # ONBOARDING_SESSION 조회
        sessions = fetch_all_dict("""
            SELECT 
                SESSION_ID,
                VIBE,
                HOUSEHOLD_SIZE,
                HOUSING_TYPE,
                PYUNG,
                BUDGET_LEVEL,
                PRIORITY,
                HAS_PET,
                MAIN_SPACE,
                COOKING,
                LAUNDRY,
                MEDIA,
                RECOMMENDATION_RESULT
            FROM ONBOARDING_SESSION
            WHERE SESSION_ID = :session_id
        """, {'session_id': session_id})
        
        if not sessions:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        session = sessions[0]
        
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
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
        
        # MAIN_SPACE 파싱
        main_space = session.get('MAIN_SPACE')
        if main_space:
            import json
            try:
                if isinstance(main_space, str):
                    main_space = json.loads(main_space)
                onboarding_data['main_space'] = main_space if isinstance(main_space, list) else [main_space]
            except:
                onboarding_data['main_space'] = []
        else:
            onboarding_data['main_space'] = []
        
        # 생활 패턴
        onboarding_data['cooking'] = session.get('COOKING', 'sometimes')
        onboarding_data['laundry'] = session.get('LAUNDRY', 'weekly')
        onboarding_data['media'] = session.get('MEDIA', 'balanced')
        
        # RECOMMENDATION_RESULT에서 추가 데이터 추출
        recommendation_result = session.get('RECOMMENDATION_RESULT', {})
        if isinstance(recommendation_result, str):
            import json
            try:
                recommendation_result = json.loads(recommendation_result)
            except:
                recommendation_result = {}
        
        if recommendation_result:
            onboarding_data['cooking'] = recommendation_result.get('cooking', onboarding_data.get('cooking', 'sometimes'))
            onboarding_data['laundry'] = recommendation_result.get('laundry', onboarding_data.get('laundry', 'weekly'))
            onboarding_data['media'] = recommendation_result.get('media', onboarding_data.get('media', 'balanced'))
            onboarding_data['main_space'] = recommendation_result.get('main_space', onboarding_data.get('main_space', []))
            onboarding_data['has_pet'] = recommendation_result.get('has_pet', onboarding_data.get('has_pet', False))
            onboarding_data['priority'] = recommendation_result.get('priority', onboarding_data.get('priority', ['value']))
        
        return onboarding_data
    
    @staticmethod
    def get_taste_for_member(member_id: str) -> Optional[int]:
        """
        회원의 taste 조회
        
        Args:
            member_id: 회원 ID
        
        Returns:
            taste_id 또는 None
        """
        from api.db.oracle_client import fetch_one
        
        result = fetch_one("""
            SELECT TASTE FROM MEMBER WHERE MEMBER_ID = :member_id
        """, {'member_id': member_id})
        
        return result[0] if result and result[0] else None


# 싱글톤 인스턴스
taste_calculation_service = TasteCalculationService()

