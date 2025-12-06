"""
취향별 독립적인 Scoring Logic 적용

각 취향 조합(taste_id)에 맞는 독립적인 scoring logic을 적용합니다.
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from django.conf import settings
from ..models import Product
from .scoring import (
    score_resolution, score_brightness, score_refresh_rate,
    score_panel_type, score_power_consumption, score_size,
    score_price_match, score_capacity, score_energy_efficiency,
    score_features, score_design, score_audio_quality, score_connectivity,
    get_spec_value
)
from ..rule_engine import UserProfile


# Scoring Logic 캐시
_taste_scoring_logics = None
_taste_id_to_logic = None


def load_taste_scoring_logics() -> List[Dict]:
    """Scoring Logic JSON 파일 로드"""
    global _taste_scoring_logics
    
    if _taste_scoring_logics is not None:
        return _taste_scoring_logics
    
    logic_file = Path(__file__).parent.parent / 'scoring_logic' / 'taste_scoring_logics.json'
    
    if not logic_file.exists():
        return []
    
    with open(logic_file, 'r', encoding='utf-8') as f:
        _taste_scoring_logics = json.load(f)
    
    return _taste_scoring_logics


def get_logic_for_taste_id(taste_id: int, onboarding_data: Dict = None) -> Optional[Dict]:
    """
    taste_id에 해당하는 Scoring Logic 반환
    
    새로운 TasteScoringLogicService를 사용하여 taste별 독립적인 logic을 제공합니다.
    각 taste별로 완전히 독립적인 scoring 로직을 적용할 수 있습니다.
    
    Args:
        taste_id: 취향 ID
        onboarding_data: 온보딩 데이터 (동적 logic 생성 시 사용)
    
    Returns:
        Scoring Logic 딕셔너리
    """
    # 새로운 서비스 사용 (taste별 독립적인 logic 제공)
    from ..services.taste_scoring_logic_service import taste_scoring_logic_service
    
    logic = taste_scoring_logic_service.get_logic_for_taste(taste_id, onboarding_data)
    
    return logic


def calculate_product_score_with_taste_logic(
    product: Product,
    profile: UserProfile,
    taste_id: Optional[int] = None,
    onboarding_data: Optional[Dict] = None
) -> float:
    """
    취향별 독립적인 Scoring Logic을 적용한 제품 점수 계산
    
    Args:
        product: 제품 객체
        profile: 사용자 프로필
        taste_id: 취향 ID (선택사항, 없으면 기본 scoring 사용)
        onboarding_data: 온보딩 데이터 (동적 logic 생성 시 사용)
    
    Returns:
        제품 점수 (0.0 ~ 1.0)
    """
    # taste_id가 없으면 기본 scoring 사용
    if taste_id is None:
        from .scoring import calculate_product_score
        return calculate_product_score(product, profile)
    
    # 해당 taste_id의 Scoring Logic 가져오기 (온보딩 데이터 기반 동적 생성 가능)
    logic = get_logic_for_taste_id(taste_id, onboarding_data)
    if logic is None:
        # Logic이 없으면 기본 scoring 사용
        from .scoring import calculate_product_score
        return calculate_product_score(product, profile)
    
    # Logic의 가중치와 규칙 적용
    return _apply_scoring_logic(product, profile, logic)


def _apply_scoring_logic(product: Product, profile: UserProfile, logic: Dict) -> float:
    """Scoring Logic 적용"""
    # 제품 스펙 파싱
    from .scoring import parse_spec_json
    spec = parse_spec_json(product)
    
    # MAIN_CATEGORY 결정 (product.spec.spec_json에서 가져오기)
    main_category = None
    if spec:
        main_category = spec.get('MAIN_CATEGORY', '').strip() if isinstance(spec.get('MAIN_CATEGORY'), str) else None
    
    # MAIN_CATEGORY가 없으면 Django category를 MAIN_CATEGORY로 매핑
    if not main_category:
        from .category_mapping import map_main_category_to_django_category, DJANGO_CATEGORY_TO_MAIN_CATEGORIES
        django_category = product.category or "LIVING"
        
        # Django category에 해당하는 첫 번째 MAIN_CATEGORY 사용 (fallback)
        possible_main_categories = DJANGO_CATEGORY_TO_MAIN_CATEGORIES.get(django_category, [])
        if possible_main_categories:
            main_category = possible_main_categories[0]  # 첫 번째를 기본값으로
        else:
            main_category = "TV"  # 최종 fallback
    
    # Logic의 가중치 가져오기 (MAIN_CATEGORY 직접 사용)
    weights = logic.get('weights', {}).get(main_category, {})
    
    # MAIN_CATEGORY에 대한 가중치가 없으면 Django category로 매핑해서 시도
    if not weights:
        from .category_mapping import map_main_category_to_django_category
        django_category = map_main_category_to_django_category(main_category)
        weights = logic.get('weights', {}).get(django_category, {})
    
    # 여전히 없으면 기본 가중치 사용
    if not weights:
        from .scoring import CATEGORY_WEIGHTS
        from .category_mapping import map_main_category_to_django_category
        django_category = map_main_category_to_django_category(main_category)
        weights = CATEGORY_WEIGHTS.get(django_category, CATEGORY_WEIGHTS.get('default', {}))
    
    # 각 속성별 점수 계산 (모든 카테고리에 대해 동적으로 처리)
    scores = {}
    
    # weights에 정의된 모든 속성에 대해 점수 계산
    if 'resolution' in weights:
        scores['resolution'] = score_resolution(spec, profile)
    if 'brightness' in weights:
        scores['brightness'] = score_brightness(spec, profile)
    if 'refresh_rate' in weights:
        scores['refresh_rate'] = score_refresh_rate(spec, profile)
    if 'panel_type' in weights:
        scores['panel_type'] = score_panel_type(spec, profile)
    if 'power_consumption' in weights:
        scores['power_consumption'] = score_power_consumption(spec, profile)
    if 'size' in weights:
        scores['size'] = score_size(spec, profile)
    if 'price_match' in weights:
        scores['price_match'] = score_price_match(product, profile)
    if 'features' in weights:
        scores['features'] = score_features(spec, product, profile)
    if 'capacity' in weights:
        scores['capacity'] = score_capacity(spec, profile, product)
    if 'energy_efficiency' in weights:
        scores['energy_efficiency'] = score_energy_efficiency(spec, profile)
    if 'design' in weights:
        scores['design'] = score_design(product, profile)
    if 'audio_quality' in weights:
        scores['audio_quality'] = score_audio_quality(spec, profile)
    if 'connectivity' in weights:
        scores['connectivity'] = score_connectivity(spec, profile)
    
    # 가중 평균 계산
    weighted_score = 0.0
    total_weight = 0.0
    
    for attr, weight in weights.items():
        if attr in scores:
            weighted_score += scores[attr] * weight
            total_weight += weight
    
    if total_weight > 0:
        base_score = weighted_score / total_weight
    else:
        base_score = 0.5
    
    # 보너스 적용
    bonuses = logic.get('bonuses', [])
    for bonus in bonuses:
        if _check_bonus_condition(product, spec, bonus):
            base_score += bonus['bonus']
    
    # 페널티 적용
    penalties = logic.get('penalties', [])
    for penalty in penalties:
        if _check_penalty_condition(product, spec, penalty):
            base_score += penalty['penalty']  # penalty는 이미 음수
    
    # 점수 범위 제한 (0.0 ~ 1.0)
    final_score = max(0.0, min(1.0, base_score))
    
    return final_score


def _check_bonus_condition(product: Product, spec: Dict, bonus: Dict) -> bool:
    """보너스 조건 확인"""
    condition = bonus.get('condition', '')
    product_name = product.name.upper()
    
    if 'OBJET' in condition or '오브제' in condition:
        return 'OBJET' in product_name or '오브제' in product.name
    elif 'SIGNATURE' in condition or '시그니처' in condition:
        return 'SIGNATURE' in product_name or '시그니처' in product.name
    elif 'AI' in condition or '스마트' in condition:
        return 'AI' in product_name or '스마트' in product.name
    elif '대용량' in condition or '800L' in condition:
        capacity_str = get_spec_value(spec, "용량", "") or get_spec_value(spec, "냉장실 용량", "")
        if capacity_str:
            import re
            capacity_match = re.search(r'(\d+)', str(capacity_str))
            if capacity_match:
                capacity = int(capacity_match.group(1))
                return capacity >= 800
    elif '소형' in condition or '컴팩트' in condition or '300L' in condition:
        capacity_str = get_spec_value(spec, "용량", "") or get_spec_value(spec, "냉장실 용량", "")
        if capacity_str:
            import re
            capacity_match = re.search(r'(\d+)', str(capacity_str))
            if capacity_match:
                capacity = int(capacity_match.group(1))
                return capacity <= 300
    
    return False


def _check_penalty_condition(product: Product, spec: Dict, penalty: Dict) -> bool:
    """페널티 조건 확인"""
    condition = penalty.get('condition', '')
    product_name = product.name.upper()
    
    if '대용량' in condition or '800L' in condition:
        capacity_str = get_spec_value(spec, "용량", "") or get_spec_value(spec, "냉장실 용량", "")
        if capacity_str:
            import re
            capacity_match = re.search(r'(\d+)', str(capacity_str))
            if capacity_match:
                capacity = int(capacity_match.group(1))
                return capacity >= 800
    elif '소형' in condition or '300L' in condition:
        capacity_str = get_spec_value(spec, "용량", "") or get_spec_value(spec, "냉장실 용량", "")
        if capacity_str:
            import re
            capacity_match = re.search(r'(\d+)', str(capacity_str))
            if capacity_match:
                capacity = int(capacity_match.group(1))
                return capacity <= 300
    elif '기본형' in condition or '실용형' in condition:
        # 기본형 디자인은 OBJET, SIGNATURE가 아닌 제품
        return 'OBJET' not in product_name and 'SIGNATURE' not in product_name and '오브제' not in product.name and '시그니처' not in product.name
    
    return False

