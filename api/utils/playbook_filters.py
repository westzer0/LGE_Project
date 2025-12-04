"""
Playbook 설계 기반 Hard Filter

정책 테이블 기반으로 설치 불가/부적합 제품 제거
"""
from typing import Dict, Optional
from ..models import Product
from .policy_loader import policy_loader
from .product_filters import get_product_spec, extract_capacity, extract_size


class PlaybookHardFilter:
    """Playbook 설계 기반 Hard Filter"""
    
    def apply_filters(
        self,
        products: list,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> list:
        """
        Hard Filter 적용
        
        Args:
            products: 제품 리스트
            user_profile: 사용자 프로필
            onboarding_data: 온보딩 데이터
            
        Returns:
            필터링된 제품 리스트
        """
        filtered = []
        
        for product in products:
            if self._should_include(product, user_profile, onboarding_data):
                filtered.append(product)
        
        print(f"[Playbook Hard Filter] 원본: {len(products)}개, 필터링 후: {len(filtered)}개")
        
        return filtered
    
    def _should_include(
        self,
        product: Product,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> bool:
        """제품이 필터를 통과하는지 확인"""
        
        # 필터 키 생성 및 규칙 조회
        filters_to_check = self._build_filter_keys(user_profile, onboarding_data, product)
        
        for filter_key in filters_to_check:
            conditions = policy_loader.get_hard_filter_rules(filter_key)
            
            if not conditions:
                continue
            
            # 각 조건 확인
            for condition in conditions:
                if not self._check_condition(product, condition, user_profile, onboarding_data):
                    return False
        
        return True
    
    def _build_filter_keys(
        self,
        user_profile: Dict,
        onboarding_data: Dict,
        product: Product
    ) -> list:
        """필터 키 리스트 생성"""
        keys = []
        category = product.category
        product_name = product.name.upper()
        
        # 주거 형태
        housing_type = user_profile.get('housing_type', 'apartment')
        if housing_type == 'studio':
            keys.append(("원룸", category))
        
        # 가족 구성
        household_size = user_profile.get('household_size', 2)
        if household_size == 1:
            keys.append(("1인", category))
            if "세탁기" in product_name:
                keys.append(("1인", "세탁기"))
            if "건조기" in product_name:
                keys.append(("1인", "건조기"))
        elif household_size == 2:
            keys.append(("2인", category))
            if "세탁기" in product_name:
                keys.append(("2인", "세탁기"))
        elif household_size >= 4:
            keys.append(("4인 이상", category))
            if "세탁기" in product_name:
                keys.append(("4인 이상", "세탁기"))
            if "건조기" in product_name:
                keys.append(("4인 이상", "건조기"))
        
        # 평수
        pyung = user_profile.get('pyung', 25)
        if pyung <= 20:
            keys.append(("20평 이하", category))
        elif pyung <= 30:
            keys.append(("20~30평", category))
        
        # 예산
        budget_level = user_profile.get('budget_level', 'medium')
        if budget_level == 'low':
            keys.append(("예산_low", "전체"))
        
        # 미디어 소비
        media = onboarding_data.get('media', 'balanced')
        if media == 'none' and category == "TV":
            keys.append(("미디어_none", "TV"))
        
        # 요리 빈도
        cooking = onboarding_data.get('cooking', 'sometimes')
        if cooking in ['rarely', '거의 안 함']:
            if "전기레인지" in product_name or "레인지" in product_name:
                keys.append(("요리_rarely", "전기레인지"))
        
        # 세탁 빈도
        laundry = onboarding_data.get('laundry', 'weekly')
        if laundry in ['rarely', '거의 안 함']:
            if "세탁기" in product_name:
                keys.append(("세탁_rarely", "세탁기"))
            if "건조기" in product_name:
                keys.append(("세탁_rarely", "건조기"))
        
        # 반려동물
        has_pet = user_profile.get('has_pet', False)
        if not has_pet:
            # 펫 전용 제품 제외
            pet_keywords = ["펫", "PET", "반려동물", "애완동물"]
            product_name_upper = product.name.upper()
            if any(kw in product_name_upper for kw in pet_keywords):
                keys.append(("펫_false", "펫_전용"))
        
        return keys
    
    def _check_condition(
        self,
        product: Product,
        condition: Dict,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> bool:
        """조건 확인"""
        condition_type = condition.get('type')
        spec_key = condition.get('spec_key')
        operator = condition.get('operator')
        value = condition.get('value')
        
        # ignore_category 타입
        if condition_type == 'ignore_category':
            return not value  # value가 True면 제외
        
        # ignore_keywords 타입
        if condition_type == 'ignore_keywords':
            keywords = condition.get('keywords', [])
            product_name_upper = product.name.upper()
            return not any(kw in product_name_upper for kw in keywords)
        
        # 스펙 기반 조건
        if spec_key and operator and value is not None:
            spec = get_product_spec(product)
            if not spec:
                return True  # 스펙이 없으면 통과
            
            # 스펙 값 추출
            spec_value = None
            
            if spec_key == "capacity_l":
                spec_value = extract_capacity(spec, product)
            elif spec_key == "capacity_kg":
                spec_value = extract_capacity(spec, product)
            elif spec_key == "size_inch":
                spec_value = extract_size(spec, product)
            elif spec_key == "depth_mm":
                # 깊이 정보 추출 (구현 필요)
                depth_str = spec.get("깊이", "") or spec.get("깊이(mm)", "")
                if depth_str:
                    import re
                    depth_match = re.search(r'(\d+)', str(depth_str))
                    if depth_match:
                        spec_value = float(depth_match.group(1))
            elif spec_key == "price":
                spec_value = float(product.price) if product.price else 0
            
            if spec_value is None:
                return True  # 값이 없으면 통과
            
            # 조건 확인
            if operator == ">":
                if spec_value > value:
                    return False  # 조건 위반
            elif operator == ">=":
                if spec_value >= value:
                    return False
            elif operator == "<":
                if spec_value < value:
                    return False
            elif operator == "<=":
                if spec_value <= value:
                    return False
            elif operator == "==":
                if spec_value == value:
                    return False
        
        return True  # 조건 통과


# Singleton 인스턴스
playbook_hard_filter = PlaybookHardFilter()

