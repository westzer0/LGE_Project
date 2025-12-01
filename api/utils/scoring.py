"""
Product scoring utilities based on ProductSpec JSON and UserProfile
"""
import json
from typing import Dict, Optional
from dataclasses import dataclass
from ..models import Product
from ..rule_engine import UserProfile


# ============================================================================
# 스코어링 가중치 설정 (Constants)
# ============================================================================

# 카테고리별 가중치
CATEGORY_WEIGHTS = {
    "TV": {
        "resolution": 0.25,      # 해상도 (4K > FHD > HD)
        "brightness": 0.15,      # 밝기 (nit)
        "refresh_rate": 0.15,   # 주사율 (Hz)
        "panel_type": 0.10,      # 패널 타입 (OLED > QLED > IPS)
        "power_consumption": 0.10,  # 전력소비 (낮을수록 좋음)
        "size": 0.10,           # 크기 (사용자 공간에 맞는지)
        "price_match": 0.15,    # 예산 대비 가격 적합도
    },
    "LIVING": {
        "audio_quality": 0.25,  # 오디오 품질
        "connectivity": 0.15,   # 연결성
        "power_consumption": 0.10,
        "size": 0.10,
        "price_match": 0.20,
        "features": 0.20,       # 추가 기능
    },
    "KITCHEN": {
        "capacity": 0.25,       # 용량
        "energy_efficiency": 0.20,  # 에너지 효율
        "features": 0.15,
        "size": 0.10,
        "price_match": 0.20,
        "design": 0.10,
    },
    "default": {
        "price_match": 0.30,
        "features": 0.25,
        "energy_efficiency": 0.20,
        "size": 0.15,
        "design": 0.10,
    }
}

# Priority별 가중치 조정
PRIORITY_MULTIPLIERS = {
    "design": {
        "design": 1.5,
        "panel_type": 1.3,
        "features": 1.2,
    },
    "tech": {
        "resolution": 1.5,
        "refresh_rate": 1.4,
        "brightness": 1.3,
        "features": 1.2,
    },
    "eco": {
        "power_consumption": 1.5,
        "energy_efficiency": 1.5,
        "power_consumption": 1.3,
    },
    "value": {
        "price_match": 1.5,
        "features": 1.2,
    },
}

# Vibe별 디자인 점수
VIBE_SCORES = {
    "modern": {
        "OBJET": 1.0,
        "SIGNATURE": 0.9,
        "default": 0.7,
    },
    "cozy": {
        "OBJET": 0.9,
        "default": 0.8,
    },
    "pop": {
        "OBJET": 1.0,
        "default": 0.8,
    },
    "luxury": {
        "SIGNATURE": 1.0,
        "OBJET": 0.8,
        "default": 0.6,
    },
}


# ============================================================================
# 스펙 파싱 헬퍼 함수
# ============================================================================

def parse_spec_json(product: Product) -> Optional[Dict]:
    """ProductSpec의 spec_json을 파싱하여 dict 반환"""
    try:
        if hasattr(product, 'spec') and product.spec:
            return json.loads(product.spec.spec_json)
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def get_spec_value(spec: Dict, key: str, default=None):
    """스펙에서 값을 안전하게 가져오기"""
    return spec.get(key, default) if spec else default


