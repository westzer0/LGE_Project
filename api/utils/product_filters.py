"""
제품 필터링 유틸리티

온보딩 데이터를 기반으로 기준에 충족하지 않은 제품들을 완전히 제외하는 엄격한 필터링 로직
"""
import json
import re
from typing import Dict, Optional
from django.db.models import Q
from ..models import Product


def get_product_spec(product: Product) -> Optional[Dict]:
    """제품 스펙 가져오기"""
    try:
        if hasattr(product, 'spec') and product.spec:
            return json.loads(product.spec.spec_json)
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def extract_capacity(spec: Optional[Dict], product: Product) -> Optional[float]:
    """스펙에서 용량 추출 (L 또는 kg)"""
    if not spec:
        return None
    
    # 용량 정보 추출 (다양한 키 시도)
    capacity_str = (
        spec.get("용량", "") or
        spec.get("총 용량", "") or
        spec.get("세탁 용량", "") or
        spec.get("냉장실 용량", "") or
        spec.get("냉동실 용량", "")
    )
    
    if not capacity_str:
        return None
    
    # 숫자 추출
    capacity_match = re.search(r'(\d+(?:\.\d+)?)', str(capacity_str).replace(',', ''))
    if not capacity_match:
        return None
    
    return float(capacity_match.group(1))


def extract_size(spec: Optional[Dict], product: Product) -> Optional[float]:
    """스펙에서 크기 추출 (인치 또는 cm)"""
    if not spec:
        return None
    
    # 크기 정보 추출
    size_str = spec.get("패널 크기", "") or spec.get("크기", "") or spec.get("화면 크기", "")
    
    if not size_str:
        return None
    
    # 숫자 추출
    size_match = re.search(r'(\d+(?:\.\d+)?)', str(size_str).replace(',', ''))
    if not size_match:
        return None
    
    size_value = float(size_match.group(1))
    
    # 인치인 경우 cm로 변환 (대략 1인치 = 2.54cm)
    if "인치" in str(size_str) or '"' in str(size_str) or "inch" in str(size_str).lower():
        return size_value  # 인치 그대로 반환 (TV는 인치 단위 사용)
    
    return size_value


def get_energy_grade(spec: Optional[Dict]) -> Optional[int]:
    """에너지 등급 추출"""
    if not spec:
        return None
    
    energy_grade = spec.get("에너지등급", "") or spec.get("에너지 효율 등급", "")
    
    if not energy_grade:
        return None
    
    # 숫자 추출 (1등급, 2등급 등)
    grade_match = re.search(r'(\d+)', str(energy_grade))
    if grade_match:
        return int(grade_match.group(1))
    
    return None


# ============================================================================
# 필터링 함수들
# ============================================================================

def filter_by_household_size(product: Product, household_size: int) -> bool:
    """
    가족 구성에 따른 용량 필터
    
    Returns:
        True: 필터 통과, False: 필터 제외
    """
    spec = get_product_spec(product)
    capacity = extract_capacity(spec, product)
    
    if capacity is None:
        # 용량 정보가 없으면 통과 (다른 필터에서 처리)
        return True
    
    category = product.category
    product_name = product.name.upper()
    
    # 냉장고 필터
    if category == "KITCHEN" or "냉장고" in product_name or "냉동고" in product_name:
        if household_size == 1:
            # 1인 가구: 200L 이상 완전 제외
            if capacity >= 200:
                return False
        elif household_size == 2:
            # 2인 가구: 900L 이상 제외
            if capacity >= 900:
                return False
        elif household_size >= 4:
            # 4인 이상: 300L 미만 제외
            if capacity < 300:
                return False
    
    # 세탁기 필터
    elif "세탁기" in product_name or "워시" in product_name:
        if household_size == 1:
            # 1인 가구: 7kg 이상 완전 제외
            if capacity >= 7:
                return False
        elif household_size == 2:
            # 2인 가구: 15kg 이상 제외
            if capacity >= 15:
                return False
        elif household_size >= 4:
            # 4인 이상: 4kg 미만 제외
            if capacity < 4:
                return False
    
    # 건조기 필터
    elif "건조기" in product_name or "드라이" in product_name:
        if household_size == 1:
            # 1인 가구: 10kg 이상 제외
            if capacity >= 10:
                return False
        elif household_size >= 4:
            # 4인 이상: 5kg 미만 제외
            if capacity < 5:
                return False
    
    return True


def filter_by_housing_type(product: Product, housing_type: str, pyung: int) -> bool:
    """
    주거 형태/평수에 따른 크기 필터
    
    Returns:
        True: 필터 통과, False: 필터 제외
    """
    spec = get_product_spec(product)
    size = extract_size(spec, product)
    
    if size is None:
        # 크기 정보가 없으면 통과
        return True
    
    category = product.category
    product_name = product.name.upper()
    
    # 원룸/오피스텔: 대형 제품 제외
    if housing_type in ['studio', 'officetel']:
        if category == "KITCHEN" or "냉장고" in product_name:
            # 냉장고: 500L 이상 제외
            capacity = extract_capacity(spec, product)
            if capacity and capacity > 500:
                return False
        elif category == "TV":
            # TV: 55인치 이상 제외
            if size > 55:
                return False
    
    # 아파트: 평수에 따라 제한
    elif housing_type == 'apartment':
        if pyung <= 20:
            # 20평 이하
            if category == "KITCHEN" or "냉장고" in product_name:
                capacity = extract_capacity(spec, product)
                if capacity and capacity > 600:
                    return False
            elif category == "TV":
                if size > 65:
                    return False
        elif pyung <= 30:
            # 20~30평
            if category == "KITCHEN" or "냉장고" in product_name:
                capacity = extract_capacity(spec, product)
                if capacity and capacity > 900:
                    return False
            elif category == "TV":
                if size > 85:
                    return False
    
    # 단독주택: 제한 없음 (통과)
    
    return True


