"""
온보딩 데이터를 기반으로 taste를 분류하는 유틸리티 (가중치 기반)

Question별 중요도를 고려하여 100개 이하의 taste로 그룹화합니다.
"""
import hashlib
import json
from typing import Dict, Optional, List


class WeightedTasteClassifier:
    """
    Question별 중요도를 고려한 taste 분류기
    
    전략:
    1. 중요도가 높은 질문은 세밀하게 구분
    2. 중요도가 낮은 질문은 그룹화
    3. 최종적으로 100개 이하의 taste로 분류
    """
    
    # Question별 중요도 (1.0 = 최고 중요도, 0.0 = 무시)
    # 사용자 논리: 주요공간 > 주거형태 > 예산 > 가족구성 > 인테리어스타일 > 생활패턴
    QUESTION_WEIGHTS = {
        'main_space': 1.0,         # 주요 공간 - 최고 중요 (어떤 공간에 설치할지가 제품 선택의 핵심)
        'housing_type': 0.9,       # 주거 형태 - 매우 중요 (아파트/주택/원룸에 따라 제품 크기/타입 결정)
        'budget': 0.8,             # 예산 - 중요 (실제 구매 가능한 제품 범위 결정)
        'mate': 0.7,               # 가족 구성 - 중상 중요도 (용량/기능 선택에 영향)
        'vibe': 0.6,               # 인테리어 스타일 - 중간 중요도 (디자인 선호도)
        'priority': 0.5,           # 우선순위 - 중간 중요도
        'pet': 0.4,                # 반려동물 - 낮은 중요도
        'cooking': 0.2,            # 요리 빈도 - 매우 낮은 중요도 (생활패턴)
        'laundry': 0.2,            # 세탁 빈도 - 매우 낮은 중요도 (생활패턴)
        'media': 0.2,              # 미디어 사용 - 매우 낮은 중요도 (생활패턴)
    }
    
    # 목표 taste 개수
    TARGET_TASTE_COUNT = 80
    
    @staticmethod
    def calculate_taste_from_onboarding(onboarding_data: Dict) -> int:
        """
        온보딩 데이터로부터 taste_id 계산 (가중치 기반)
        
        Args:
            onboarding_data: 온보딩 데이터 딕셔너리
        
        Returns:
            taste_id (1 ~ TARGET_TASTE_COUNT)
        """
        # 1. 주요 속성 추출 및 정규화
        vibe = onboarding_data.get('vibe', 'modern')
        household_size = onboarding_data.get('household_size', 2)
        housing_type = onboarding_data.get('housing_type', 'apartment')
        pyung = onboarding_data.get('pyung', 25)
        budget_level = onboarding_data.get('budget_level', 'medium')
        priority = onboarding_data.get('priority', ['value'])
        has_pet = onboarding_data.get('has_pet', False)
        
        # main_space 정규화
        main_space = onboarding_data.get('main_space', [])
        if isinstance(main_space, str):
            main_space = [main_space]
        main_space_str = ','.join(sorted(main_space)) if main_space else 'none'
        
        # priority 정규화
        if isinstance(priority, str):
            priority = [priority]
        priority_str = ','.join(sorted(priority)) if priority else 'value'
        
        # 생활 패턴 정규화
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        # 2. 중요도 기반 정규화
        # 중요도가 낮은 질문은 그룹화하여 구분을 줄임
        
        # housing_type: 중요도 낮음 - 4개를 2개로 그룹화
        housing_group = WeightedTasteClassifier._group_housing_type(housing_type)
        
        # main_space: 중요도 중간 - 복잡한 조합을 단순화
        main_space_group = WeightedTasteClassifier._group_main_space(main_space)
        
        # priority: 중요도 높음 - 첫 번째 우선순위만 사용
        primary_priority = priority[0] if priority else 'value'
        
        # 생활 패턴: 중요도 매우 낮음 - 그룹화
        lifestyle_group = WeightedTasteClassifier._group_lifestyle(cooking, laundry, media)
        
        # 3. 가중치 기반 Taste 키 생성
        # 중요도 순서: main_space > housing_type > budget > mate > vibe > priority > pet > lifestyle
        # 중요도가 높은 속성은 세밀하게, 낮은 속성은 그룹화된 값 사용
        taste_key_parts = [
            main_space_group,              # 1.0 - 최고 중요도 (세밀하게 구분)
            housing_type,                  # 0.9 - 매우 중요 (원본 값 사용, 세밀하게)
            WeightedTasteClassifier._normalize_budget_level(budget_level),  # 0.8 - 중요 (3가지)
            WeightedTasteClassifier._normalize_household_size(household_size),  # 0.7 - 중상 (4가지)
            vibe,                          # 0.6 - 중간 (4가지)
            primary_priority,              # 0.5 - 중간 (4가지)
            'pet' if has_pet else 'no_pet',  # 0.4 - 낮음 (2가지)
            lifestyle_group,               # 0.2 - 매우 낮음 (그룹화됨)
        ]
        
        taste_key = '|'.join(str(p) for p in taste_key_parts)
        
        # 4. 해시 기반 taste_id 생성
        taste_hash = int(hashlib.md5(taste_key.encode('utf-8')).hexdigest(), 16)
        taste_id = (taste_hash % WeightedTasteClassifier.TARGET_TASTE_COUNT) + 1
        
        return taste_id
    
    @staticmethod
    def _group_housing_type(housing_type: str) -> str:
        """주거 형태는 중요도가 높으므로 그룹화하지 않고 원본 값 사용"""
        # 중요도가 높으므로 원본 값 그대로 사용
        return housing_type
    
    @staticmethod
    def _group_main_space(main_space: List[str]) -> str:
        """주요 공간 처리 (최고 중요도이므로 세밀하게 구분)"""
        if not main_space or main_space == ['none']:
            return 'none'
        
        # 'all'이 포함되면 'all'
        if 'all' in main_space:
            return 'all'
        
        # 중요도가 높으므로 정렬된 조합으로 세밀하게 구분
        # 예: ['kitchen', 'living'] vs ['kitchen'] vs ['living'] 모두 다르게 구분
        return ','.join(sorted(main_space))
    
    @staticmethod
    def _group_lifestyle(cooking: str, laundry: str, media: str) -> str:
        """생활 패턴 그룹화 (3개 속성을 1개로)"""
        # 요리: 자주 vs 가끔/거의 안함
        cooking_group = 'cooking_often' if cooking == 'often' else 'cooking_rare'
        
        # 세탁: 매일 vs 가끔
        laundry_group = 'laundry_daily' if laundry == 'daily' else 'laundry_weekly'
        
        # 미디어: OTT/게임 vs TV/없음
        media_group = 'media_active' if media in ['ott', 'gaming'] else 'media_passive'
        
        # 조합 (간단하게)
        return f"{cooking_group[:1]}{laundry_group[:1]}{media_group[:1]}"
    
    @staticmethod
    def _normalize_household_size(size: Optional[int]) -> str:
        """가구 인원수를 범위로 정규화"""
        if not size:
            return '2인'
        
        if size == 1:
            return '1인'
        elif size == 2:
            return '2인'
        elif size <= 4:
            return '3-4인'
        else:
            return '5인이상'
    
    @staticmethod
    def _normalize_budget_level(budget_level: str) -> str:
        """예산 레벨 정규화"""
        if budget_level in ['low', 'budget']:
            return 'low'
        elif budget_level in ['medium', 'standard']:
            return 'medium'
        elif budget_level in ['high', 'premium', 'luxury']:
            return 'high'
        return 'medium'
    
    @staticmethod
    def get_taste_description(taste_id: int) -> str:
        """taste_id에 대한 설명 반환"""
        return f"Taste_{taste_id:03d}"


# 싱글톤 인스턴스
weighted_taste_classifier = WeightedTasteClassifier()

