"""
Taste별 Scoring Logic Registry

각 taste_id별로 독립적인 scoring logic을 등록하고 관리하는 시스템.
확장 가능한 구조로 모든 scoring 로직을 taste별로 다르게 적용할 수 있습니다.
"""
import json
from pathlib import Path
from typing import Dict, Optional, List, Callable, Any
from functools import lru_cache
from django.conf import settings
from ..models import Product


class ScoringLogicRegistry:
    """
    Taste별 Scoring Logic을 등록하고 관리하는 레지스트리
    
    각 taste_id별로:
    - 카테고리별 가중치 (MAIN_CATEGORY 직접 지원)
    - 속성별 점수 계산 함수 커스터마이징
    - 보너스/페널티 규칙
    - 필터 규칙
    등을 독립적으로 설정할 수 있습니다.
    """
    
    def __init__(self):
        self._logics: Dict[int, Dict] = {}  # taste_id -> logic
        self._logic_groups: Dict[int, int] = {}  # taste_id -> logic_id (그룹핑)
        self._scoring_functions: Dict[str, Callable] = {}  # 속성별 점수 계산 함수
        self._default_scoring_functions: Dict[str, Callable] = {}
        self._loaded = False
        
    def load_from_json(self, file_path: Optional[Path] = None):
        """JSON 파일에서 scoring logics 로드"""
        if self._loaded:
            return
        
        if file_path is None:
            file_path = Path(__file__).parent.parent / 'scoring_logic' / 'taste_scoring_logics.json'
        
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            logics = json.load(f)
        
        for logic in logics:
            logic_id = logic.get('logic_id')
            applies_to_taste_ids = logic.get('applies_to_taste_ids', [])
            
            for taste_id in applies_to_taste_ids:
                self._logic_groups[taste_id] = logic_id
                # 각 taste_id별로 독립적인 logic 복사본 생성
                self._logics[taste_id] = self._normalize_logic(logic.copy())
        
        self._loaded = True
    
    def _normalize_logic(self, logic: Dict) -> Dict:
        """
        Logic을 정규화하여 MAIN_CATEGORY를 직접 지원하도록 변환
        
        기존 TV, KITCHEN, LIVING 키를 MAIN_CATEGORY로 확장
        """
        weights = logic.get('weights', {})
        
        # MAIN_CATEGORY 매핑 정보 가져오기
        from .category_mapping import (
            DJANGO_CATEGORY_TO_MAIN_CATEGORIES,
            MAIN_CATEGORY_TO_DJANGO_CATEGORY
        )
        
        normalized_weights = {}
        
        # 기존 Django category 기반 weights를 MAIN_CATEGORY로 확장
        for django_category, category_weights in weights.items():
            if django_category in ['TV', 'KITCHEN', 'LIVING', 'AIR', 'AI', 'OBJET', 'SIGNATURE']:
                # 해당 Django category에 속하는 모든 MAIN_CATEGORY에 가중치 적용
                main_categories = DJANGO_CATEGORY_TO_MAIN_CATEGORIES.get(django_category, [])
                
                if main_categories:
                    # 각 MAIN_CATEGORY에 동일한 가중치 적용
                    for main_cat in main_categories:
                        normalized_weights[main_cat] = category_weights.copy()
                else:
                    # 매핑이 없으면 Django category 키도 유지 (fallback)
                    normalized_weights[django_category] = category_weights
            else:
                # 이미 MAIN_CATEGORY 형식이면 그대로 사용
                normalized_weights[django_category] = category_weights
        
        logic['weights'] = normalized_weights
        return logic
    
    def register_logic(self, taste_id: int, logic: Dict):
        """
        특정 taste_id에 대한 scoring logic 등록
        
        Args:
            taste_id: 취향 ID (1~120)
            logic: Scoring logic 딕셔너리
                {
                    'weights': {
                        'MAIN_CATEGORY': {
                            'attribute': weight,
                            ...
                        },
                        ...
                    },
                    'scoring_functions': {  # 선택사항: 속성별 커스텀 함수
                        'attribute': function_name,
                        ...
                    },
                    'bonuses': [...],
                    'penalties': [...],
                    'filters': {...}
                }
        """
        self._logics[taste_id] = self._normalize_logic(logic)
    
    def get_logic(self, taste_id: int) -> Optional[Dict]:
        """taste_id에 해당하는 scoring logic 가져오기"""
        if not self._loaded:
            self.load_from_json()
        
        return self._logics.get(taste_id)
    
    def register_scoring_function(self, attribute: str, func: Callable, override: bool = False):
        """
        속성별 점수 계산 함수 등록 (전역)
        
        Args:
            attribute: 속성명 (예: 'resolution', 'capacity')
            func: 점수 계산 함수 (spec: Dict, profile: UserProfile, logic: Dict) -> float
            override: 기존 함수를 덮어쓸지 여부
        """
        if override or attribute not in self._scoring_functions:
            self._scoring_functions[attribute] = func
    
    def register_default_scoring_function(self, attribute: str, func: Callable):
        """기본 점수 계산 함수 등록 (기본 구현)"""
        self._default_scoring_functions[attribute] = func
    
    def get_scoring_function(self, attribute: str, logic: Optional[Dict] = None) -> Optional[Callable]:
        """
        속성별 점수 계산 함수 가져오기
        
        우선순위:
        1. Logic에 정의된 커스텀 함수
        2. 전역 등록된 함수
        3. 기본 함수
        """
        # Logic에 정의된 커스텀 함수 확인
        if logic:
            scoring_functions = logic.get('scoring_functions', {})
            if attribute in scoring_functions:
                func_name = scoring_functions[attribute]
                if isinstance(func_name, str):
                    # 함수명 문자열인 경우 전역 함수에서 찾기
                    return self._scoring_functions.get(func_name) or self._default_scoring_functions.get(func_name)
                elif callable(func_name):
                    return func_name
        
        # 전역 등록된 함수
        if attribute in self._scoring_functions:
            return self._scoring_functions[attribute]
        
        # 기본 함수
        return self._default_scoring_functions.get(attribute)
    
    def has_logic(self, taste_id: int) -> bool:
        """taste_id에 등록된 logic이 있는지 확인"""
        if not self._loaded:
            self.load_from_json()
        
        return taste_id in self._logics
    
    def list_taste_ids(self) -> List[int]:
        """등록된 모든 taste_id 목록 반환"""
        if not self._loaded:
            self.load_from_json()
        
        return sorted(self._logics.keys())
    
    def clear_cache(self):
        """캐시 초기화"""
        self._logics.clear()
        self._logic_groups.clear()
        self._loaded = False


# 전역 레지스트리 인스턴스
_registry = ScoringLogicRegistry()


def get_registry() -> ScoringLogicRegistry:
    """전역 레지스트리 인스턴스 반환"""
    return _registry


def register_taste_logic(taste_id: int, logic: Dict):
    """taste별 scoring logic 등록 (편의 함수)"""
    _registry.register_logic(taste_id, logic)


def get_taste_logic(taste_id: int) -> Optional[Dict]:
    """taste별 scoring logic 가져오기 (편의 함수)"""
    return _registry.get_logic(taste_id)

