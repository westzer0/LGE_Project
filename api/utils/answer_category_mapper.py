"""
Answer ID별 MAIN_CATEGORY 1:1 매핑 로직

각 onboarding_answer ID의 특성을 고려하여 MAIN_CATEGORY를 정렬하고 매핑합니다.
"""
from typing import List, Dict, Optional
from api.db.oracle_client import get_connection


class AnswerCategoryMapper:
    """
    Answer ID별 MAIN_CATEGORY 매핑 클래스
    
    각 answer_ID의 특성(question_type, answer_value)을 고려하여
    MAIN_CATEGORY를 정렬하고 1:1로 매핑합니다.
    """
    
    # Answer 특성별 MAIN_CATEGORY 우선순위 매핑
    ANSWER_CATEGORY_PRIORITY = {
        # vibe (분위기) 기반
        'vibe_modern': ['TV', '에어컨', '청소기', '공기청정기', '냉장고'],
        'vibe_cozy': ['냉장고', '세탁기', '에어컨', 'TV', '공기청정기'],
        'vibe_pop': ['TV', '청소기', '에어컨', '공기청정기', '냉장고'],
        'vibe_luxury': ['TV', '냉장고', '에어컨', '세탁기', '공기청정기'],
        
        # mate (가구 구성) 기반
        'mate_alone': ['TV', '냉장고', '청소기', '에어컨'],
        'mate_couple': ['TV', '냉장고', '세탁기', '에어컨', '공기청정기'],
        'mate_family_3_4': ['냉장고', '세탁기', 'TV', '에어컨', '공기청정기'],
        'mate_family_5plus': ['냉장고', '세탁기', '에어컨', 'TV', '공기청정기'],
        
        # main_space (주요 공간) 기반
        'main_space_living': ['TV', '에어컨', '공기청정기', '청소기'],
        'main_space_kitchen': ['냉장고', '전자레인지', '식기세척기', '오븐'],
        'main_space_bedroom': ['에어컨', 'TV', '공기청정기'],
        'main_space_dressing': ['세탁기', '건조기', '워시타워'],
        'main_space_study': ['TV', '에어컨', '공기청정기'],
        'main_space_all': ['TV', '냉장고', '에어컨', '세탁기', '공기청정기', '청소기'],
        
        # cooking (요리 빈도) 기반
        'cooking_rarely': ['냉장고', '전자레인지'],
        'cooking_sometimes': ['냉장고', '전자레인지', '식기세척기'],
        'cooking_often': ['냉장고', '전자레인지', '식기세척기', '오븐', '가스레인지'],
        
        # laundry (세탁 빈도) 기반
        'laundry_weekly': ['세탁기'],
        'laundry_few_times': ['세탁기', '건조기'],
        'laundry_daily': ['세탁기', '건조기', '워시타워'],
        
        # media (미디어 사용) 기반
        'media_ott': ['TV'],
        'media_gaming': ['TV'],
        'media_tv': ['TV'],
        'media_none': [],
        
        # priority (우선순위) 기반
        'priority_design': ['TV', '냉장고', '에어컨'],
        'priority_tech': ['TV', '냉장고', '에어컨', '세탁기'],
        'priority_eco': ['에어컨', '냉장고', '세탁기'],
        'priority_value': ['냉장고', '세탁기', 'TV'],
        
        # budget_level (예산) 기반
        'budget_low': ['냉장고', '세탁기', 'TV'],
        'budget_medium': ['TV', '냉장고', '에어컨', '세탁기'],
        'budget_high': ['TV', '냉장고', '에어컨', '세탁기', '공기청정기', '청소기'],
        
        # pet (반려동물) 기반
        'pet_yes': ['공기청정기', '청소기', '에어컨'],
        'pet_no': ['TV', '냉장고', '에어컨'],
    }
    
    @staticmethod
    def get_answer_ids_for_taste(taste_id: int) -> List[int]:
        """
        taste_id에 해당하는 answer_ID 리스트 조회
        
        Oracle DB의 ONBOARDING_RESPONSE를 통해
        해당 taste_id를 가진 사용자들의 answer_ID를 조회합니다.
        
        Args:
            taste_id: 취향 ID (1~120)
        
        Returns:
            answer_ID 리스트
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # MEMBER 테이블에서 taste_id로 member_id 조회
                    # ONBOARDING_USER_RESPONSE에서 answer_ID 조회
                    cur.execute("""
                        SELECT DISTINCT r.ANSWER_ID
                        FROM ONBOARDING_USER_RESPONSE r
                        JOIN ONBOARDING_SESSION s ON r.SESSION_ID = s.SESSION_ID
                        LEFT JOIN MEMBER m ON s.MEMBER_ID = m.MEMBER_ID
                        WHERE (m.TASTE = :taste_id OR s.SESSION_ID IN (
                            SELECT DISTINCT s2.SESSION_ID
                            FROM ONBOARDING_SESSION s2
                            JOIN MEMBER m2 ON s2.MEMBER_ID = m2.MEMBER_ID
                            WHERE m2.TASTE = :taste_id
                        ))
                          AND r.ANSWER_ID IS NOT NULL
                        ORDER BY r.ANSWER_ID
                    """, {'taste_id': taste_id})
                    results = cur.fetchall()
                    return [int(row[0]) for row in results if row[0] is not None]
        except Exception as e:
            print(f"[AnswerCategoryMapper] Oracle DB 조회 실패: {e}")
            # Fallback: onboarding_data 기반으로 answer_ID 추정
            return []
    
    @staticmethod
    def get_answer_info(answer_id: int) -> Optional[Dict]:
        """
        answer_ID의 정보 조회 (question_type, answer_value 등)
        
        Args:
            answer_id: 답변 ID
        
        Returns:
            answer 정보 딕셔너리 (question_type, answer_value, answer_text)
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT a.ANSWER_ID, a.ANSWER_VALUE, a.ANSWER_TEXT, q.QUESTION_TYPE
                        FROM ONBOARDING_ANSWER a
                        JOIN ONBOARDING_QUESTION q ON a.QUESTION_ID = q.QUESTION_ID
                        WHERE a.ANSWER_ID = :answer_id
                    """, {'answer_id': answer_id})
                    result = cur.fetchone()
                    if result:
                        return {
                            'answer_id': result[0],
                            'answer_value': result[1],
                            'answer_text': result[2],
                            'question_type': result[3]
                        }
        except Exception as e:
            print(f"[AnswerCategoryMapper] Answer 정보 조회 실패: {e}")
        return None
    
    @staticmethod
    def get_categories_for_answer(answer_id: int) -> List[str]:
        """
        answer_ID에 1:1로 매핑된 MAIN_CATEGORY 리스트 반환
        
        Args:
            answer_id: 답변 ID
        
        Returns:
            MAIN_CATEGORY 리스트 (정렬된 우선순위)
        """
        answer_info = AnswerCategoryMapper.get_answer_info(answer_id)
        if not answer_info:
            return []
        
        question_type = answer_info.get('question_type', '')
        answer_value = answer_info.get('answer_value', '')
        
        # question_type과 answer_value를 조합하여 키 생성
        key = f"{question_type}_{answer_value}"
        
        # 우선순위 매핑에서 카테고리 가져오기
        categories = AnswerCategoryMapper.ANSWER_CATEGORY_PRIORITY.get(key, [])
        
        # 매핑이 없으면 question_type만으로 시도
        if not categories:
            type_key = f"{question_type}_*"
            # question_type별 기본 카테고리
            type_defaults = {
                'vibe': ['TV', '냉장고', '에어컨'],
                'mate': ['냉장고', '세탁기', 'TV'],
                'main_space': ['TV', '냉장고', '에어컨'],
                'cooking': ['냉장고', '전자레인지'],
                'laundry': ['세탁기'],
                'media': ['TV'],
                'priority': ['TV', '냉장고', '에어컨'],
                'budget_level': ['냉장고', '세탁기', 'TV'],
                'pet': ['공기청정기', '청소기'],
            }
            categories = type_defaults.get(question_type, [])
        
        # 실제 존재하는 카테고리만 필터링
        from api.utils.taste_category_selector import TasteCategorySelector
        available_categories = TasteCategorySelector.get_available_categories()
        categories = [cat for cat in categories if cat in available_categories]
        
        return categories
    
    @staticmethod
    def get_answer_ids_from_onboarding_data(onboarding_data: Dict) -> List[Dict]:
        """
        onboarding_data에서 answer_ID 추정
        (Oracle DB가 없을 때 사용)
        
        Args:
            onboarding_data: 온보딩 데이터
        
        Returns:
            answer 정보 리스트 (question_type, answer_value 포함)
        """
        answers = []
        
        # vibe
        if 'vibe' in onboarding_data:
            answers.append({
                'question_type': 'vibe',
                'answer_value': onboarding_data['vibe']
            })
        
        # mate (household_size 기반)
        if 'household_size' in onboarding_data:
            size = onboarding_data['household_size']
            if size == 1:
                answers.append({'question_type': 'mate', 'answer_value': 'alone'})
            elif size == 2:
                answers.append({'question_type': 'mate', 'answer_value': 'couple'})
            elif 3 <= size <= 4:
                answers.append({'question_type': 'mate', 'answer_value': 'family_3_4'})
            elif size >= 5:
                answers.append({'question_type': 'mate', 'answer_value': 'family_5plus'})
        
        # pet
        has_pet = onboarding_data.get('has_pet', False) or onboarding_data.get('pet', False)
        answers.append({
            'question_type': 'pet',
            'answer_value': 'yes' if has_pet else 'no'
        })
        
        # main_space
        main_space = onboarding_data.get('main_space', 'living')
        if isinstance(main_space, list):
            for space in main_space:
                answers.append({'question_type': 'main_space', 'answer_value': space})
        else:
            answers.append({'question_type': 'main_space', 'answer_value': main_space})
        
        # cooking
        if 'cooking' in onboarding_data:
            answers.append({
                'question_type': 'cooking',
                'answer_value': onboarding_data['cooking']
            })
        
        # laundry
        if 'laundry' in onboarding_data:
            answers.append({
                'question_type': 'laundry',
                'answer_value': onboarding_data['laundry']
            })
        
        # media
        if 'media' in onboarding_data:
            answers.append({
                'question_type': 'media',
                'answer_value': onboarding_data['media']
            })
        
        # priority
        priority = onboarding_data.get('priority', 'value')
        if isinstance(priority, list):
            for p in priority:
                answers.append({'question_type': 'priority', 'answer_value': p})
        else:
            answers.append({'question_type': 'priority', 'answer_value': priority})
        
        # budget_level
        if 'budget_level' in onboarding_data:
            answers.append({
                'question_type': 'budget_level',
                'answer_value': onboarding_data['budget_level']
            })
        
        return answers
    
    @staticmethod
    def get_categories_for_taste(taste_id: int, onboarding_data: Dict = None) -> List[str]:
        """
        taste_id에 해당하는 모든 answer_ID의 MAIN_CATEGORY를 수집하고 정렬
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터 (필수, answer_ID 추정용)
        
        Returns:
            정렬된 MAIN_CATEGORY 리스트 (중복 제거, 우선순위 정렬)
        """
        # 1. Oracle DB에서 answer_ID 조회 시도
        answer_ids = AnswerCategoryMapper.get_answer_ids_for_taste(taste_id)
        
        all_categories = []
        category_weights = {}  # 카테고리별 가중치 (나타난 횟수)
        
        # 2-1. Oracle DB에서 answer_ID를 가져온 경우
        if answer_ids:
            for answer_id in answer_ids:
                categories = AnswerCategoryMapper.get_categories_for_answer(answer_id)
                for cat in categories:
                    all_categories.append(cat)
                    category_weights[cat] = category_weights.get(cat, 0) + 1
        
        # 2-2. Oracle DB가 없거나 answer_ID가 없으면 onboarding_data에서 추정
        if not answer_ids and onboarding_data:
            answer_infos = AnswerCategoryMapper.get_answer_ids_from_onboarding_data(onboarding_data)
            from api.utils.taste_category_selector import TasteCategorySelector
            available_categories = TasteCategorySelector.get_available_categories()
            
            for answer_info in answer_infos:
                question_type = answer_info.get('question_type', '')
                answer_value = answer_info.get('answer_value', '')
                
                # question_type과 answer_value를 조합하여 키 생성
                key = f"{question_type}_{answer_value}"
                
                # 우선순위 매핑에서 카테고리 가져오기
                categories = AnswerCategoryMapper.ANSWER_CATEGORY_PRIORITY.get(key, [])
                
                # 매핑이 없으면 question_type만으로 시도
                if not categories:
                    type_defaults = {
                        'vibe': ['TV', '냉장고', '에어컨', '공기청정기', '청소기', '세탁기'],
                        'mate': ['냉장고', '세탁기', 'TV', '에어컨', '공기청정기', '청소기'],
                        'main_space': ['TV', '냉장고', '에어컨', '공기청정기', '청소기', '세탁기'],
                        'cooking': ['냉장고', '전자레인지', '식기세척기', '오븐'],
                        'laundry': ['세탁기', '건조기', '워시타워'],
                        'media': ['TV', '에어컨', '공기청정기'],
                        'priority': ['TV', '냉장고', '에어컨', '세탁기', '공기청정기', '청소기'],
                        'budget_level': ['냉장고', '세탁기', 'TV', '에어컨', '공기청정기', '청소기', '식기세척기'],
                        'pet': ['공기청정기', '청소기', '에어컨', 'TV'],
                    }
                    categories = type_defaults.get(question_type, [])
                
                # 실제 존재하는 카테고리만 필터링
                categories = [cat for cat in categories if cat in available_categories]
                
                for cat in categories:
                    all_categories.append(cat)
                    category_weights[cat] = category_weights.get(cat, 0) + 1
            
            # 추가: 모든 사용 가능한 카테고리도 가중치를 낮춰서 추가 (다양성 확보)
            # 이미 선택된 카테고리가 적으면 더 많은 카테고리 추가
            if len(set(all_categories)) < 5:
                for cat in available_categories:
                    if cat not in all_categories:
                        all_categories.append(cat)
                        category_weights[cat] = category_weights.get(cat, 0) + 0.1  # 낮은 가중치
        
        # 3. 가중치 기준으로 정렬 (자주 나타난 카테고리가 우선)
        sorted_categories = sorted(
            set(all_categories),
            key=lambda x: (-category_weights.get(x, 0), x)  # 가중치 내림차순, 이름 오름차순
        )
        
        # 4. 결과가 없으면 onboarding_data 기반 fallback
        if not sorted_categories and onboarding_data:
            from api.utils.taste_category_selector import TasteCategorySelector
            sorted_categories = TasteCategorySelector._select_categories_by_onboarding(onboarding_data)
        
        # 5. 카테고리가 적으면 onboarding_data 기반으로 추가 카테고리 확보
        if onboarding_data and len(sorted_categories) < 8:
            from api.utils.taste_category_selector import TasteCategorySelector
            additional_categories = TasteCategorySelector._select_categories_by_onboarding(onboarding_data)
            for cat in additional_categories:
                if cat not in sorted_categories:
                    sorted_categories.append(cat)
                    if len(sorted_categories) >= 10:  # 최대 10개까지
                        break
        
        return sorted_categories


# 싱글톤 인스턴스
answer_category_mapper = AnswerCategoryMapper()

