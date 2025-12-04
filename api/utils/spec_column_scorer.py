"""
SPEC 칼럼 기반 점수 산출 로직

Oracle DB PRODUCT SPEC 테이블의 SPEC_TYPE(COMMON/VARIANT)과 SPEC_KEY를 기반으로
칼럼 점수를 산출하고, 이를 통해 패키지에 포함될 가전 종류를 결정합니다.
"""
import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from ..models import Product, ProductSpec
from .product_type_classifier import extract_product_type, group_products_by_type


class SpecColumnScorer:
    """SPEC 칼럼 기반 점수 산출기"""
    
    def __init__(self):
        # COMMON 칼럼: 모든 제품 종류에 공통, 반드시 포함
        self.common_spec_keys = []
        
        # VARIANT 칼럼: 제품 종류별로 다름, 조건부 포함
        self.variant_spec_keys_by_type = defaultdict(set)
        
        # SPEC_KEY별 등장 빈도 (제품 종류별)
        self.spec_key_frequency = defaultdict(lambda: defaultdict(int))
        
        # SPEC_KEY별 전체 등장 빈도
        self.spec_key_total_frequency = defaultdict(int)
    
    def analyze_spec_structure(self, products: List[Product]) -> Dict:
        """
        제품 스펙 구조 분석
        
        - COMMON 칼럼 식별 (모든 제품 종류에 100% 존재)
        - VARIANT 칼럼 식별 (제품 종류별로 다름)
        - SPEC_KEY별 등장 빈도 계산
        
        Returns:
            분석 결과 딕셔너리
        """
        print("[SpecColumnScorer] 제품 스펙 구조 분석 시작...")
        
        # 제품 종류별로 그룹화
        products_by_type = group_products_by_type(products)
        
        # 제품 종류별 SPEC_KEY 수집
        spec_keys_by_type = defaultdict(set)
        all_spec_keys = set()
        
        total_products = 0
        for product_type, type_products in products_by_type.items():
            for product in type_products:
                if not hasattr(product, 'spec') or not product.spec:
                    continue
                
                try:
                    spec_json = json.loads(product.spec.spec_json)
                    if isinstance(spec_json, dict):
                        spec_keys = set(spec_json.keys())
                        spec_keys_by_type[product_type].update(spec_keys)
                        all_spec_keys.update(spec_keys)
                        
                        # 등장 빈도 계산
                        for key in spec_keys:
                            self.spec_key_frequency[product_type][key] += 1
                            self.spec_key_total_frequency[key] += 1
                        
                        total_products += 1
                except (json.JSONDecodeError, AttributeError):
                    continue
        
        # COMMON 칼럼 식별: 모든 제품 종류에서 100% 존재하는 칼럼
        common_spec_keys = set(all_spec_keys)
        for product_type, keys in spec_keys_by_type.items():
            type_product_count = len([p for p in products_by_type[product_type] if hasattr(p, 'spec') and p.spec])
            if type_product_count == 0:
                continue
            
            # 해당 제품 종류에서 100% 존재하는 칼럼만
            type_common_keys = set()
            for key in keys:
                frequency = self.spec_key_frequency[product_type][key]
                if frequency == type_product_count:  # 100% 존재
                    type_common_keys.add(key)
            
            # 모든 제품 종류에서 공통인 칼럼만 남김
            common_spec_keys = common_spec_keys.intersection(type_common_keys)
        
        self.common_spec_keys = list(common_spec_keys)
        
        # VARIANT 칼럼 식별: 제품 종류별로 다른 칼럼
        for product_type, keys in spec_keys_by_type.items():
            variant_keys = keys - common_spec_keys
            self.variant_spec_keys_by_type[product_type].update(variant_keys)
        
        print(f"[SpecColumnScorer] 분석 완료:")
        print(f"  - 총 제품 수: {total_products}")
        print(f"  - 제품 종류 수: {len(products_by_type)}")
        print(f"  - COMMON 칼럼 수: {len(self.common_spec_keys)}")
        print(f"  - COMMON 칼럼: {self.common_spec_keys[:10]}...")
        
        for product_type, variant_keys in list(self.variant_spec_keys_by_type.items())[:5]:
            print(f"  - {product_type} VARIANT 칼럼: {len(variant_keys)}개")
        
        return {
            'common_spec_keys': list(common_spec_keys),
            'variant_spec_keys_by_type': {
                k: list(v) for k, v in self.variant_spec_keys_by_type.items()
            },
            'total_products': total_products,
            'spec_key_frequency': dict(self.spec_key_frequency)
        }
    
    def get_scoring_spec_keys(
        self,
        product_type: str,
        user_profile: dict,
        onboarding_data: dict
    ) -> List[str]:
        """
        점수 산출에 사용할 SPEC_KEY 목록 반환
        
        Args:
            product_type: 제품 종류
            user_profile: 사용자 프로필
            onboarding_data: 온보딩 데이터
            
        Returns:
            점수 산출에 사용할 SPEC_KEY 리스트
        """
        scoring_keys = []
        
        # 1. COMMON 칼럼: 반드시 포함
        scoring_keys.extend(self.common_spec_keys)
        
        # 2. VARIANT 칼럼: 조건부 포함
        variant_keys = self.variant_spec_keys_by_type.get(product_type, set())
        
        for variant_key in variant_keys:
            if self._should_include_variant_key(
                variant_key,
                product_type,
                user_profile,
                onboarding_data
            ):
                scoring_keys.append(variant_key)
        
        return scoring_keys
    
    def _should_include_variant_key(
        self,
        spec_key: str,
        product_type: str,
        user_profile: dict,
        onboarding_data: dict
    ) -> bool:
        """
        VARIANT 칼럼을 점수 산출에 포함할지 결정
        
        기준:
        - 등장 빈도 (해당 제품 종류에서 얼마나 자주 나타나는지)
        - 온보딩 사용자 정보에 따른 중요도
        
        Returns:
            포함 여부 (True/False)
        """
        # 등장 빈도 확인
        type_product_count = self._get_product_count_by_type(product_type)
        if type_product_count == 0:
            return False
        
        frequency = self.spec_key_frequency[product_type].get(spec_key, 0)
        frequency_ratio = frequency / type_product_count if type_product_count > 0 else 0
        
        # 최소 등장 빈도 기준 (예: 50% 이상)
        min_frequency_threshold = 0.5
        
        # 온보딩 정보에 따른 중요도 조정
        importance_multiplier = self._calculate_variant_key_importance(
            spec_key,
            product_type,
            user_profile,
            onboarding_data
        )
        
        # 등장 빈도가 높고, 중요도가 높은 경우 포함
        if frequency_ratio >= min_frequency_threshold and importance_multiplier >= 0.8:
            return True
        
        # 등장 빈도가 매우 높은 경우 (80% 이상) 무조건 포함
        if frequency_ratio >= 0.8:
            return True
        
        return False
    
    def _get_product_count_by_type(self, product_type: str) -> int:
        """제품 종류별 제품 수 반환"""
        # 실제 구현에서는 DB에서 조회하거나 캐시 사용
        # 여기서는 frequency 데이터 기반으로 추정
        max_count = 0
        for key, count in self.spec_key_frequency[product_type].items():
            max_count = max(max_count, count)
        return max_count
    
    def _calculate_variant_key_importance(
        self,
        spec_key: str,
        product_type: str,
        user_profile: dict,
        onboarding_data: dict
    ) -> float:
        """
        VARIANT 칼럼의 중요도 계산 (0.0 ~ 1.0)
        
        온보딩 사용자 정보에 따라 중요도가 달라짐
        """
        importance = 1.0
        
        household_size = user_profile.get('household_size', 2)
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        priority = user_profile.get('priority', 'value')
        
        # SPEC_KEY별 중요도 조정 로직
        spec_key_lower = spec_key.lower()
        
        # 용량 관련 칼럼
        if '용량' in spec_key or 'capacity' in spec_key_lower or '용량' in spec_key:
            if product_type in ['냉장고', '세탁기'] and household_size >= 3:
                importance = 1.2  # 큰 가족에게 용량 중요
        
        # 에너지 효율 관련
        if '에너지' in spec_key or 'energy' in spec_key_lower or '효율' in spec_key:
            if priority == 'eco':
                importance = 1.3  # 에너지 효율 우선 사용자에게 중요
        
        # 해상도/화질 관련 (TV)
        if product_type == 'TV' and ('해상도' in spec_key or 'resolution' in spec_key_lower):
            if media in ['gaming', 'heavy']:
                importance = 1.3  # 게이머/헤비 사용자에게 중요
        
        # 세탁 용량 관련
        if product_type == '세탁기' and ('용량' in spec_key or 'kg' in spec_key_lower):
            if laundry == 'daily':
                importance = 1.2  # 매일 세탁하는 사용자에게 중요
        
        # 요리 관련 칼럼
        if product_type in ['오븐', '식기세척기']:
            if cooking in ['high', 'often']:
                importance = 1.2
        
        return min(importance, 1.5)  # 최대 1.5배
    
    def calculate_product_type_column_score(
        self,
        product_type: str,
        products: List[Product],
        user_profile: dict,
        onboarding_data: dict
    ) -> float:
        """
        제품 종류별 칼럼 점수 산출
        
        해당 제품 종류의 모든 제품에 대해 COMMON + VARIANT 칼럼 기반 점수 계산
        
        Returns:
            제품 종류별 칼럼 점수 (0.0 ~ 1.0)
        """
        if not products:
            return 0.0
        
        # 점수 산출에 사용할 SPEC_KEY 목록
        scoring_keys = self.get_scoring_spec_keys(
            product_type,
            user_profile,
            onboarding_data
        )
        
        if not scoring_keys:
            return 0.0
        
        # 각 제품별 칼럼 점수 계산
        product_scores = []
        
        for product in products:
            if not hasattr(product, 'spec') or not product.spec:
                continue
            
            try:
                spec_json = json.loads(product.spec.spec_json)
                if not isinstance(spec_json, dict):
                    continue
                
                # COMMON 칼럼 점수 (필수)
                common_score = self._calculate_common_column_score(
                    spec_json,
                    scoring_keys,
                    user_profile,
                    onboarding_data
                )
                
                # VARIANT 칼럼 점수 (조건부)
                variant_score = self._calculate_variant_column_score(
                    spec_json,
                    product_type,
                    scoring_keys,
                    user_profile,
                    onboarding_data
                )
                
                # 최종 칼럼 점수 (COMMON 70%, VARIANT 30% 가중치)
                column_score = common_score * 0.7 + variant_score * 0.3
                product_scores.append(column_score)
                
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
        
        # 제품 종류별 평균 칼럼 점수
        if product_scores:
            avg_score = sum(product_scores) / len(product_scores)
            return avg_score
        
        return 0.0
    
    def _calculate_common_column_score(
        self,
        spec_json: dict,
        scoring_keys: List[str],
        user_profile: dict,
        onboarding_data: dict
    ) -> float:
        """COMMON 칼럼 기반 점수 계산"""
        score = 0.0
        common_keys_in_spec = 0
        
        for key in self.common_spec_keys:
            if key in spec_json and spec_json[key]:
                common_keys_in_spec += 1
                # 칼럼 값의 적정성 평가 (간단한 로직)
                # 실제로는 더 복잡한 평가 필요
        
        if len(self.common_spec_keys) > 0:
            score = common_keys_in_spec / len(self.common_spec_keys)
        
        return score
    
    def _calculate_variant_column_score(
        self,
        spec_json: dict,
        product_type: str,
        scoring_keys: List[str],
        user_profile: dict,
        onboarding_data: dict
    ) -> float:
        """VARIANT 칼럼 기반 점수 계산"""
        variant_keys = self.variant_spec_keys_by_type.get(product_type, set())
        variant_keys_in_scoring = [
            k for k in scoring_keys 
            if k in variant_keys and k not in self.common_spec_keys
        ]
        
        if not variant_keys_in_scoring:
            return 0.0
        
        variant_keys_in_spec = 0
        for key in variant_keys_in_scoring:
            if key in spec_json and spec_json[key]:
                variant_keys_in_spec += 1
        
        score = variant_keys_in_spec / len(variant_keys_in_scoring) if variant_keys_in_scoring else 0.0
        return score


# Singleton 인스턴스
spec_column_scorer = SpecColumnScorer()