def parse_number(value, default=0):
    """문자열에서 숫자 추출 (예: "1,920 × 1,080" → 1920)"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    
    import re
    # 숫자만 추출 (첫 번째 숫자)
    numbers = re.findall(r'\d+', str(value).replace(',', ''))
    return float(numbers[0]) if numbers else default


def parse_resolution(resolution_str: str) -> tuple:
    """해상도 문자열 파싱 (예: "1,920 × 1,080" → (1920, 1080))"""
    if not resolution_str:
        return (0, 0)
    
    import re
    numbers = re.findall(r'\d+', str(resolution_str).replace(',', ''))
    if len(numbers) >= 2:
        return (int(numbers[0]), int(numbers[1]))
    elif len(numbers) == 1:
        return (int(numbers[0]), 0)
    return (0, 0)


# ============================================================================
# 개별 스펙 점수 계산 함수
# ============================================================================

def score_resolution(spec: Dict, profile: UserProfile) -> float:
    """해상도 점수 (0.0 ~ 1.0)"""
    resolution_str = get_spec_value(spec, "해상도", "")
    if not resolution_str:
        return 0.5  # 기본값
    
    width, height = parse_resolution(resolution_str)
    total_pixels = width * height
    
    # 해상도 등급별 점수
    if total_pixels >= 3840 * 2160:  # 4K
        return 1.0
    elif total_pixels >= 2560 * 1440:  # QHD
        return 0.8
    elif total_pixels >= 1920 * 1080:  # FHD
        return 0.6
    elif total_pixels >= 1280 * 720:  # HD
        return 0.4
    else:
        return 0.2


def score_brightness(spec: Dict, profile: UserProfile) -> float:
    """밝기 점수 (0.0 ~ 1.0)"""
    brightness_str = get_spec_value(spec, "밝기 (Typ.)", "")
    if not brightness_str:
        return 0.5
    
    brightness = parse_number(brightness_str)
    
    # 밝기 등급별 점수 (nit 기준)
    if brightness >= 1000:
        return 1.0
    elif brightness >= 700:
        return 0.8
    elif brightness >= 500:
        return 0.6
    elif brightness >= 300:
        return 0.4
    else:
        return 0.2


def score_refresh_rate(spec: Dict, profile: UserProfile) -> float:
    """주사율 점수 (0.0 ~ 1.0)"""
    refresh_str = get_spec_value(spec, "주사율", "")
    if not refresh_str:
        return 0.5
    
    refresh_rate = parse_number(refresh_str)
    
    # 주사율 등급별 점수
    if refresh_rate >= 120:
        return 1.0
    elif refresh_rate >= 100:
        return 0.9
    elif refresh_rate >= 60:
        return 0.7
    else:
        return 0.4


def score_panel_type(spec: Dict, profile: UserProfile) -> float:
    """패널 타입 점수 (0.0 ~ 1.0)"""
    panel_type = get_spec_value(spec, "패널 타입", "").upper()
    
    # 패널 타입별 점수
    if "OLED" in panel_type:
        return 1.0
    elif "QLED" in panel_type or "QD-OLED" in panel_type:
        return 0.9
    elif "IPS" in panel_type:
        return 0.7
    elif "VA" in panel_type:
        return 0.6
    else:
        return 0.5


def score_power_consumption(spec: Dict, profile: UserProfile) -> float:
    """전력소비 점수 (낮을수록 좋음, 0.0 ~ 1.0)"""
    power_str = get_spec_value(spec, "전력소비", "")
    if not power_str:
        return 0.5
    
    # 전력소비 값 추출 (W 단위)
    import re
    power_match = re.search(r'(\d+(?:\.\d+)?)\s*W', str(power_str), re.IGNORECASE)
    if power_match:
        power = float(power_match.group(1))
    else:
        power = parse_number(power_str)
    
    # 전력소비가 낮을수록 높은 점수 (역변환)
    # 0W ~ 50W: 1.0, 50W ~ 100W: 0.8, 100W ~ 200W: 0.6, 200W+: 0.4
    if power <= 50:
        return 1.0
    elif power <= 100:
        return 0.8
    elif power <= 200:
        return 0.6
    elif power <= 300:
        return 0.4
    else:
        return 0.2


def score_size(spec: Dict, profile: UserProfile) -> float:
    """크기 적합도 점수 (0.0 ~ 1.0) - TV 등 물리적 크기"""
    size_str = get_spec_value(spec, "패널 크기", "") or get_spec_value(spec, "크기", "")
    if not size_str:
        return 0.5
    
    # 크기 추출 (cm 또는 inch)
    import re
    size_match = re.search(r'(\d+(?:\.\d+)?)', str(size_str))
    if size_match:
        size_cm = float(size_match.group(1))
        # inch인 경우 cm로 변환 (대략 1 inch = 2.54 cm)
        if "인치" in str(size_str) or '"' in str(size_str) or "inch" in str(size_str).lower():
            size_cm = size_cm * 2.54
    else:
        return 0.5
    
    # 공간 크기에 따른 적합도 (space_size 기반)
    space_size = profile.space_size.lower() if profile.space_size else ""
    household_size = parse_number(profile.household_size, 2)
    
    # 가구 인원과 공간 크기 기반 적정 크기 계산
    if space_size in ["small", "소형"]:
        ideal_size = 100  # 40인치 정도
    elif space_size in ["medium", "중형"]:
        ideal_size = 120  # 48인치 정도
    else:  # large
        ideal_size = 150  # 60인치 정도
    
    # 가구 인원이 많을수록 큰 화면 선호
    ideal_size += (household_size - 2) * 10
    
    # 1인 가구는 작은 크기 선호 (기본 크기 축소)
    if household_size == 1:
        ideal_size = max(ideal_size - 20, 80)  # 최소 80cm (약 32인치)
    
    # 차이가 적을수록 높은 점수
    diff = abs(size_cm - ideal_size)
    
    # 1인 가구에게 대형 제품에 대한 강한 감점 적용
    if household_size == 1 and size_cm > ideal_size + 20:
        # 이상적인 크기보다 20cm 이상 크면 급격히 감점
        over_ratio = (size_cm - ideal_size - 20) / ideal_size
        penalty = min(0.3, over_ratio * 0.5)  # 최대 0.3 감점
        base_score = max(0.2, 1.0 - diff / 100) if diff <= 50 else 0.2
        return max(0.0, base_score - penalty)
    
    # 일반적인 점수 계산
    if diff <= 10:
        return 1.0
    elif diff <= 20:
        return 0.8
    elif diff <= 30:
        return 0.6
    elif diff <= 50:
        return 0.4
    else:
        return 0.2


def score_price_match(product: Product, profile: UserProfile) -> float:
    """예산 대비 가격 적합도 점수 (0.0 ~ 1.0)"""
    price = float(product.price) if product.price else 0
    discount_price = float(product.discount_price) if product.discount_price else price
    
    # 예산 범위 설정
    budget_ranges = {
        "budget": (0, 500000),
        "standard": (500000, 2000000),
        "premium": (2000000, 5000000),
        "luxury": (5000000, float('inf')),
    }
    
    budget_level = profile.budget_level.lower() if profile.budget_level else "standard"
    min_budget, max_budget = budget_ranges.get(budget_level, (0, float('inf')))
    
    # 예산 범위 내에 있으면 높은 점수
    if min_budget <= discount_price <= max_budget:
        # 예산 중간값에 가까울수록 높은 점수
        budget_center = (min_budget + max_budget) / 2
        diff = abs(discount_price - budget_center) / (max_budget - min_budget) if max_budget != float('inf') else 0.1
        return max(0.7, 1.0 - diff)
    elif discount_price < min_budget:
        # 예산보다 낮으면 약간 감점
        return 0.6
    else:
        # 예산보다 높으면 감점
        over_ratio = (discount_price - max_budget) / max_budget if max_budget != float('inf') else 0.1
        return max(0.1, 0.5 - over_ratio * 0.5)


def score_capacity(spec: Dict, profile: UserProfile, product: Product) -> float:
    """
    용량 적합도 점수 (0.0 ~ 1.0) - 냉장고, 세탁기 등 용량 기반 제품
    
    Args:
        spec: 제품 스펙 딕셔너리
        profile: 사용자 프로필
        product: 제품 인스턴스 (카테고리 확인용)
    
    Returns:
        float: 용량 적합도 점수 (0.0 ~ 1.0)
    """
    # 용량 정보 추출 (다양한 키 시도)
    capacity_str = (
        get_spec_value(spec, "용량", "") or
        get_spec_value(spec, "총 용량", "") or
        get_spec_value(spec, "세탁 용량", "") or
        get_spec_value(spec, "냉장실 용량", "") or
        get_spec_value(spec, "냉동실 용량", "")
    )
    
    if not capacity_str:
        return 0.5  # 용량 정보가 없으면 기본값
    
    # 용량 숫자 추출 (L, 리터 단위)
    import re
    capacity_match = re.search(r'(\d+(?:\.\d+)?)', str(capacity_str).replace(',', ''))
    if not capacity_match:
        return 0.5
    
    capacity_liters = float(capacity_match.group(1))
    
    # 가구 인원수 파싱
    household_size = parse_number(profile.household_size, 2)
    
    # 카테고리별 적정 용량 계산
    category = product.category if hasattr(product, 'category') else ""
    
    if category == "KITCHEN" or "냉장고" in product.name or "냉동고" in product.name:
        # 냉장고: 1인당 50-70L 적정
        ideal_capacity = household_size * 60
        max_reasonable = household_size * 100  # 최대 적정 용량
        min_reasonable = household_size * 40   # 최소 적정 용량
        capacity_value = capacity_liters
        
    elif category == "LIVING" or "세탁기" in product.name or "건조기" in product.name:
        # 세탁기: 1인당 2-3kg 적정, 2인 가구는 4-5kg
        # 용량이 kg 단위일 수 있음
        if capacity_liters > 50:  # L 단위가 아니라 kg 단위일 가능성
            capacity_kg = capacity_liters
        else:
            capacity_kg = capacity_liters  # 실제로는 kg일 수도
        
        ideal_capacity = max(4, household_size * 2.5)
        max_reasonable = household_size * 4
        min_reasonable = max(3, household_size * 1.5)
        
        # 세탁기용량은 보통 kg이므로 liters로 변환하지 않음
        capacity_value = capacity_kg
        
    else:
        # 기타 제품은 기본 계산
        ideal_capacity = household_size * 50
        max_reasonable = household_size * 100
        min_reasonable = household_size * 30
        capacity_value = capacity_liters
    
    # 1인 가구에게 대형 용량에 대한 강한 감점 (하드 필터링 수준)
    if household_size == 1:
        if category == "KITCHEN" or "냉장고" in product.name:
            # 1인 가구: 200L 이상은 과도하게 큼 (매우 강한 감점)
            if capacity_value >= 200:
                over_ratio = (capacity_value - 200) / 200
                return max(0.0, 0.1 - over_ratio * 0.05)  # 0.1 ~ 0.05
            elif capacity_value >= 150:
                # 150-200L: 강한 감점
                return 0.15
            elif capacity_value >= 100:
                # 100-150L: 중간 감점
                return 0.3
            # 100L 이하는 아래 일반 계산으로 진행 (1인 가구에게 적합한 용량)
        
        elif "세탁기" in product.name:
            # 1인 가구: 7kg 이상은 과도하게 큼
            if capacity_value >= 7:
                return 0.05  # 매우 강한 감점
            elif capacity_value >= 5:
                return 0.2
            # 5kg 이하는 아래 일반 계산으로 진행
    
    # 일반적인 용량 적합도 계산 (1인 가구의 적정 용량 포함)
    if min_reasonable <= capacity_value <= max_reasonable:
        # 적정 범위 내: 이상적인 용량에 가까울수록 높은 점수
        diff = abs(capacity_value - ideal_capacity)
        ideal_range = (max_reasonable - min_reasonable) / 2
        
        if diff <= ideal_range * 0.2:
            return 1.0
        elif diff <= ideal_range * 0.4:
            return 0.8
        elif diff <= ideal_range * 0.6:
            return 0.6
        else:
            return 0.5
    
    elif capacity_value < min_reasonable:
        # 용량 부족: 약간 감점
        under_ratio = (min_reasonable - capacity_value) / min_reasonable
        return max(0.3, 0.7 - under_ratio * 0.4)
    
    else:
        # 용량 과다: 감점 (1인 가구는 이미 위에서 처리됨)
        if household_size > 1:
            over_ratio = (capacity_value - max_reasonable) / max_reasonable
            return max(0.2, 0.7 - over_ratio * 0.5)
        else:
            # 1인 가구는 이미 위에서 강하게 감점되었으므로 여기 도달하지 않음
            return 0.2


def score_features(spec: Dict, product: Product, profile: UserProfile) -> float:
    """
    기능 점수 (0.0 ~ 1.0) - 펫 기능, 기타 기능 평가
    
    Args:
        spec: 제품 스펙 딕셔너리
        product: 제품 인스턴스
        profile: 사용자 프로필
    
    Returns:
        float: 기능 점수 (0.0 ~ 1.0)
    """
    score = 0.7  # 기본 점수
    
    # 제품명과 설명에서 펫 관련 키워드 검색
    product_name = product.name.upper() if hasattr(product, 'name') else ""
    product_desc = (product.description.upper() if hasattr(product, 'description') and product.description else "")
    
    # 스펙 전체를 문자열로 변환하여 검색
    spec_text = ""
    if spec:
        spec_text = json.dumps(spec, ensure_ascii=False).upper()
    
    # 펫 관련 키워드
    pet_keywords = [
        "펫", "PET", "반려동물", "애완동물", "동물케어", 
        "펫케어", "PET CARE", "동물", "애완"
    ]
    
    has_pet_feature = any(keyword in product_name or keyword in product_desc or keyword in spec_text 
                          for keyword in pet_keywords)
    
    # 사용자가 반려동물을 키우지 않는 경우
    if not profile.has_pet:
        if has_pet_feature:
            # 펫 기능이 있는 제품: 강한 감점 (0.3 감점)
            score = max(0.1, score - 0.4)
            print(f"[Features Penalty] {product.name}: 펫 기능 감지, 반려동물 없음 사용자에게 감점")
    
    # 사용자가 반려동물을 키우는 경우
    elif profile.has_pet:
        if has_pet_feature:
            # 펫 기능이 있으면 가산점
            score = min(1.0, score + 0.2)
    
    return max(0.0, min(1.0, score))


def score_design(product: Product, profile: UserProfile) -> float:
    """디자인 점수 (vibe 기반, 0.0 ~ 1.0)"""
    vibe = profile.vibe.lower() if profile.vibe else ""
    category = product.category
    
    # 카테고리별 디자인 라인업 매칭
    if category in ["OBJET", "SIGNATURE"]:
        design_line = category
    elif "OBJET" in product.name.upper() or "오브제" in product.name:
        design_line = "OBJET"
    elif "SIGNATURE" in product.name.upper() or "시그니처" in product.name:
        design_line = "SIGNATURE"
    else:
        design_line = "default"
    
    # Vibe별 점수
    vibe_scores = VIBE_SCORES.get(vibe, VIBE_SCORES.get("modern", {}))
    return vibe_scores.get(design_line, vibe_scores.get("default", 0.5))


def score_energy_efficiency(spec: Dict, profile: UserProfile) -> float:
    """에너지 효율 점수 (0.0 ~ 1.0)"""
    # 에너지 효율 등급 확인
    energy_grade = get_spec_value(spec, "에너지등급", "")
    if not energy_grade:
        energy_grade = get_spec_value(spec, "에너지 효율 등급", "")
    
    # 등급별 점수 (1등급이 최고)
    grade_scores = {
        "1등급": 1.0,
        "1": 1.0,
        "2등급": 0.85,
        "2": 0.85,
        "3등급": 0.7,
        "3": 0.7,
        "4등급": 0.55,
        "4": 0.55,
        "5등급": 0.4,
        "5": 0.4,
    }
    
    if energy_grade:
        for grade, score in grade_scores.items():
            if grade in str(energy_grade):
                return score
    
    # 전력소비량 기반 점수 (낮을수록 좋음)
    power_consumption = score_power_consumption(spec, profile)
    return power_consumption


def score_audio_quality(spec: Dict, profile: UserProfile) -> float:
    """오디오 품질 점수 (0.0 ~ 1.0)"""
    # 오디오 관련 스펙 확인
    audio_specs = [
        get_spec_value(spec, "채널", ""),
        get_spec_value(spec, "출력", ""),
        get_spec_value(spec, "와트", ""),
        get_spec_value(spec, "사운드", ""),
    ]
    
    # 오디오 관련 스펙이 있으면 기본 점수
    if any(audio_specs):
        return 0.7
    
    # 기본값
    return 0.5


def score_connectivity(spec: Dict, profile: UserProfile) -> float:
    """연결성 점수 (0.0 ~ 1.0)"""
    # 연결 관련 스펙 확인
    connectivity_specs = [
        get_spec_value(spec, "블루투스", ""),
        get_spec_value(spec, "와이파이", ""),
        get_spec_value(spec, "WiFi", ""),
        get_spec_value(spec, "연결", ""),
        get_spec_value(spec, "포트", ""),
    ]
    
    # 연결 관련 스펙이 있으면 기본 점수
    if any(connectivity_specs):
        return 0.7
    
    # 기본값
    return 0.5


# ============================================================================
# 메인 스코어링 함수
# ============================================================================

def calculate_product_score(product: Product, profile: UserProfile) -> float:
    """
    제품의 종합 점수를 계산 (0.0 ~ 1.0)
    
    Args:
        product: Product 인스턴스
        profile: UserProfile 인스턴스
    
    Returns:
        float: 종합 점수 (0.0 ~ 1.0)
    """
    spec = parse_spec_json(product)
    if not spec:
        # 스펙이 없으면 기본 점수 (가격 적합도만)
        return score_price_match(product, profile) * 0.5
    
    category = product.category
    priority = profile.priority.lower() if profile.priority else ""
    
    # 카테고리별 가중치 가져오기
    weights = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["default"])
    
    # Priority별 가중치 조정
    multipliers = PRIORITY_MULTIPLIERS.get(priority, {})
    
    # 각 스펙 점수 계산
    scores = {}
    
    # TV 카테고리
    if category == "TV":
        scores["resolution"] = score_resolution(spec, profile)
        scores["brightness"] = score_brightness(spec, profile)
        scores["refresh_rate"] = score_refresh_rate(spec, profile)
        scores["panel_type"] = score_panel_type(spec, profile)
        scores["power_consumption"] = score_power_consumption(spec, profile)
        scores["size"] = score_size(spec, profile)
        scores["price_match"] = score_price_match(product, profile)
        scores["design"] = score_design(product, profile)
    
    # LIVING 카테고리 (오디오, 세탁기 등)
    elif category == "LIVING":
        # 오디오 관련 스펙 점수 (간단한 구현)
        scores["audio_quality"] = 0.7  # 기본값 (향후 확장 가능)
        scores["connectivity"] = 0.7
        scores["power_consumption"] = score_power_consumption(spec, profile)
        scores["size"] = score_size(spec, profile)
        scores["price_match"] = score_price_match(product, profile)
        scores["features"] = score_features(spec, product, profile)
        scores["design"] = score_design(product, profile)
        
        # 세탁기/건조기인 경우 용량 점수 추가
        if "세탁기" in product.name or "건조기" in product.name or "워시" in product.name.upper():
            scores["capacity"] = score_capacity(spec, profile, product)
    
    # KITCHEN 카테고리 (냉장고 등)
    elif category == "KITCHEN":
        scores["capacity"] = score_capacity(spec, profile, product)
        scores["energy_efficiency"] = score_power_consumption(spec, profile)
        scores["features"] = score_features(spec, product, profile)
        scores["size"] = score_size(spec, profile)
        scores["price_match"] = score_price_match(product, profile)
        scores["design"] = score_design(product, profile)
    
    # 기타 카테고리 (AI, OBJET, SIGNATURE, AIR 등)
    else:
        # 사용자가 선택한 카테고리와 제품 카테고리가 불일치하면 강한 감점
        target_categories = getattr(profile, 'target_categories', [])
        if target_categories and category not in target_categories:
            # 카테고리 불일치: 기본 점수의 30%만 적용
            base_score = score_price_match(product, profile) * 0.3
            return min(0.3, base_score)
        
        scores["price_match"] = score_price_match(product, profile)
        scores["features"] = score_features(spec, product, profile)
        scores["energy_efficiency"] = score_power_consumption(spec, profile)
        scores["size"] = score_size(spec, profile)
        scores["design"] = score_design(product, profile)
        
        # 냉장고가 다른 카테고리에 있을 경우 용량 점수 추가
        if "냉장고" in product.name or "냉동고" in product.name:
            scores["capacity"] = score_capacity(spec, profile, product)
    
    # 가중치 적용하여 종합 점수 계산
    total_score = 0.0
    total_weight = 0.0
    
    for key, weight in weights.items():
        if key in scores:
            # Priority별 가중치 조정
            multiplier = multipliers.get(key, 1.0)
            adjusted_weight = weight * multiplier
            total_score += scores[key] * adjusted_weight
            total_weight += adjusted_weight
    
    # 정규화 (0.0 ~ 1.0)
    if total_weight > 0:
        final_score = total_score / total_weight
    else:
        final_score = 0.5  # 기본값
    
    # Priority별 추가 보정 (개인화 강화)
    # 같은 제품이라도 priority에 따라 최종 점수가 달라지도록
    if priority == "tech":
        # 기술 우선: 기술 관련 점수가 높으면 추가 보너스
        tech_score = (scores.get("resolution", 0) + scores.get("refresh_rate", 0) + 
                     scores.get("brightness", 0) + scores.get("features", 0)) / 4
        if tech_score > 0.7:
            final_score += 0.05
    elif priority == "design":
        # 디자인 우선: 디자인 점수가 높으면 추가 보너스
        if scores.get("design", 0) > 0.7:
            final_score += 0.05
    elif priority == "eco":
        # 에너지 효율 우선: 에너지 점수가 높으면 추가 보너스
        eco_score = (scores.get("power_consumption", 0) + 
                    scores.get("energy_efficiency", 0)) / 2
        if eco_score > 0.7:
            final_score += 0.05
    elif priority == "value":
        # 가성비 우선: 가격 적합도가 높으면 추가 보너스
        if scores.get("price_match", 0) > 0.7:
            final_score += 0.05
    
    # Vibe별 추가 보정 (개인화 강화)
    vibe = profile.vibe.lower() if profile.vibe else ""
    design_score = scores.get("design", 0)
    if vibe == "modern" and design_score > 0.8:
        final_score += 0.03
    elif vibe == "cozy" and design_score > 0.75:
        final_score += 0.03
    elif vibe == "luxury" and design_score > 0.85:
        final_score += 0.05
    elif vibe == "pop" and design_score > 0.75:
        final_score += 0.03
    
    # 가족 인원과 반려동물 정보 기반 추가 점수 조정
    household_size = getattr(profile, '_household_size_int', 2)
    has_pet = getattr(profile, 'has_pet', False) or getattr(profile, '_has_pet', False)
    
    # 가족 인원 기반 점수 조정
    product_name_upper = product.name.upper()
    spec_str = json.dumps(spec, ensure_ascii=False).upper() if spec else ""
    
    # 용량 관련 키워드
    large_capacity_keywords = ['대용량', '4인', '5인', '6인', '870L', '900L', '1000L', 'LARGE', 'XL', '대형']
    small_capacity_keywords = ['소형', '1인', '300L', '400L', '500L', 'SMALL', 'S', '소형']
    
    # 가족 구성원 수에 따른 용량 적합도 보정 (더 세밀하게)
    if household_size == 1:
        # 1인 가구: 작은 용량 제품에 가산점
        if any(keyword in product_name_upper or keyword in spec_str for keyword in small_capacity_keywords):
            final_score += 0.15
        # 큰 용량 제품에 감점
        elif any(keyword in product_name_upper or keyword in spec_str for keyword in large_capacity_keywords):
            final_score -= 0.2
    elif household_size == 2:
        # 2인 가구: 중간 용량 선호, 큰 용량은 약간 감점
        if any(keyword in product_name_upper or keyword in spec_str for keyword in large_capacity_keywords):
            final_score -= 0.05  # 약간 감점
    elif household_size == 3:
        # 3인 가구: 중대형 용량 선호
        if any(keyword in product_name_upper or keyword in spec_str for keyword in large_capacity_keywords):
            final_score += 0.08
        elif any(keyword in product_name_upper or keyword in spec_str for keyword in small_capacity_keywords):
            final_score -= 0.1
    elif household_size >= 4:
        # 4인 이상 가족: 큰 용량 제품에 가산점
        if any(keyword in product_name_upper or keyword in spec_str for keyword in large_capacity_keywords):
            final_score += 0.15
        # 작은 용량 제품에 감점
        elif any(keyword in product_name_upper or keyword in spec_str for keyword in small_capacity_keywords):
            final_score -= 0.2
    
    # 반려동물 기반 점수 조정
    pet_keywords = ['펫', 'PET', '반려동물', '애완동물', '동물', '털', '냄새']
    if has_pet:
        # 반려동물이 있는 경우: 반려동물 관련 기능이 있는 제품에 가산점
        if any(keyword in product_name_upper or keyword in spec_str for keyword in pet_keywords):
            final_score += 0.2
    else:
        # 반려동물이 없는 경우: 반려동물 전용 기능이 있는 제품에 약간 감점
        # (완전히 제외하지는 않고 약간만 감점)
        if any(keyword in product_name_upper or keyword in spec_str for keyword in pet_keywords):
            final_score -= 0.1
    
    # 최종 점수 클리핑
    return max(0.0, min(1.0, final_score))

