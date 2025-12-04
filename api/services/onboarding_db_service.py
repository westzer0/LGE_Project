"""
온보딩 데이터를 Oracle DB에 저장하는 서비스
"""
import json
from datetime import datetime
from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one


class OnboardingDBService:
    """온보딩 데이터를 Oracle DB에 저장/조회하는 서비스"""
    
    @staticmethod
    def create_or_update_session(session_id, user_id=None, current_step=1, status='IN_PROGRESS', **kwargs):
        """
        온보딩 세션 생성 또는 업데이트
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID (선택적)
            current_step: 현재 단계
            status: 상태 (IN_PROGRESS, COMPLETED, ABANDONED)
            **kwargs: 추가 필드 (vibe, household_size, housing_type, pyung, priority, budget_level 등)
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 세션이 존재하는지 확인
                cur.execute("""
                    SELECT SESSION_ID FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                """, {'session_id': session_id})
                exists = cur.fetchone()
                
                # JSON 필드 처리
                selected_categories = json.dumps(kwargs.get('selected_categories', []), ensure_ascii=False)
                recommended_products = json.dumps(kwargs.get('recommended_products', []), ensure_ascii=False)
                recommendation_result = json.dumps(kwargs.get('recommendation_result', {}), ensure_ascii=False)
                
                if exists:
                    # 업데이트
                    # recommendation_result에서 추가 필드 추출
                    has_pet = None
                    main_space = None
                    cooking = None
                    laundry = None
                    media = None
                    priority_list = None
                    
                    if recommendation_result:
                        try:
                            result_dict = json.loads(recommendation_result) if isinstance(recommendation_result, str) else recommendation_result
                            has_pet = 'Y' if result_dict.get('has_pet') or result_dict.get('pet') == 'yes' else 'N'
                            main_space = json.dumps(result_dict.get('main_space', []), ensure_ascii=False) if result_dict.get('main_space') else None
                            cooking = result_dict.get('cooking')
                            laundry = result_dict.get('laundry')
                            media = result_dict.get('media')
                            priority_list = json.dumps(result_dict.get('priority', []), ensure_ascii=False) if result_dict.get('priority') else None
                        except:
                            pass
                    
                    cur.execute("""
                        UPDATE ONBOARDING_SESSION SET
                            USER_ID = :user_id,
                            CURRENT_STEP = :current_step,
                            STATUS = :status,
                            VIBE = :vibe,
                            HOUSEHOLD_SIZE = :household_size,
                            HAS_PET = :has_pet,
                            HOUSING_TYPE = :housing_type,
                            PYUNG = :pyung,
                            MAIN_SPACE = :main_space,
                            COOKING = :cooking,
                            LAUNDRY = :laundry,
                            MEDIA = :media,
                            PRIORITY = :priority,
                            PRIORITY_LIST = :priority_list,
                            BUDGET_LEVEL = :budget_level,
                            SELECTED_CATEGORIES = :selected_categories,
                            RECOMMENDED_PRODUCTS = :recommended_products,
                            RECOMMENDATION_RESULT = :recommendation_result,
                            UPDATED_AT = SYSDATE,
                            COMPLETED_AT = CASE WHEN :status = 'COMPLETED' THEN SYSDATE ELSE COMPLETED_AT END
                        WHERE SESSION_ID = :session_id
                    """, {
                        'session_id': session_id,
                        'user_id': user_id,
                        'current_step': current_step,
                        'status': status,
                        'vibe': kwargs.get('vibe'),
                        'household_size': kwargs.get('household_size'),
                        'has_pet': has_pet,
                        'housing_type': kwargs.get('housing_type'),
                        'pyung': kwargs.get('pyung'),
                        'main_space': main_space,
                        'cooking': cooking,
                        'laundry': laundry,
                        'media': media,
                        'priority': kwargs.get('priority'),
                        'priority_list': priority_list,
                        'budget_level': kwargs.get('budget_level'),
                        'selected_categories': selected_categories,
                        'recommended_products': recommended_products,
                        'recommendation_result': recommendation_result,
                    })
                else:
                    # recommendation_result에서 추가 필드 추출
                    has_pet = None
                    main_space = None
                    cooking = None
                    laundry = None
                    media = None
                    priority_list = None
                    
                    if recommendation_result:
                        try:
                            result_dict = json.loads(recommendation_result) if isinstance(recommendation_result, str) else recommendation_result
                            has_pet = 'Y' if result_dict.get('has_pet') or result_dict.get('pet') == 'yes' else 'N'
                            main_space = json.dumps(result_dict.get('main_space', []), ensure_ascii=False) if result_dict.get('main_space') else None
                            cooking = result_dict.get('cooking')
                            laundry = result_dict.get('laundry')
                            media = result_dict.get('media')
                            priority_list = json.dumps(result_dict.get('priority', []), ensure_ascii=False) if result_dict.get('priority') else None
                        except:
                            pass
                    
                    # 생성
                    cur.execute("""
                        INSERT INTO ONBOARDING_SESSION (
                            SESSION_ID, USER_ID, CURRENT_STEP, STATUS,
                            VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG, MAIN_SPACE,
                            COOKING, LAUNDRY, MEDIA,
                            PRIORITY, PRIORITY_LIST, BUDGET_LEVEL,
                            SELECTED_CATEGORIES, RECOMMENDED_PRODUCTS, RECOMMENDATION_RESULT,
                            CREATED_AT, UPDATED_AT, COMPLETED_AT
                        ) VALUES (
                            :session_id, :user_id, :current_step, :status,
                            :vibe, :household_size, :has_pet, :housing_type, :pyung, :main_space,
                            :cooking, :laundry, :media,
                            :priority, :priority_list, :budget_level,
                            :selected_categories, :recommended_products, :recommendation_result,
                            SYSDATE, SYSDATE,
                            CASE WHEN :status = 'COMPLETED' THEN SYSDATE ELSE NULL END
                        )
                    """, {
                        'session_id': session_id,
                        'user_id': user_id,
                        'current_step': current_step,
                        'status': status,
                        'vibe': kwargs.get('vibe'),
                        'household_size': kwargs.get('household_size'),
                        'has_pet': has_pet,
                        'housing_type': kwargs.get('housing_type'),
                        'pyung': kwargs.get('pyung'),
                        'main_space': main_space,
                        'cooking': cooking,
                        'laundry': laundry,
                        'media': media,
                        'priority': kwargs.get('priority'),
                        'priority_list': priority_list,
                        'budget_level': kwargs.get('budget_level'),
                        'selected_categories': selected_categories,
                        'recommended_products': recommended_products,
                        'recommendation_result': recommendation_result,
                    })
                
                conn.commit()
                return True
    
    @staticmethod
    def save_user_response(session_id, step_number, question_type, answer_value, answer_text=None, question_id=None, answer_id=None):
        """
        사용자 응답 저장
        
        Args:
            session_id: 세션 ID
            step_number: 단계 번호
            question_type: 질문 유형 (vibe, mate, pet, housing_type, main_space, pyung, cooking, laundry, media, priority, budget)
            answer_value: 선택한 값
            answer_text: 텍스트 입력 값 (평수 등)
            question_id: 질문 ID (선택적, 자동 조회)
            answer_id: 답변 ID (선택적, 자동 조회)
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # question_id가 없으면 자동 조회
                if not question_id:
                    cur.execute("""
                        SELECT QUESTION_ID FROM ONBOARDING_QUESTION
                        WHERE STEP_NUMBER = :step_number AND QUESTION_TYPE = :question_type
                        AND ROWNUM = 1
                    """, {
                        'step_number': step_number,
                        'question_type': question_type
                    })
                    result = cur.fetchone()
                    if result:
                        question_id = result[0]
                    else:
                        raise ValueError(f"Question not found: step={step_number}, type={question_type}")
                
                # answer_id가 없고 answer_value가 있으면 자동 조회
                if not answer_id and answer_value:
                    cur.execute("""
                        SELECT ANSWER_ID FROM ONBOARDING_ANSWER
                        WHERE QUESTION_ID = :question_id AND ANSWER_VALUE = :answer_value
                        AND ROWNUM = 1
                    """, {
                        'question_id': question_id,
                        'answer_value': answer_value
                    })
                    result = cur.fetchone()
                    if result:
                        answer_id = result[0]
                
                # 기존 응답이 있는지 확인 (같은 세션, 같은 질문)
                cur.execute("""
                    SELECT RESPONSE_ID FROM ONBOARDING_USER_RESPONSE
                    WHERE SESSION_ID = :session_id AND QUESTION_ID = :question_id
                    AND ROWNUM = 1
                """, {
                    'session_id': session_id,
                    'question_id': question_id
                })
                existing = cur.fetchone()
                
                if existing:
                    # 업데이트
                    cur.execute("""
                        UPDATE ONBOARDING_USER_RESPONSE SET
                            ANSWER_ID = :answer_id,
                            ANSWER_VALUE = :answer_value,
                            RESPONSE_TEXT = :response_text,
                            STEP_NUMBER = :step_number
                        WHERE RESPONSE_ID = :response_id
                    """, {
                        'response_id': existing[0],
                        'answer_id': answer_id,
                        'answer_value': answer_value,
                        'response_text': answer_text,
                        'step_number': step_number
                    })
                else:
                    # 생성
                    cur.execute("""
                        INSERT INTO ONBOARDING_USER_RESPONSE (
                            RESPONSE_ID, SESSION_ID, QUESTION_ID, ANSWER_ID,
                            ANSWER_VALUE, RESPONSE_TEXT, STEP_NUMBER, CREATED_AT
                        ) VALUES (
                            SEQ_ONBOARDING_USER_RESPONSE.NEXTVAL,
                            :session_id, :question_id, :answer_id,
                            :answer_value, :response_text, :step_number, SYSDATE
                        )
                    """, {
                        'session_id': session_id,
                        'question_id': question_id,
                        'answer_id': answer_id,
                        'answer_value': answer_value,
                        'response_text': answer_text,
                        'step_number': step_number
                    })
                
                conn.commit()
                return True
    
    @staticmethod
    def save_multiple_responses(session_id, step_number, question_type, answer_values):
        """
        다중 선택 응답 저장 (main_space, priority 등)
        
        Args:
            session_id: 세션 ID
            step_number: 단계 번호
            question_type: 질문 유형
            answer_values: 선택한 값 리스트
        """
        # 기존 응답 삭제 (같은 세션, 같은 질문 타입)
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 질문 ID 조회
                cur.execute("""
                    SELECT QUESTION_ID FROM ONBOARDING_QUESTION
                    WHERE STEP_NUMBER = :step_number AND QUESTION_TYPE = :question_type
                    AND ROWNUM = 1
                """, {
                    'step_number': step_number,
                    'question_type': question_type
                })
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Question not found: step={step_number}, type={question_type}")
                question_id = result[0]
                
                # 기존 응답 삭제
                cur.execute("""
                    DELETE FROM ONBOARDING_USER_RESPONSE
                    WHERE SESSION_ID = :session_id AND QUESTION_ID = :question_id
                """, {
                    'session_id': session_id,
                    'question_id': question_id
                })
                
                # 새 응답 저장
                for answer_value in answer_values:
                    # answer_id 조회
                    cur.execute("""
                        SELECT ANSWER_ID FROM ONBOARDING_ANSWER
                        WHERE QUESTION_ID = :question_id AND ANSWER_VALUE = :answer_value
                        AND ROWNUM = 1
                    """, {
                        'question_id': question_id,
                        'answer_value': answer_value
                    })
                    result = cur.fetchone()
                    answer_id = result[0] if result else None
                    
                    cur.execute("""
                        INSERT INTO ONBOARDING_USER_RESPONSE (
                            RESPONSE_ID, SESSION_ID, QUESTION_ID, ANSWER_ID,
                            ANSWER_VALUE, RESPONSE_TEXT, STEP_NUMBER, CREATED_AT
                        ) VALUES (
                            SEQ_ONBOARDING_USER_RESPONSE.NEXTVAL,
                            :session_id, :question_id, :answer_id,
                            :answer_value, NULL, :step_number, SYSDATE
                        )
                    """, {
                        'session_id': session_id,
                        'question_id': question_id,
                        'answer_id': answer_id,
                        'answer_value': answer_value,
                        'step_number': step_number
                    })
                
                conn.commit()
                return True
    
    @staticmethod
    def get_session(session_id):
        """
        세션 정보 조회
        """
        result = fetch_one("""
            SELECT * FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
        """, {'session_id': session_id})
        
        if not result:
            return None
        
        # 컬럼명 가져오기
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id", {'session_id': session_id})
                cols = [c[0] for c in cur.description]
                session_dict = dict(zip(cols, result))
                
                # JSON 필드 파싱
                if session_dict.get('SELECTED_CATEGORIES'):
                    try:
                        session_dict['SELECTED_CATEGORIES'] = json.loads(session_dict['SELECTED_CATEGORIES'])
                    except:
                        session_dict['SELECTED_CATEGORIES'] = []
                
                if session_dict.get('RECOMMENDED_PRODUCTS'):
                    try:
                        session_dict['RECOMMENDED_PRODUCTS'] = json.loads(session_dict['RECOMMENDED_PRODUCTS'])
                    except:
                        session_dict['RECOMMENDED_PRODUCTS'] = []
                
                if session_dict.get('RECOMMENDATION_RESULT'):
                    try:
                        session_dict['RECOMMENDATION_RESULT'] = json.loads(session_dict['RECOMMENDATION_RESULT'])
                    except:
                        session_dict['RECOMMENDATION_RESULT'] = {}
                
                return session_dict
    
    @staticmethod
    def get_user_responses(session_id, step_number=None):
        """
        사용자 응답 조회
        """
        if step_number:
            sql = """
                SELECT r.*, q.QUESTION_TYPE, q.QUESTION_TEXT, a.ANSWER_TEXT
                FROM ONBOARDING_USER_RESPONSE r
                JOIN ONBOARDING_QUESTION q ON r.QUESTION_ID = q.QUESTION_ID
                LEFT JOIN ONBOARDING_ANSWER a ON r.ANSWER_ID = a.ANSWER_ID
                WHERE r.SESSION_ID = :session_id AND r.STEP_NUMBER = :step_number
                ORDER BY r.STEP_NUMBER, q.QUESTION_ORDER
            """
            params = {'session_id': session_id, 'step_number': step_number}
        else:
            sql = """
                SELECT r.*, q.QUESTION_TYPE, q.QUESTION_TEXT, a.ANSWER_TEXT
                FROM ONBOARDING_USER_RESPONSE r
                JOIN ONBOARDING_QUESTION q ON r.QUESTION_ID = q.QUESTION_ID
                LEFT JOIN ONBOARDING_ANSWER a ON r.ANSWER_ID = a.ANSWER_ID
                WHERE r.SESSION_ID = :session_id
                ORDER BY r.STEP_NUMBER, q.QUESTION_ORDER
            """
            params = {'session_id': session_id}
        
        return fetch_all_dict(sql, params)


# 싱글톤 인스턴스
onboarding_db_service = OnboardingDBService()

