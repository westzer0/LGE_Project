"""
Oracle DB의 PRODUCT_IMAGE 테이블에서 제품 이미지 URL 가져오기
"""
import logging
from api.db.oracle_client import fetch_one, fetch_all_dict

logger = logging.getLogger(__name__)


def get_image_url_from_product_image_table(
    product_id: int = None, 
    product_name: str = None,
    model_number: str = None
) -> str:
    """
    Oracle DB의 PRODUCT_IMAGE 테이블에서 이미지 URL 가져오기
    
    Args:
        product_id: Oracle DB의 PRODUCT_ID (PRODUCT.PRODUCT_ID)
        product_name: 제품명 (제품명으로 PRODUCT 테이블에서 PRODUCT_ID 찾기)
        model_number: 모델명 (모델명으로 PRODUCT 테이블에서 PRODUCT_ID 찾기)
    
    Returns:
        이미지 URL (없으면 빈 문자열)
    """
    try:
        # product_id가 없으면 PRODUCT 테이블에서 찾기
        if not product_id:
            if model_number:
                product_id = _get_product_id_from_model_number(model_number)
            if not product_id and product_name:
                product_id = _get_product_id_from_name(product_name)
            
            if not product_id:
                logger.warning(f'제품을 찾을 수 없습니다: name={product_name}, model={model_number}')
                return ''
        
        # PRODUCT_IMAGE 테이블에서 이미지 URL 가져오기
        result = fetch_one("""
            SELECT IMAGE_URL
            FROM PRODUCT_IMAGE
            WHERE PRODUCT_ID = :product_id
            AND IMAGE_URL IS NOT NULL
            AND IMAGE_URL != ''
            AND ROWNUM = 1
            ORDER BY PRODUCT_IMAGE_ID
        """, {'product_id': product_id})
        
        if result and result[0]:
            image_url = str(result[0]).strip()
            if image_url:
                logger.debug(f'이미지 URL 찾음: PRODUCT_ID={product_id} -> {image_url[:100]}')
                return image_url
        
        logger.warning(f'이미지 URL을 찾을 수 없습니다: PRODUCT_ID={product_id}')
        return ''
        
    except Exception as e:
        logger.error(f'PRODUCT_IMAGE 테이블 조회 오류: {e}')
        return ''


def _get_product_id_from_name(product_name: str) -> int:
    """
    제품명으로 PRODUCT 테이블에서 PRODUCT_ID 찾기
    
    Args:
        product_name: 제품명
    
    Returns:
        PRODUCT_ID (없으면 None)
    """
    try:
        result = fetch_one("""
            SELECT PRODUCT_ID
            FROM PRODUCT
            WHERE PRODUCT_NAME LIKE :product_name
            AND STATUS = '판매중'
            AND ROWNUM = 1
            ORDER BY PRODUCT_ID DESC
        """, {'product_name': f'%{product_name}%'})
        
        if result and result[0]:
            return int(result[0])
        
        return None
        
    except Exception as e:
        logger.error(f'PRODUCT 테이블 조회 오류: {e}')
        return None


def _get_product_id_from_model_number(model_number: str) -> int:
    """
    모델명으로 PRODUCT 테이블에서 PRODUCT_ID 찾기
    
    Args:
        model_number: 모델명
    
    Returns:
        PRODUCT_ID (없으면 None)
    """
    try:
        result = fetch_one("""
            SELECT PRODUCT_ID
            FROM PRODUCT
            WHERE MODEL_NUMBER = :model_number
            AND STATUS = '판매중'
            AND ROWNUM = 1
            ORDER BY PRODUCT_ID DESC
        """, {'model_number': model_number})
        
        if result and result[0]:
            return int(result[0])
        
        return None
        
    except Exception as e:
        logger.error(f'PRODUCT 테이블 조회 오류 (모델명): {e}')
        return None


def get_image_url_by_product_id(product_id: int) -> str:
    """
    제품 ID로 이미지 URL 가져오기 (간편 함수)
    
    Args:
        product_id: 제품 ID
    
    Returns:
        이미지 URL
    """
    return get_image_url_from_product_image_table(product_id=product_id)

