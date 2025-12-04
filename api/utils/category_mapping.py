"""
MAIN_CATEGORY (Oracle DB)와 Django Product.category 매핑

Oracle DB의 MAIN_CATEGORY 값과 Django Product 모델의 category 필드를 매핑합니다.
"""

# MAIN_CATEGORY → Django category 매핑
MAIN_CATEGORY_TO_DJANGO_CATEGORY = {
    # TV/오디오 관련
    'TV': 'TV',
    '오디오': 'TV',
    '사운드바': 'TV',
    '프로젝터': 'TV',
    '스탠바이미': 'TV',
    
    # 주방가전 관련
    '냉장고': 'KITCHEN',
    '김치냉장고': 'KITCHEN',
    '전기레인지': 'KITCHEN',
    '식기세척기': 'KITCHEN',
    '오븐': 'KITCHEN',
    '인덕션': 'KITCHEN',
    '전자레인지': 'KITCHEN',
    '광파오븐전자레인지': 'KITCHEN',
    
    # 생활가전 관련
    '세탁': 'LIVING',
    '세탁기': 'LIVING',
    '건조기': 'LIVING',
    '청소기': 'LIVING',
    '의류관리기': 'LIVING',
    '정수기': 'LIVING',
    '가습기': 'LIVING',
    '제습기': 'LIVING',
    '공기청정기': 'LIVING',
    '식물생활가전': 'LIVING',
    '신발관리': 'LIVING',
    
    # 에어컨/에어케어 관련
    '에어컨': 'AIR',
    '시스템 에어컨': 'AIR',
    '환기 시스템': 'AIR',
    
    # AI Home
    'AIHome': 'AI',
    
    # OBJET
    'OBJET': 'OBJET',
    
    # SIGNATURE
    'SIGNATURE': 'SIGNATURE',
    
    # 기타
    '상업용 디스플레이': 'TV',
    '컨버터블 패키': 'KITCHEN',
    '맥주제조기': 'KITCHEN',
    '안마의자': 'LIVING',
    '와인셀러': 'KITCHEN',
}

# 역매핑: Django category → 가능한 MAIN_CATEGORY 리스트
DJANGO_CATEGORY_TO_MAIN_CATEGORIES = {
    'TV': ['TV', '오디오', '사운드바', '프로젝터', '스탠바이미', '상업용 디스플레이'],
    'KITCHEN': ['냉장고', '김치냉장고', '전기레인지', '식기세척기', '오븐', '인덕션', '전자레인지', 
                '광파오븐전자레인지', '컨버터블 패키', '맥주제조기', '와인셀러'],
    'LIVING': ['세탁', '세탁기', '건조기', '청소기', '의류관리기', '정수기', '가습기', '제습기',
               '공기청정기', '식물생활가전', '신발관리', '안마의자'],
    'AIR': ['에어컨', '시스템 에어컨', '환기 시스템'],
    'AI': ['AIHome'],
    'OBJET': ['OBJET'],
    'SIGNATURE': ['SIGNATURE'],
}


def map_main_category_to_django_category(main_category: str) -> str:
    """
    Oracle DB의 MAIN_CATEGORY를 Django Product.category로 변환
    
    Args:
        main_category: Oracle DB의 MAIN_CATEGORY 값 (예: "TV", "냉장고")
    
    Returns:
        Django Product.category 값 (예: "TV", "KITCHEN")
    """
    return MAIN_CATEGORY_TO_DJANGO_CATEGORY.get(main_category, 'LIVING')  # 기본값: LIVING


def get_django_categories_for_main_categories(main_categories: list) -> list:
    """
    MAIN_CATEGORY 리스트를 Django category 리스트로 변환 (중복 제거)
    
    Args:
        main_categories: MAIN_CATEGORY 리스트 (예: ["TV", "냉장고", "에어컨"])
    
    Returns:
        Django category 리스트 (예: ["TV", "KITCHEN", "AIR"])
    """
    django_categories = []
    for main_cat in main_categories:
        django_cat = map_main_category_to_django_category(main_cat)
        if django_cat not in django_categories:
            django_categories.append(django_cat)
    return django_categories


def validate_category_match(product_category: str, expected_main_category: str) -> bool:
    """
    제품의 Django category가 예상된 MAIN_CATEGORY와 매칭되는지 확인
    
    Args:
        product_category: Django Product.category 값
        expected_main_category: 예상된 MAIN_CATEGORY 값
    
    Returns:
        매칭 여부
    """
    mapped_category = map_main_category_to_django_category(expected_main_category)
    return product_category == mapped_category