def filter_by_lifestyle(product: Product, user_profile: dict) -> bool:
    """
    생활 패턴 기반 필터
    
    Returns:
        True: 필터 통과, False: 필터 제외
    """
    category = product.category
    product_name = product.name.upper()
    
    cooking = user_profile.get('cooking', 'sometimes')
    laundry = user_profile.get('laundry', 'weekly')
    media = user_profile.get('media', 'balanced')
    
    # 요리 빈도 필터
    if cooking == 'rarely' or cooking == '거의 안 함':
        # 요리 안 함: 전기레인지, 식기세척기 제외
        if '전기레인지' in product_name or '레인지' in product_name:
            return False
        if '식기세척기' in product_name or '세척기' in product_name:
            # 정수기는 선택적 (물 마시는 용도로 사용 가능)
            pass
    
    # 세탁 빈도 필터
    if laundry == 'rarely' or laundry == '거의 안 함':
        # 세탁 안 함: 세탁기, 건조기, 워시타워 제외
        if '세탁기' in product_name or '워시' in product_name:
            return False
        if '건조기' in product_name or '드라이' in product_name:
            return False
    
    # 미디어 사용 필터
    if media == 'rare' or media == '거의 안 봄':
        # 미디어 안 봄: TV, 오디오 제품 제외
        if category == "TV":
            return False
        if '오디오' in product_name or '스피커' in product_name:
            return False
    
    return True


def filter_by_priority(product: Product, user_profile: dict) -> bool:
    """
    우선순위 기반 필터
    
    Returns:
        True: 필터 통과, False: 필터 제외
    """
    priority = user_profile.get('priority', 'value')
    spec = get_product_spec(product)
    product_name = product.name.upper()
    
    # 에너지 효율 우선
    if priority == 'eco' or priority == '에너지효율':
        energy_grade = get_energy_grade(spec)
        if energy_grade and energy_grade > 2:
            # 3등급 이하 제외
            return False
    
    # 디자인 우선
    elif priority == 'design' or priority == '디자인':
        # OBJET, SIGNATURE가 아닌 기본형 제품 제외
        if 'OBJET' not in product_name and 'SIGNATURE' not in product_name:
            # 단, 선택한 카테고리에 OBJET/SIGNATURE가 없으면 예외 처리
            # (이 경우는 recommendation_engine에서 처리)
            # 여기서는 일단 통과
            pass
    
    # 가성비 우선
    elif priority == 'value' or priority == '가성비':
        # 프리미엄 제품 제외
        if 'SIGNATURE' in product_name or '프리미엄' in product_name:
            return False
    
    # 기술/성능 우선
    elif priority == 'tech' or priority == '기술':
        # 구형 모델이나 기본 기능만 있는 제품 제외
        # (스펙 정보로 판단하기 어려우므로 일단 통과)
        pass
    
    return True


def apply_all_filters(products, user_profile: dict) -> list:
    """
    모든 필터를 적용하여 제품 목록 필터링
    
    Args:
        products: 제품 QuerySet 또는 리스트
        user_profile: 사용자 프로필 딕셔너리
    
    Returns:
        필터링된 제품 리스트
    """
    filtered = []
    household_size = user_profile.get('household_size', 2)
    housing_type = user_profile.get('housing_type', 'apartment')
    pyung = user_profile.get('pyung', 25)
    
    excluded_count = {
        'household_size': 0,
        'housing_type': 0,
        'lifestyle': 0,
        'priority': 0,
    }
    
    for product in products:
        # 가족 구성 필터
        if not filter_by_household_size(product, household_size):
            excluded_count['household_size'] += 1
            continue
        
        # 주거 형태 필터
        if not filter_by_housing_type(product, housing_type, pyung):
            excluded_count['housing_type'] += 1
            continue
        
        # 생활 패턴 필터
        if not filter_by_lifestyle(product, user_profile):
            excluded_count['lifestyle'] += 1
            continue
        
        # 우선순위 필터
        if not filter_by_priority(product, user_profile):
            excluded_count['priority'] += 1
            continue
        
        # 모든 필터 통과
        filtered.append(product)
    
    # 디버깅 로그
    print(f"[필터링 결과]")
    print(f"  원본: {len(products)}개")
    print(f"  필터링 후: {len(filtered)}개")
    print(f"  제외된 제품:")
    print(f"    - 가족 구성: {excluded_count['household_size']}개")
    print(f"    - 주거 형태: {excluded_count['housing_type']}개")
    print(f"    - 생활 패턴: {excluded_count['lifestyle']}개")
    print(f"    - 우선순위: {excluded_count['priority']}개")
    
    return filtered



