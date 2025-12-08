"""
Ill-suited Category Detection Logic

온보딩 세션 답변을 분석하여 완전히 부적합한 카테고리를 판별하는 모듈.
0점을 받아야 하는 카테고리들을 식별합니다.
"""
from typing import List, Dict, Set


class IllSuitedCategoryDetector:
    """
    온보딩 세션 답변 기반으로 ill-suited 카테고리를 판별하는 클래스
    
    Ill-suited란 onboarding_session 답변에 완전 반대되는 제품들을 의미합니다.
    예: 반려동물을 키운다고 답변 -> 반려동물 전용 제품은 ill-suited가 될 수 없음
        반려동물을 키우지 않는다고 답변 -> 반려동물 전용 제품은 ill-suited
    """
    
    @staticmethod
    def detect_ill_suited_categories(onboarding_data: Dict, all_categories: List[str]) -> List[str]:
        """
        온보딩 데이터를 분석하여 ill-suited 카테고리 리스트 반환
        
        Args:
            onboarding_data: 온보딩 세션 데이터
                - has_pet: 반려동물 여부 (bool)
                - household_size: 가구 인원수 (int)
                - housing_type: 주거 형태 (str)
                - pyung: 평수 (int)
                - main_space: 주요 공간 (str)
                - cooking: 요리 빈도 (str)
                - laundry: 세탁 빈도 (str)
                - media: 미디어 사용 패턴 (str)
                - vibe: 인테리어 무드 (str)
                - priority: 우선순위 (str)
                - budget_level: 예산 수준 (str)
            all_categories: 모든 사용 가능한 카테고리 리스트
        
        Returns:
            ill-suited 카테고리 리스트 (완전히 부적합한 카테고리들)
        """
        ill_suited = []
        
        has_pet = onboarding_data.get('has_pet', False) or onboarding_data.get('pet', False)
        household_size = onboarding_data.get('household_size', 2)
        housing_type = onboarding_data.get('housing_type', 'apartment')
        pyung = onboarding_data.get('pyung', 25)
        main_space = onboarding_data.get('main_space', 'living')
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        vibe = onboarding_data.get('vibe', 'modern')
        
        # 1. 반려동물 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_pet_related(has_pet, all_categories)
        )
        
        # 2. 가구 수 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_household_size(household_size, all_categories)
        )
        
        # 3. 주거 형태 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_housing_type(housing_type, pyung, all_categories)
        )
        
        # 4. 주요 공간 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_main_space(main_space, all_categories)
        )
        
        # 5. 생활 패턴 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_lifestyle(cooking, laundry, media, all_categories)
        )
        
        # 6. 인테리어 무드 관련 ill-suited 판별
        ill_suited.extend(
            IllSuitedCategoryDetector._check_vibe(vibe, all_categories)
        )
        
        # 중복 제거 및 정렬
        return sorted(list(set(ill_suited)))
    
    @staticmethod
    def _check_pet_related(has_pet: bool, all_categories: List[str]) -> List[str]:
        """
        반려동물 관련 ill-suited 카테고리 판별
        
        Logic:
        - 반려동물을 키우지 않는다면 (has_pet=False): 반려동물 전용 제품은 ill-suited
        - 반려동물을 키운다면: 반려동물 관련 제품은 적합 (ill-suited 아님)
        """
        ill_suited = []
        
        # 반려동물 전용 카테고리 (실제로는 카테고리가 아닐 수 있지만, 
        # 만약 있다면 예시로 추가)
        pet_specific_keywords = ['반려동물', '펫', 'pet']
        
        # 일반적으로 반려동물이 없으면 특정 카테고리가 필요 없을 수 있음
        # 하지만 실제 카테고리명에 따라 다를 수 있으므로 여기서는 보수적으로 접근
        if not has_pet:
            # 반려동물 관련 제품이 별도 카테고리로 존재한다면 ill-suited
            for category in all_categories:
                category_lower = category.lower()
                if any(keyword in category_lower for keyword in pet_specific_keywords):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def _check_household_size(household_size: int, all_categories: List[str]) -> List[str]:
        """
        가구 수 관련 ill-suited 카테고리 판별
        
        Logic:
        - 1인 가구: 대형 가전(김치냉장고, 워시타워 등)은 ill-suited
        - 5인 이상 가구: 미니 가전(미니냉장고, 미니세탁기 등)은 ill-suited
        """
        ill_suited = []
        
        if household_size == 1:
            # 1인 가구: 대형/프리미엄 가전은 ill-suited
            large_categories = ['김치냉장고', '워시타워', '대형냉장고', '대형세탁기']
            for category in all_categories:
                if any(large in category for large in large_categories):
                    ill_suited.append(category)
        
        elif household_size >= 5:
            # 5인 이상 가구: 미니 가전은 ill-suited
            mini_categories = ['미니냉장고', '미니세탁기', '미니세탁']
            for category in all_categories:
                if any(mini in category for mini in mini_categories):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def _check_housing_type(housing_type: str, pyung: int, all_categories: List[str]) -> List[str]:
        """
        주거 형태 및 평수 관련 ill-suited 카테고리 판별
        
        Logic:
        - 원룸/오피스텔 + 작은 평수: 대형 가전, 건조기, 식기세척기 등은 ill-suited
        - 단독주택: 특정 공용 가전은 적합하지 않을 수 있음
        """
        ill_suited = []
        
        # 원룸/오피스텔 + 20평 이하: 대형 가전은 ill-suited
        if housing_type in ['studio', 'officetel', '원룸', '오피스텔'] and pyung <= 20:
            large_space_categories = [
                '김치냉장고', '워시타워', '건조기', '식기세척기',
                '대형냉장고', '대형TV', '프로젝터'
            ]
            for category in all_categories:
                if any(large in category for large in large_space_categories):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def _check_main_space(main_space: str, all_categories: List[str]) -> List[str]:
        """
        주요 공간 관련 ill-suited 카테고리 판별
        
        Logic:
        - 주방이 주요 공간이 아니면: 주방 전용 가전(식기세척기, 전자레인지 등)은 ill-suited
        - 세탁실이 주요 공간이 아니면: 세탁 전용 가전(건조기, 워시타워 등)은 ill-suited
        """
        ill_suited = []
        
        main_space_lower = str(main_space).lower()
        
        # 주방이 주요 공간이 아닐 때
        if 'kitchen' not in main_space_lower and '주방' not in main_space_lower:
            kitchen_categories = ['식기세척기', '전자레인지', '오븐', '김치냉장고']
            for category in all_categories:
                if any(kitchen in category for kitchen in kitchen_categories):
                    ill_suited.append(category)
        
        # 세탁실/베란다가 주요 공간이 아닐 때
        if 'laundry' not in main_space_lower and '세탁' not in main_space_lower and '베란다' not in main_space_lower:
            laundry_categories = ['건조기', '워시타워', '의류관리기']
            for category in all_categories:
                if any(laundry in category for laundry in laundry_categories):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def _check_lifestyle(cooking: str, laundry: str, media: str, all_categories: List[str]) -> List[str]:
        """
        생활 패턴 관련 ill-suited 카테고리 판별
        
        Logic:
        - 요리를 전혀 안 하면: 주방 가전(식기세척기, 오븐 등)은 ill-suited
        - 세탁을 거의 안 하면: 세탁 가전(건조기, 워시타워 등)은 ill-suited
        - 미디어를 전혀 안 보면: TV, 프로젝터 등은 ill-suited
        """
        ill_suited = []
        
        cooking_lower = str(cooking).lower()
        laundry_lower = str(laundry).lower()
        media_lower = str(media).lower()
        
        # 요리를 전혀 안 함
        if cooking_lower in ['rarely', 'never', '전혀', '안함', '없음']:
            cooking_categories = ['식기세척기', '오븐', '전자레인지']
            for category in all_categories:
                if any(cook in category for cook in cooking_categories):
                    ill_suited.append(category)
        
        # 세탁을 거의 안 함
        if laundry_lower in ['rarely', 'never', '거의안함', '전혀', '없음']:
            laundry_categories = ['건조기', '워시타워', '의류관리기']
            for category in all_categories:
                if any(laund in category for laund in laundry_categories):
                    ill_suited.append(category)
        
        # 미디어를 전혀 안 봄
        if media_lower in ['none', 'minimal', '없음', '안봄']:
            media_categories = ['TV', '프로젝터', '스탠바이미', '오디오', '사운드바']
            for category in all_categories:
                if any(med in category for med in media_categories):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def _check_vibe(vibe: str, all_categories: List[str]) -> List[str]:
        """
        인테리어 무드 관련 ill-suited 카테고리 판별
        
        Logic:
        - 모던/심플 무드: 오버스타일된 제품은 ill-suited
        - 럭셔리 무드: 저가형 제품은 ill-suited
        - 팝/생기있는 무드: 너무 심플한 제품은 ill-suited
        """
        ill_suited = []
        
        vibe_lower = str(vibe).lower()
        
        # 모던/심플 무드: 오버스타일 제품은 ill-suited
        if vibe_lower in ['modern', '모던', '심플']:
            # 실제로는 카테고리명에 오버스타일이 드러나지 않을 수 있음
            # 여기서는 보수적으로 접근
            pass
        
        # 럭셔리 무드: 저가형 제품은 ill-suited
        if vibe_lower in ['luxury', '럭셔리', '고급']:
            budget_categories = ['미니냉장고', '미니세탁기']  # 저가형으로 간주
            for category in all_categories:
                if any(budget in category for budget in budget_categories):
                    ill_suited.append(category)
        
        return ill_suited
    
    @staticmethod
    def get_ill_suited_reason(category: str, onboarding_data: Dict) -> str:
        """
        특정 카테고리가 ill-suited인 이유를 반환
        
        Args:
            category: 카테고리명
            onboarding_data: 온보딩 데이터
        
        Returns:
            ill-suited 이유 설명
        """
        reasons = []
        
        has_pet = onboarding_data.get('has_pet', False)
        household_size = onboarding_data.get('household_size', 2)
        housing_type = onboarding_data.get('housing_type', 'apartment')
        pyung = onboarding_data.get('pyung', 25)
        main_space = onboarding_data.get('main_space', 'living')
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        category_lower = category.lower()
        
        # 반려동물 관련
        if '반려동물' in category_lower or '펫' in category_lower:
            if not has_pet:
                reasons.append("반려동물을 키우지 않으므로 불필요")
        
        # 가구 수 관련
        if household_size == 1 and ('대형' in category_lower or '김치냉장고' in category_lower or '워시타워' in category_lower):
            reasons.append("1인 가구에 비해 과도하게 큰 제품")
        
        if household_size >= 5 and '미니' in category_lower:
            reasons.append("대가족에 비해 용량이 부족한 제품")
        
        # 주거 형태/평수 관련
        if housing_type in ['studio', 'officetel'] and pyung <= 20:
            if '대형' in category_lower or '건조기' in category_lower or '식기세척기' in category_lower:
                reasons.append("작은 평수에 설치하기 어려운 제품")
        
        # 주요 공간 관련
        main_space_lower = str(main_space).lower()
        if 'kitchen' not in main_space_lower and '주방' not in main_space_lower:
            if '식기세척기' in category_lower or '전자레인지' in category_lower:
                reasons.append("주방이 주요 공간이 아니므로 불필요")
        
        if 'laundry' not in main_space_lower and '세탁' not in main_space_lower:
            if '건조기' in category_lower or '워시타워' in category_lower:
                reasons.append("세탁실이 주요 공간이 아니므로 불필요")
        
        # 생활 패턴 관련
        cooking_lower = str(cooking).lower()
        if cooking_lower in ['rarely', 'never', '전혀']:
            if '식기세척기' in category_lower or '오븐' in category_lower:
                reasons.append("요리를 거의 하지 않으므로 불필요")
        
        laundry_lower = str(laundry).lower()
        if laundry_lower in ['rarely', 'never', '거의안함']:
            if '건조기' in category_lower or '워시타워' in category_lower:
                reasons.append("세탁을 거의 하지 않으므로 불필요")
        
        media_lower = str(media).lower()
        if media_lower in ['none', 'minimal', '없음']:
            if 'TV' in category_lower or '프로젝터' in category_lower:
                reasons.append("미디어를 거의 사용하지 않으므로 불필요")
        
        return "; ".join(reasons) if reasons else "온보딩 답변과 부적합한 카테고리"



