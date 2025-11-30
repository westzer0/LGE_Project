from dataclasses import dataclass
from typing import List
from .models import Product


@dataclass
class UserProfile:
    """사용자 프로필 데이터"""
    vibe: str = ""
    household_size: str = ""
    has_pet: bool = False
    housing_type: str = ""
    main_space: str = ""
    space_size: str = ""
    cook_freq: str = ""
    laundry_pattern: str = ""
    media_usage: str = ""
    priority: str = ""  # "design", "tech", "eco", "value"
    budget_level: str = ""  # "budget", "standard", "premium", "luxury"
    target_categories: List[str] = None

    def __post_init__(self):
        if self.target_categories is None:
            self.target_categories = []


def build_profile(payload: dict) -> UserProfile:
    """JSON payload에서 UserProfile 생성"""
    return UserProfile(
        vibe=payload.get("vibe", ""),
        household_size=payload.get("household_size", ""),
        has_pet=payload.get("has_pet", False),
        housing_type=payload.get("housing_type", ""),
        main_space=payload.get("main_space", ""),
        space_size=payload.get("space_size", ""),
        cook_freq=payload.get("cook_freq", ""),
        laundry_pattern=payload.get("laundry_pattern", ""),
        media_usage=payload.get("media_usage", ""),
        priority=payload.get("priority", ""),
        budget_level=payload.get("budget_level", "standard"),
        target_categories=payload.get("target_categories", []),
    )


def compute_filters(profile: UserProfile) -> dict:
    """UserProfile에서 필터 조건 계산"""
    filters = {
        "sort_by": "price",
        "price_flag": False,
        "eco_flag": False,
        "min_price": 0,
        "max_price": float('inf'),
        "design_tags": [],
    }

    # priority에 따른 정렬 및 플래그 설정
    if profile.priority == "design":
        filters["sort_by"] = "name"  # 디자인 우선은 이름순 (실제로는 design_tags 기반 정렬 예정)
        filters["design_tags"] = _get_design_tags(profile.vibe)
    elif profile.priority == "tech":
        filters["sort_by"] = "name"  # 기술 우선
    elif profile.priority == "eco":
        filters["sort_by"] = "price"
        filters["eco_flag"] = True
    elif profile.priority == "value":
        filters["sort_by"] = "discount_price"
        filters["price_flag"] = True

    # budget_level에 따른 가격 범위 설정
    if profile.budget_level == "budget":
        filters["min_price"] = 0
        filters["max_price"] = 500000
    elif profile.budget_level == "standard":
        filters["min_price"] = 500000
        filters["max_price"] = 2000000
    elif profile.budget_level == "premium":
        filters["min_price"] = 2000000
        filters["max_price"] = 5000000
    elif profile.budget_level == "luxury":
        filters["min_price"] = 5000000
        filters["max_price"] = float('inf')

    return filters


def _get_design_tags(vibe: str) -> List[str]:
    """vibe에 따른 design_tags 리스트 생성 (향후 필터링용)"""
    vibe_map = {
        "modern": ["OBJET", "SIGNATURE"],
        "cozy": ["OBJET"],
        "unique": ["OBJET"],
        "luxury": ["SIGNATURE"],
    }
    return vibe_map.get(vibe.lower(), [])


def recommend_products(profile: UserProfile) -> List[dict]:
    """UserProfile 기반으로 제품 추천"""
    filters = compute_filters(profile)

    # 기본 쿼리셋: 활성 제품만
    queryset = Product.objects.filter(is_active=True)

    # 카테고리 필터
    if profile.target_categories:
        queryset = queryset.filter(category__in=profile.target_categories)
    # target_categories가 없으면 모든 카테고리에서 추천

    # 가격 필터
    if filters["min_price"] > 0:
        queryset = queryset.filter(price__gte=filters["min_price"])
    if filters["max_price"] < float('inf'):
        queryset = queryset.filter(price__lte=filters["max_price"])

    # 정렬
    if filters["sort_by"] == "discount_price":
        # discount_price가 있는 것만 필터링하고 오름차순 정렬
        queryset = queryset.filter(discount_price__isnull=False).order_by("discount_price")
    else:
        # 기본 정렬: discount_price 내림차순, price 오름차순
        queryset = queryset.order_by("-discount_price", "price")

    # 상위 3개만 선택
    products = list(queryset[:3])

    # dict 리스트로 변환
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "name": product.name,
            "model_number": product.model_number,
            "category": product.category,
            "category_display": product.get_category_display(),
            "description": product.description,
            "price": float(product.price),
            "discount_price": float(product.discount_price) if product.discount_price else None,
            "image_url": product.image_url,
            "reason": build_reason(profile, product),
        })

    return result


def build_reason(profile: UserProfile, product: Product) -> str:
    """추천 이유 생성"""
    reasons = []

    # household_size 기반
    if profile.household_size:
        if profile.household_size in ["1", "1인"]:
            reasons.append("1인 가구에 적합한")
        elif profile.household_size in ["2", "2인", "신혼"]:
            reasons.append("신혼부부에게 추천하는")
        elif profile.household_size in ["3", "4", "3~4인"]:
            reasons.append("가족 구성원 수에 맞는")

    # priority 기반
    if profile.priority == "design":
        reasons.append("디자인이 뛰어난")
    elif profile.priority == "tech":
        reasons.append("최신 기술이 적용된")
    elif profile.priority == "eco":
        reasons.append("에너지 효율이 우수한")
    elif profile.priority == "value":
        reasons.append("가성비가 좋은")

    # budget_level 기반
    if profile.budget_level == "budget":
        reasons.append("합리적인 가격의")
    elif profile.budget_level == "premium":
        reasons.append("프리미엄 라인업의")
    elif profile.budget_level == "luxury":
        reasons.append("럭셔리 라인업의")

    # 기본 메시지
    if not reasons:
        reasons.append("추천하는")

    return " ".join(reasons) + f" {product.name}"

