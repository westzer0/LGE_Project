"""
제품 종류 분류 유틸리티

제품명에서 제품 종류를 추출하고 분류합니다.
"""
import re
from typing import Optional, Dict, List
from ..models import Product


# 제품 종류 키워드 매핑 (우선순위 순서대로 - 더 구체적인 것부터)
PRODUCT_TYPE_KEYWORDS = {
    # TV
    'TV': ['TV', '티비', '올레드', 'OLED', 'QNED', '나노셀', '울트라', 'QLED'],
    
    # 에어컨 관련
    '에어컨': ['에어컨', 'AIR CONDITIONER', '휘센', 'WHISEN', 'CONDITIONER'],
    'CONDITIONER': ['CONDITIONER', '에어컨', 'AIR CONDITIONER'],
    
    # 세탁 관련
    'LAUNDRY': ['LAUNDRY', '세탁기', '트롬', 'WASH'],
    '세탁기': ['세탁기', '트롬', '워시', 'WASH', '통돌이'],
    '의류건조기': ['의류건조기', '건조기', 'DRY', '드라이', '건조', '건조의류'],
    '건조기': ['건조기', 'DRY', '드라이', '건조'],
    '워시타워': ['워시타워', '워시타', 'WASHTOWER', '세탁+건조'],
    '워시콤보': ['워시콤보', '워시콤', '세탁+건조', '콤보', 'WASHCOMBO'],
    
    # 공기 관련
    '공기청정기': ['공기청정기', '공청', '에어케어', 'AIR PURIFIER', '공기', '퓨리케어 360'],
    '제습기': ['제습기', 'DEHUMIDIFIER', '제습'],
    '가습기': ['가습기', 'HUMIDIFIER', '가습'],
    
    # 안마의자
    '안마의자': ['안마의자', '안마', 'MASSAGE', '쇼파', 'MASSAGE CHAIR'],
    
    # 청소기
    '청소기': ['청소기', '코드제로', 'CODEZERO', '로봇청소기', '로보킹', '로봇', 'A5', 'A7', 'A9', 'R5', 'R9', 'M9', 'VACUUM'],
    
    # 주방가전
    '식기세척기': ['식기세척기', '식세기', 'DISHWASHER', 'DUE'],
    '와인셀러': ['와인셀러', '와인', 'WINE', 'WINE CELLAR'],
    '전기레인지': ['전기레인지', '인덕션', '레인지', 'INDUCTION', 'RANGE'],
    '정수기': ['정수기', '퓨리케어', 'PURICARE', '정수', 'WATER PURIFIER'],
    '맥주제조기': ['맥주제조기', '홈브루', '맥주', 'BREW', 'HOMEBREW'],
    '광파오븐전자레인지': ['광파오븐', '전자레인지', '레인지', 'MICROWAVE', '큐커', '오븐레인지'],
    '전자레인지': ['전자레인지', 'MICROWAVE', '큐커'],
    '오븐': ['오븐', 'OVEN'],
    '김치냉장고': ['김치냉장고', '김치', 'KIMCHI'],
    '냉장고': ['냉장고', '디오스', 'DIOS', '컨버터블', '일반냉장고', '냉동고', 'REFRIGERATOR'],
    
    # 기타
    '스타일러': ['스타일러', 'STYLER', '스티머', '의류관리기'],
    '모니터': ['모니터', 'MONITOR', '게이밍모니터'],
}


