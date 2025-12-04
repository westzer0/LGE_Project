"""
Taste별 MAIN CATEGORY 선택 로직

각 taste에 따라 PRODUCT 테이블의 MAIN CATEGORY를 N개 선택합니다.
"""
from typing import List, Dict
from api.utils.taste_classifier import taste_classifier


class TasteCategorySelector:
    """
    Taste별로 MAIN CATEGORY를 선택하는 클래스
    
    MAIN CATEGORY 목록:
    - TV: TV/오디오
    - KITCHEN: 주방가전
    - LIVING: 생활가전
    - AIR: 에어컨/에어케어
    - AI: AI Home
    - OBJET: LG Objet
    - SIGNATURE: LG SIGNATURE
    """
    
    # 모든 MAIN CATEGORY
    ALL_CATEGORIES = ['TV', 'KITCHEN', 'LIVING', 'AIR', 'AI', 'OBJET', 'SIGNATURE']
    
    @staticmethod
    def select_categories_for_taste(taste_id: int, onboarding_data: Dict, num_categories: int = None) -> List[str]:
        """
        Taste별로 MAIN CATEGORY를 N개 선택
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터
            num_categories: 선택할 카테고리 개수 (None이면 자동 결정)
        
        Returns:
            선택된 MAIN CATEGORY 리스트
        """
        # 1. 필수 카테고리 (항상 포함)
        essential_categories = ['TV', 'KITCHEN', 'LIVING']
        
        # 2. num_categories가 지정되지 않으면 온보딩 데이터 기반으로 결정
        if num_categories is None:
            num_categories = TasteCategorySelector._determine_num_categories(onboarding_data)
        
        # 3. 필수 카테고리 포함
        selected = essential_categories.copy()
        
        # 4. 추가 카테고리 선택 (필요한 경우)
        if num_categories > len(essential_categories):
            additional_count = num_categories - len(essential_categories)
            additional = TasteCategorySelector._select_additional_categories(
                taste_id, onboarding_data, essential_categories, additional_count
            )
            selected.extend(additional)
        
        # 5. num_categories보다 적으면 필수 카테고리만 반환
        return selected[:num_categories]
    
    @staticmethod
    def _determine_num_categories(onboarding_data: Dict) -> int:
        """
        온보딩 데이터 기반으로 카테고리 개수 결정
        
        Args:
            onboarding_data: 온보딩 데이터
        
        Returns:
            선택할 카테고리 개수 (3~7)
        """
        household_size = onboarding_data.get('household_size', 2)
        budget_level = onboarding_data.get('budget_level', 'medium')
        pyung = onboarding_data.get('pyung', 25)
        
        # 기본값: 3개 (필수 카테고리)
        num = 3
        
        # 대가족이면 +1
        if household_size >= 4:
            num += 1
        
        # 높은 예산이면 +1
        if budget_level in ['high', 'premium', 'luxury']:
            num += 1
        
        # 큰 평수면 +1
        if pyung >= 40:
            num += 1
        
        # 최대 7개로 제한
        return min(num, 7)
    
    @staticmethod
    def _select_additional_categories(
        taste_id: int,
        onboarding_data: Dict,
        already_selected: List[str],
        count: int
    ) -> List[str]:
        """
        추가 카테고리 선택
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터
            already_selected: 이미 선택된 카테고리
            count: 추가로 선택할 개수
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        available = [cat for cat in TasteCategorySelector.ALL_CATEGORIES if cat not in already_selected]
        
        if not available or count <= 0:
            return []
        
        # 온보딩 데이터 기반 우선순위 결정
        priority_order = TasteCategorySelector._get_category_priority(onboarding_data, available)
        
        # 우선순위대로 선택
        selected = []
        for cat in priority_order:
            if cat in available and len(selected) < count:
                selected.append(cat)
        
        # 부족하면 나머지 랜덤 선택
        remaining = [cat for cat in available if cat not in selected]
        while len(selected) < count and remaining:
            selected.append(remaining.pop(0))
        
        return selected[:count]
    
    @staticmethod
    def _get_category_priority(onboarding_data: Dict, available_categories: List[str]) -> List[str]:
        """
        온보딩 데이터 기반 카테고리 우선순위 결정
        
        Args:
            onboarding_data: 온보딩 데이터
            available_categories: 선택 가능한 카테고리
        
        Returns:
            우선순위가 높은 순서대로 정렬된 카테고리 리스트
        """
        priority = []
        
        # 미디어 사용이 높으면 AIR (에어컨/에어케어) 우선
        media = onboarding_data.get('media', 'balanced')
        if media in ['high', 'gaming'] and 'AIR' in available_categories:
            priority.append('AIR')
        
        # 디자인 우선순위면 OBJET, SIGNATURE 우선
        priority_list = onboarding_data.get('priority', [])
        if isinstance(priority_list, str):
            priority_list = [priority_list]
        priority_lower = [p.lower() for p in priority_list]
        
        if 'design' in priority_lower:
            if 'OBJET' in available_categories:
                priority.append('OBJET')
            if 'SIGNATURE' in available_categories:
                priority.append('SIGNATURE')
        
        # 기술 우선순위면 AI 우선
        if 'tech' in priority_lower or 'ai' in priority_lower:
            if 'AI' in available_categories:
                priority.append('AI')
        
        # 나머지 카테고리 추가
        for cat in ['AIR', 'AI', 'OBJET', 'SIGNATURE']:
            if cat in available_categories and cat not in priority:
                priority.append(cat)
        
        return priority


def get_categories_for_taste(taste_id: int, onboarding_data: Dict, num_categories: int = None) -> List[str]:
    """
    Taste별로 MAIN CATEGORY 선택
    
    Args:
        taste_id: 취향 ID
        onboarding_data: 온보딩 데이터
        num_categories: 선택할 카테고리 개수 (None이면 자동 결정)
    
    Returns:
        선택된 MAIN CATEGORY 리스트
    """
    return TasteCategorySelector.select_categories_for_taste(taste_id, onboarding_data, num_categories)

