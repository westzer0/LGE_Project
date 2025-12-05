"""
CSV 파일에서 제품 이미지 URL을 가져오는 유틸리티 함수
"""
import os
import csv
import json
import ast
from django.conf import settings


def get_image_url_from_csv(product_name, category_hint=None):
    """
    CSV 파일에서 제품명으로 이미지 URL을 찾아 반환하는 함수
    
    Args:
        product_name (str): 찾을 제품명 (예: "LG 디오스 냉장고")
        category_hint (str, optional): 카테고리 힌트 (예: "냉장고", "TV")
    
    Returns:
        str: 이미지 URL (첫 번째 이미지) 또는 기본 placeholder URL
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 프로젝트 루트 경로 가져오기
    base_dir = settings.BASE_DIR
    csv_base_path = os.path.join(base_dir, 'data', '제품스펙')
    
    logger.debug(f'이미지 검색 시작: 제품명="{product_name}", 카테고리 힌트="{category_hint}"')
    
    # 경로 확인
    if not os.path.exists(csv_base_path):
        logger.error(f'CSV 기본 경로가 존재하지 않음: {csv_base_path}')
        return 'https://via.placeholder.com/800x600?text=Path+Not+Found'
    
    # 카테고리 힌트 매핑 (제품 타입 -> 폴더명)
    category_mapping = {
        # 주방가전
        '냉장고': '주방가전',
        '김치냉장고': '주방가전',
        '식기세척기': '주방가전',
        '광파오븐': '주방가전',
        '전자레인지': '주방가전',
        '정수기': '주방가전',
        '와인셀러': '주방가전',
        '전기레인지': '주방가전',
        '맥주제조기': '주방가전',
        '컨버터블': '주방가전',
        
        # 생활가전
        '세탁': '생활가전',
        '세탁기': '생활가전',
        '청소기': '생활가전',
        '의류건조기': '생활가전',
        '의류관리기': '생활가전',
        '워시콤보': '생활가전',
        '워시타워': '생활가전',
        '안마의자': '생활가전',
        '신발관리': '생활가전',
        '식물생활가전': '생활가전',
        
        # TV오디오
        'TV': 'TV오디오',
        '스탠바이미': 'TV오디오',
        '오디오': 'TV오디오',
        '프로젝터': 'TV오디오',
        '디스플레이': 'TV오디오',
        
        # 에어컨에어케어
        '에어컨': '에어컨에어케어',
        '공기청정기': '에어컨에어케어',
        '가습기': '에어컨에어케어',
        '제습기': '에어컨에어케어',
        '환기': '에어컨에어케어',
        
        # PC모니터
        '모니터': 'PC모니터',
        '노트북': 'PC모니터',
        '데스크톱': 'PC모니터',
        '태블릿': 'PC모니터',
        
        # AIHome
        'AIHome': 'AIHome',
        'AI홈': 'AIHome',
    }
    
    # 검색할 폴더 목록 결정
    search_folders = []
    
    if category_hint:
        # 카테고리 힌트가 있으면 매핑된 폴더를 우선 검색
        mapped_category = category_mapping.get(category_hint)
        if mapped_category:
            search_folders.append(mapped_category)
    
    # 모든 폴더를 검색 대상에 추가 (힌트가 있으면 그 다음에 검색)
    all_categories = ['AIHome', 'PC모니터', 'TV오디오', '주방가전', '생활가전', '에어컨에어케어']
    for cat in all_categories:
        if cat not in search_folders:
            search_folders.append(cat)
    
    # 각 폴더를 순회하며 CSV 파일 검색
    for category_folder in search_folders:
        category_path = os.path.join(csv_base_path, category_folder)
        
        # 폴더가 존재하지 않으면 건너뛰기
        if not os.path.exists(category_path):
            continue
        
        # 폴더 내의 모든 CSV 파일 검색
        csv_files = [f for f in os.listdir(category_path) if f.endswith('.csv')]
        
        for csv_file in csv_files:
            csv_file_path = os.path.join(category_path, csv_file)
            
            try:
                # UTF-8 인코딩으로 시도
                image_url = _search_in_csv_file(csv_file_path, product_name, encoding='utf-8')
                if image_url:
                    logger.debug(f'이미지 찾음: {csv_file} -> {image_url[:100]}')
                    return image_url
            except (UnicodeDecodeError, Exception):
                try:
                    # UTF-8 실패 시 CP949로 시도
                    image_url = _search_in_csv_file(csv_file_path, product_name, encoding='cp949')
                    if image_url:
                        return image_url
                except Exception as e:
                    # 에러 발생 시 다음 파일로
                    continue
    
    # 찾지 못한 경우 기본 placeholder 이미지 반환
    logger.warning(f'이미지를 찾을 수 없음: 제품명="{product_name}", 카테고리 힌트="{category_hint}"')
    return 'https://via.placeholder.com/800x600?text=Image+Not+Found'


def _search_in_csv_file(csv_file_path, product_name, encoding='utf-8'):
    """
    단일 CSV 파일에서 제품명을 검색하여 이미지 URL 반환
    
    Args:
        csv_file_path (str): CSV 파일 경로
        product_name (str): 찾을 제품명
        encoding (str): 파일 인코딩
    
    Returns:
        str or None: 이미지 URL 또는 None
    """
    try:
        with open(csv_file_path, 'r', encoding=encoding, errors='ignore') as f:
            # CSV 파일 읽기 (BOM 처리)
            # BOM이 있는 경우 첫 번째 컬럼명에서 제거
            reader = csv.DictReader(f)
            
            # BOM 제거를 위한 컬럼명 정리
            fieldnames = reader.fieldnames
            if fieldnames and fieldnames[0].startswith('\ufeff'):
                fieldnames = [name.replace('\ufeff', '') if name.startswith('\ufeff') else name for name in fieldnames]
                reader.fieldnames = fieldnames
            
            for row in reader:
                # 제품명 컬럼 확인 (BOM 제거된 컬럼명도 확인)
                product_name_col = None
                for col_name in ['제품명', '제품명 ', 'product_name', 'Product Name']:
                    # 원본 컬럼명과 BOM 제거된 컬럼명 모두 확인
                    if col_name in row:
                        product_name_col = col_name
                        break
                    # BOM이 있는 경우도 확인
                    bom_col_name = '\ufeff' + col_name
                    if bom_col_name in row:
                        product_name_col = bom_col_name
                        break
                
                if not product_name_col:
                    continue
                
                # 제품명이 포함되어 있는지 확인 (부분 일치, 대소문자 무시)
                row_product_name = str(row[product_name_col]).strip()
                product_name_clean = product_name.strip()
                product_name_lower = product_name_clean.lower()
                row_product_name_lower = row_product_name.lower()
                
                # 더 유연한 매칭: 제품명의 주요 키워드가 포함되어 있는지 확인
                # 1. 정확한 포함 관계 확인
                # 2. 주요 키워드(2글자 이상)가 모두 포함되어 있는지 확인
                keywords = [kw for kw in product_name_lower.split() if len(kw) > 1]
                keyword_match = len(keywords) > 0 and all(kw in row_product_name_lower for kw in keywords)
                
                if (product_name_lower in row_product_name_lower or 
                    row_product_name_lower in product_name_lower or
                    keyword_match or
                    any(len(kw) > 2 and kw in row_product_name_lower for kw in keywords)):
                    # 이미지리스트 컬럼 찾기
                    image_col = None
                    for col_name in ['이미지리스트', '이미지 리스트', 'image_list', 'Image List', '이미지']:
                        if col_name in row:
                            image_col = col_name
                            break
                    
                    if not image_col:
                        continue
                    
                    # 이미지 URL 추출
                    image_value = str(row[image_col]).strip()
                    
                    if not image_value or image_value == 'nan' or image_value == '':
                        continue
                    
                    # 이미지 값이 리스트 형태인지 확인 (문자열로 저장된 리스트)
                    try:
                        # 리스트 형태로 파싱 시도
                        if image_value.startswith('[') and image_value.endswith(']'):
                            # ast.literal_eval로 안전하게 파싱
                            image_list = ast.literal_eval(image_value)
                            if isinstance(image_list, list) and len(image_list) > 0:
                                # 첫 번째 유효한 URL 반환
                                for url in image_list:
                                    if isinstance(url, str) and url.startswith('http'):
                                        return url
                                # 리스트에 URL이 없으면 첫 번째 항목 반환
                                return str(image_list[0])
                    except (ValueError, SyntaxError) as e:
                        # 파싱 실패 시 로그 출력 (디버깅용)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f'이미지 리스트 파싱 실패: {e}, 값: {image_value[:100]}')
                        pass
                    
                    # 단일 URL인 경우
                    if image_value.startswith('http'):
                        return image_value
                    
                    # 여러 URL이 쉼표로 구분된 경우
                    if ',' in image_value:
                        urls = [url.strip() for url in image_value.split(',')]
                        for url in urls:
                            if url.startswith('http'):
                                return url
    
    except Exception as e:
        # 에러 발생 시 None 반환
        return None
    
    return None