def extract_product_type(product: Product) -> Optional[str]:
    """
    제품명에서 제품 종류를 추출합니다.
    
    Args:
        product: Product 객체
        
    Returns:
        제품 종류 (예: '세탁기', '청소기', '냉장고') 또는 None
    """
    if not product or not product.name:
        return None
    
    product_name_upper = product.name.upper()
    product_name = product.name
    
    # 제품 종류별로 키워드 매칭 (우선순위 순서대로)
    for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            keyword_upper = keyword.upper()
            if keyword_upper in product_name_upper or keyword in product_name:
                return product_type
    
    # 카테고리 기반 기본 분류
    category = product.category
    if category == 'TV':
        return 'TV'
    elif category == 'KITCHEN':
        # 주방가전은 더 세분화 필요
        if any(kw in product_name_upper for kw in ['냉장고', 'DIOS', '컨버터블']):
            return '냉장고'
        elif any(kw in product_name_upper for kw in ['식기', 'DISH']):
            return '식기세척기'
        elif any(kw in product_name_upper for kw in ['정수', 'PURI']):
            return '정수기'
        elif any(kw in product_name_upper for kw in ['오븐', 'OVEN']):
            return '오븐'
        elif any(kw in product_name_upper for kw in ['레인지', 'MICRO']):
            return '전자레인지'
    elif category == 'LIVING':
        # 생활가전도 세분화
        if any(kw in product_name_upper for kw in ['세탁', 'WASH', '트롬']):
            return '세탁기'
        elif any(kw in product_name_upper for kw in ['청소', 'CODEZERO', '로봇']):
            return '청소기'
        elif any(kw in product_name_upper for kw in ['스타일러', 'STYLER']):
            return '스타일러'
    elif category == 'AIR':
        if any(kw in product_name_upper for kw in ['공기청정', 'AIR PURIFIER']):
            return '공기청정기'
        elif any(kw in product_name_upper for kw in ['제습', 'DEHUMID']):
            return '제습기'
        elif any(kw in product_name_upper for kw in ['에어컨', 'AIR CONDITIONER']):
            return '에어컨'
    
    return None


def get_product_types_for_scenario(user_profile: dict, onboarding_data: dict) -> List[str]:
    """
    시나리오별 추천할 제품 종류 목록을 반환합니다.
    
    Args:
        user_profile: 사용자 프로필
        onboarding_data: 온보딩 데이터
        
    Returns:
        추천할 제품 종류 목록
    """
    household_size = user_profile.get('household_size', 2)
    housing_type = user_profile.get('housing_type', 'apartment')
    cooking = onboarding_data.get('cooking', 'sometimes')
    laundry = onboarding_data.get('laundry', 'weekly')
    media = onboarding_data.get('media', 'balanced')
    
    product_types = []
    
    # 모든 시나리오에 공통으로 필요한 제품
    product_types.append('냉장고')
    
    # 세탁 관련
    if laundry in ['daily', 'weekly', 'few_times']:
        if household_size >= 4:
            product_types.append('워시타워')  # 4인 이상은 워시타워
        elif household_size >= 2:
            product_types.append('세탁기')
            product_types.append('건조기')
        else:
            product_types.append('세탁기')
    
    # 요리 관련
    if cooking in ['high', 'often']:
        product_types.append('식기세척기')
        product_types.append('오븐')
    
    # 청소 관련 (모든 시나리오)
    product_types.append('청소기')
    
    # TV/미디어
    if media != 'none':
        product_types.append('TV')
    
    # 에어컨/공기청정 (주거 형태에 따라)
    if housing_type in ['apartment', 'detached', 'villa']:
        product_types.append('에어컨')
        product_types.append('공기청정기')
    
    # 스타일러 (선택적)
    if household_size >= 3:
        product_types.append('스타일러')
    
    return list(set(product_types))  # 중복 제거


def group_products_by_type(products: List[Product]) -> Dict[str, List[Product]]:
    """
    제품 리스트를 제품 종류별로 그룹화합니다.
    
    Args:
        products: 제품 리스트
        
    Returns:
        제품 종류별 그룹화된 딕셔너리
    """
    grouped = {}
    
    for product in products:
        product_type = extract_product_type(product)
        
        if product_type:
            if product_type not in grouped:
                grouped[product_type] = []
            grouped[product_type].append(product)
        else:
            # 종류를 찾지 못한 경우 '기타'로 분류
            if '기타' not in grouped:
                grouped['기타'] = []
            grouped['기타'].append(product)
    
    return grouped

