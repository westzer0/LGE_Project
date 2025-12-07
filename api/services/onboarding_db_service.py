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
                selected_categories = kwargs.get('selected_categories', [])
                recommended_products = kwargs.get('recommended_products', [])
                recommendation_result = json.dumps(kwargs.get('recommendation_result', {}), ensure_ascii=False)
                
                # 정규화 테이블용 데이터 준비
                main_spaces = kwargs.get('main_space', [])
                if isinstance(main_spaces, str):
                    try:
                        main_spaces = json.loads(main_spaces)
                    except:
                        main_spaces = [main_spaces] if main_spaces else []
                elif not isinstance(main_spaces, list):
                    main_spaces = []
                
                priority_list = kwargs.get('priority_list', [])
                if isinstance(priority_list, str):
                    try:
                        priority_list = json.loads(priority_list)
                    except:
                        priority_list = [priority_list] if priority_list else []
                elif not isinstance(priority_list, list):
                    priority_list = []
                
                if exists:
                    # 업데이트
                    # recommendation_result에서 추가 필드 추출
                    has_pet = None
                    cooking = None
                    laundry = None
                    media = None
                    
                    if recommendation_result:
                        try:
                            result_dict = json.loads(recommendation_result) if isinstance(recommendation_result, str) else recommendation_result
                            has_pet = 'Y' if result_dict.get('has_pet') or result_dict.get('pet') == 'yes' else 'N'
                            cooking = result_dict.get('cooking')
                            laundry = result_dict.get('laundry')
                            media = result_dict.get('media')
                            # main_space와 priority는 kwargs에서 가져옴
                            if not main_spaces and result_dict.get('main_space'):
                                main_spaces = result_dict.get('main_space', [])
                            if not priority_list and result_dict.get('priority'):
                                priority_list = result_dict.get('priority', [])
                        except:
                            pass
                    
                    # 기본 테이블 업데이트 (CLOB 컬럼은 NULL로 유지 - 정규화 테이블 사용)
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
                            COOKING = :cooking,
                            LAUNDRY = :laundry,
                            MEDIA = :media,
                            PRIORITY = :priority,
                            BUDGET_LEVEL = :budget_level,
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
                        'cooking': cooking,
                        'laundry': laundry,
                        'media': media,
                        'priority': kwargs.get('priority'),
                        'budget_level': kwargs.get('budget_level'),
                        'recommendation_result': recommendation_result,
                    })
                    
                    # 정규화 테이블 업데이트
                    # MAIN_SPACE
                    cur.execute("DELETE FROM ONBOARD_SESS_MAIN_SPACES WHERE SESSION_ID = :session_id", {'session_id': session_id})
                    for space in main_spaces:
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_MAIN_SPACES (SESSION_ID, MAIN_SPACE)
                            VALUES (:session_id, :main_space)
                        """, {'session_id': session_id, 'main_space': str(space)})
                    
                    # PRIORITY_LIST
                    cur.execute("DELETE FROM ONBOARD_SESS_PRIORITIES WHERE SESSION_ID = :session_id", {'session_id': session_id})
                    for idx, priority in enumerate(priority_list, start=1):
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_PRIORITIES (SESSION_ID, PRIORITY, PRIORITY_ORDER)
                            VALUES (:session_id, :priority, :priority_order)
                        """, {'session_id': session_id, 'priority': str(priority), 'priority_order': idx})
                    
                    # SELECTED_CATEGORIES
                    cur.execute("DELETE FROM ONBOARD_SESS_CATEGORIES WHERE SESSION_ID = :session_id", {'session_id': session_id})
                    for category in selected_categories:
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_CATEGORIES (SESSION_ID, CATEGORY_NAME)
                            VALUES (:session_id, :category_name)
                        """, {'session_id': session_id, 'category_name': str(category)})
                    
                    # RECOMMENDED_PRODUCTS
                    cur.execute("DELETE FROM ONBOARD_SESS_REC_PRODUCTS WHERE SESSION_ID = :session_id", {'session_id': session_id})
                    for idx, product_id in enumerate(recommended_products, start=1):
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_REC_PRODUCTS (SESSION_ID, PRODUCT_ID, RANK_ORDER)
                            VALUES (:session_id, :product_id, :rank_order)
                        """, {'session_id': session_id, 'product_id': int(product_id), 'rank_order': idx})
                else:
                    # recommendation_result에서 추가 필드 추출
                    has_pet = None
                    cooking = None
                    laundry = None
                    media = None
                    
                    if recommendation_result:
                        try:
                            result_dict = json.loads(recommendation_result) if isinstance(recommendation_result, str) else recommendation_result
                            has_pet = 'Y' if result_dict.get('has_pet') or result_dict.get('pet') == 'yes' else 'N'
                            cooking = result_dict.get('cooking')
                            laundry = result_dict.get('laundry')
                            media = result_dict.get('media')
                            # main_space와 priority는 kwargs에서 가져옴
                            if not main_spaces and result_dict.get('main_space'):
                                main_spaces = result_dict.get('main_space', [])
                            if not priority_list and result_dict.get('priority'):
                                priority_list = result_dict.get('priority', [])
                        except:
                            pass
                    
                    # 기본 테이블 생성 (CLOB 컬럼은 NULL - 정규화 테이블 사용)
                    cur.execute("""
                        INSERT INTO ONBOARDING_SESSION (
                            SESSION_ID, USER_ID, CURRENT_STEP, STATUS,
                            VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG,
                            COOKING, LAUNDRY, MEDIA,
                            PRIORITY, BUDGET_LEVEL,
                            RECOMMENDATION_RESULT,
                            CREATED_AT, UPDATED_AT, COMPLETED_AT
                        ) VALUES (
                            :session_id, :user_id, :current_step, :status,
                            :vibe, :household_size, :has_pet, :housing_type, :pyung,
                            :cooking, :laundry, :media,
                            :priority, :budget_level,
                            :recommendation_result,
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
                        'cooking': cooking,
                        'laundry': laundry,
                        'media': media,
                        'priority': kwargs.get('priority'),
                        'budget_level': kwargs.get('budget_level'),
                        'recommendation_result': recommendation_result,
                    })
                    
                    # 정규화 테이블에 데이터 저장
                    # MAIN_SPACE
                    for space in main_spaces:
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_MAIN_SPACES (SESSION_ID, MAIN_SPACE)
                            VALUES (:session_id, :main_space)
                        """, {'session_id': session_id, 'main_space': str(space)})
                    
                    # PRIORITY_LIST
                    for idx, priority in enumerate(priority_list, start=1):
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_PRIORITIES (SESSION_ID, PRIORITY, PRIORITY_ORDER)
                            VALUES (:session_id, :priority, :priority_order)
                        """, {'session_id': session_id, 'priority': str(priority), 'priority_order': idx})
                    
                    # SELECTED_CATEGORIES
                    for category in selected_categories:
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_CATEGORIES (SESSION_ID, CATEGORY_NAME)
                            VALUES (:session_id, :category_name)
                        """, {'session_id': session_id, 'category_name': str(category)})
                    
                    # RECOMMENDED_PRODUCTS
                    for idx, product_id in enumerate(recommended_products, start=1):
                        cur.execute("""
                            INSERT INTO ONBOARD_SESS_REC_PRODUCTS (SESSION_ID, PRODUCT_ID, RANK_ORDER)
                            VALUES (:session_id, :product_id, :rank_order)
                        """, {'session_id': session_id, 'product_id': int(product_id), 'rank_order': idx})
                
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
        세션 정보 조회 (정규화 테이블에서 데이터 읽기)
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
                
                # 정규화 테이블에서 데이터 읽기
                # MAIN_SPACE
                cur.execute("""
                    SELECT MAIN_SPACE FROM ONBOARD_SESS_MAIN_SPACES
                    WHERE SESSION_ID = :session_id
                    ORDER BY MAIN_SPACE
                """, {'session_id': session_id})
                main_spaces = [row[0] for row in cur.fetchall()]
                session_dict['MAIN_SPACE'] = json.dumps(main_spaces, ensure_ascii=False) if main_spaces else None
                
                # PRIORITY_LIST
                cur.execute("""
                    SELECT PRIORITY FROM ONBOARD_SESS_PRIORITIES
                    WHERE SESSION_ID = :session_id
                    ORDER BY PRIORITY_ORDER
                """, {'session_id': session_id})
                priorities = [row[0] for row in cur.fetchall()]
                session_dict['PRIORITY_LIST'] = json.dumps(priorities, ensure_ascii=False) if priorities else None
                
                # SELECTED_CATEGORIES
                cur.execute("""
                    SELECT CATEGORY_NAME FROM ONBOARD_SESS_CATEGORIES
                    WHERE SESSION_ID = :session_id
                    ORDER BY CATEGORY_NAME
                """, {'session_id': session_id})
                categories = [row[0] for row in cur.fetchall()]
                session_dict['SELECTED_CATEGORIES'] = categories
                
                # RECOMMENDED_PRODUCTS
                cur.execute("""
                    SELECT PRODUCT_ID FROM ONBOARD_SESS_REC_PRODUCTS
                    WHERE SESSION_ID = :session_id
                    ORDER BY RANK_ORDER
                """, {'session_id': session_id})
                products = [row[0] for row in cur.fetchall()]
                session_dict['RECOMMENDED_PRODUCTS'] = products
                
                # RECOMMENDATION_RESULT 파싱
                if session_dict.get('RECOMMENDATION_RESULT'):
                    try:
                        rec_result = session_dict['RECOMMENDATION_RESULT']
                        if hasattr(rec_result, 'read'):
                            rec_result = rec_result.read()
                        session_dict['RECOMMENDATION_RESULT'] = json.loads(rec_result) if isinstance(rec_result, str) else rec_result
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

