"""
온보딩 데이터를 기반으로 taste를 분류하는 유틸리티

온보딩 조합(약 10,000개)을 적절한 수의 taste(100-150개)로 그룹화합니다.
"""
import hashlib
import json
from typing import Dict, Optional


class TasteClassifier:
    """
    온보딩 데이터를 기반으로 taste를 계산하는 클래스
    
    전략:
    1. 해시 기반 분류: 온보딩 데이터를 해시하여 일정 범위의 taste_id 생성
    2. 주요 속성 기반 그룹화: vibe, household_size, priority, budget_level 등을 조합
    3. 약 100-150개의 taste로 구분
    """
    
    # Taste 개수 설정
    TASTE_COUNT = 1920  # 1920개 taste로 확장
    
    @staticmethod
    def calculate_taste_from_onboarding(onboarding_data: Dict) -> int:
        """
        온보딩 데이터로부터 taste_id 계산
        
        Args:
            onboarding_data: 온보딩 데이터 딕셔너리
                - vibe: 분위기
                - household_size: 가구 인원수
                - housing_type: 주거 형태
                - pyung: 평수
                - main_space: 주요 공간 (배열)
                - cooking: 요리 빈도
                - laundry: 세탁 빈도
                - media: 미디어 사용 패턴
                - priority: 우선순위 (배열)
                - budget_level: 예산 범위
                - has_pet: 반려동물 여부
        
        Returns:
            taste_id (1 ~ TASTE_COUNT)
        """
        # 1. 주요 속성 추출 및 정규화
        vibe = onboarding_data.get('vibe', 'modern')
        household_size = onboarding_data.get('household_size', 2)
        housing_type = onboarding_data.get('housing_type', 'apartment')
        pyung = onboarding_data.get('pyung', 25)
        budget_level = onboarding_data.get('budget_level', 'medium')
        priority = onboarding_data.get('priority', ['value'])
        has_pet = onboarding_data.get('has_pet', False)
        
        # main_space 정규화 (배열을 정렬된 문자열로)
        main_space = onboarding_data.get('main_space', [])
        if isinstance(main_space, str):
            main_space = [main_space]
        main_space_str = ','.join(sorted(main_space)) if main_space else 'none'
        
        # priority 정규화 (배열을 정렬된 문자열로)
        if isinstance(priority, str):
            priority = [priority]
        priority_str = ','.join(sorted(priority)) if priority else 'value'
        
        # 생활 패턴 정규화
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        # 2. 평수 범위화 (10단위로 그룹화)
        pyung_range = TasteClassifier._normalize_pyung(pyung)
        
        # 3. 가구 인원수 범위화
        household_range = TasteClassifier._normalize_household_size(household_size)
        
        # 4. Taste 키 생성 (주요 속성 조합)
        taste_key_parts = [
            vibe,  # 4가지
            household_range,  # 4가지 범위
            housing_type,  # 4가지
            pyung_range,  # 7가지 범위
            budget_level,  # 3가지
            priority_str[:20],  # 우선순위 조합 (최대 20자)
            main_space_str[:30],  # 주요 공간 조합 (최대 30자)
            'pet' if has_pet else 'no_pet',  # 반려동물 여부
            cooking,  # 3가지
            laundry,  # 3가지
            media,  # 4가지
        ]
        
        taste_key = '|'.join(str(p) for p in taste_key_parts)
        
        # 5. 해시 기반 taste_id 생성 (1 ~ TASTE_COUNT)
        taste_hash = int(hashlib.md5(taste_key.encode('utf-8')).hexdigest(), 16)
        taste_id = (taste_hash % TasteClassifier.TASTE_COUNT) + 1
        
        # 6. 검증: 1~1920 범위의 정수로 보장
        taste_id = int(taste_id)
        if taste_id < 1:
            taste_id = 1
        elif taste_id > TasteClassifier.TASTE_COUNT:
            taste_id = TasteClassifier.TASTE_COUNT
        
        return taste_id
    
    @staticmethod
    def _normalize_pyung(pyung: Optional[int]) -> str:
        """평수를 범위로 정규화"""
        if not pyung:
            return '20-30'
        
        if pyung <= 10:
            return '10이하'
        elif pyung <= 15:
            return '11-15'
        elif pyung <= 20:
            return '16-20'
        elif pyung <= 30:
            return '21-30'
        elif pyung <= 40:
            return '31-40'
        elif pyung <= 50:
            return '41-50'
        else:
            return '51이상'
    
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
    def calculate_taste_from_session(session_data: Dict) -> int:
        """
        ONBOARDING_SESSION 데이터로부터 taste_id 계산
        
        Args:
            session_data: ONBOARDING_SESSION 테이블의 데이터
        
        Returns:
            taste_id
        """
        # ONBOARDING_SESSION 데이터를 onboarding_data 형식으로 변환
        onboarding_data = {
            'vibe': session_data.get('VIBE'),
            'household_size': session_data.get('HOUSEHOLD_SIZE'),
            'housing_type': session_data.get('HOUSING_TYPE'),
            'pyung': session_data.get('PYUNG'),
            'budget_level': session_data.get('BUDGET_LEVEL'),
            'priority': session_data.get('PRIORITY'),
            'has_pet': session_data.get('HAS_PET') == 'Y' if session_data.get('HAS_PET') else False,
        }
        
        # MAIN_SPACE 파싱 (JSON 문자열일 수 있음)
        main_space = session_data.get('MAIN_SPACE')
        if main_space:
            try:
                if isinstance(main_space, str):
                    main_space = json.loads(main_space)
                onboarding_data['main_space'] = main_space if isinstance(main_space, list) else [main_space]
            except:
                onboarding_data['main_space'] = []
        else:
            onboarding_data['main_space'] = []
        
        # 생활 패턴
        onboarding_data['cooking'] = session_data.get('COOKING', 'sometimes')
        onboarding_data['laundry'] = session_data.get('LAUNDRY', 'weekly')
        onboarding_data['media'] = session_data.get('MEDIA', 'balanced')
        
        return TasteClassifier.calculate_taste_from_onboarding(onboarding_data)
    
    @staticmethod
    def get_taste_description(taste_id: int) -> str:
        """
        taste_id에 대한 설명 반환
        
        Args:
            taste_id: 취향 ID
        
        Returns:
            취향 설명
        """
        return f"Taste_{taste_id:03d}"


# 싱글톤 인스턴스
taste_classifier = TasteClassifier()

