"""
스코어링 로직 검증 및 테스트 유틸리티
"""
from typing import Dict, List, Optional
from ..models import Product, ProductSpec
from .scoring import calculate_product_score
from ..rule_engine import UserProfile


def validate_scoring_logic(
    product: Product,
    user_profile: UserProfile,
    expected_score_range: tuple = (0.0, 1.0)
) -> Dict:
    """
    스코어링 로직 검증
    
    Args:
        product: 검증할 제품
        user_profile: 사용자 프로필
        expected_score_range: 예상 점수 범위 (min, max)
    
    Returns:
        검증 결과 딕셔너리
    """
    try:
        score = calculate_product_score(product, user_profile)
        
        is_valid = (
            expected_score_range[0] <= score <= expected_score_range[1]
        )
        
        return {
            'valid': is_valid,
            'score': score,
            'expected_range': expected_score_range,
            'product_id': product.id,
            'product_name': product.name,
            'errors': [] if is_valid else [
                f"점수 {score:.2f}가 예상 범위 {expected_score_range}를 벗어났습니다."
            ]
        }
    except Exception as e:
        return {
            'valid': False,
            'score': None,
            'expected_range': expected_score_range,
            'product_id': product.id,
            'product_name': product.name,
            'errors': [str(e)]
        }


def validate_multiple_products(
    products: List[Product],
    user_profile: UserProfile,
    expected_score_range: tuple = (0.0, 1.0)
) -> Dict:
    """
    여러 제품에 대한 스코어링 검증
    
    Args:
        products: 검증할 제품 리스트
        user_profile: 사용자 프로필
        expected_score_range: 예상 점수 범위
    
    Returns:
        전체 검증 결과
    """
    results = []
    valid_count = 0
    error_count = 0
    
    for product in products:
        result = validate_scoring_logic(product, user_profile, expected_score_range)
        results.append(result)
        
        if result['valid']:
            valid_count += 1
        else:
            error_count += 1
    
    return {
        'total': len(products),
        'valid': valid_count,
        'errors': error_count,
        'results': results,
        'success_rate': valid_count / len(products) if products else 0.0
    }


def check_score_distribution(
    products: List[Product],
    user_profile: UserProfile
) -> Dict:
    """
    점수 분포 확인
    
    Args:
        products: 제품 리스트
        user_profile: 사용자 프로필
    
    Returns:
        점수 분포 통계
    """
    scores = []
    errors = []
    
    for product in products:
        try:
            score = calculate_product_score(product, user_profile)
            scores.append(score)
        except Exception as e:
            errors.append({
                'product_id': product.id,
                'product_name': product.name,
                'error': str(e)
            })
    
    if not scores:
        return {
            'error': '점수를 계산할 수 있는 제품이 없습니다.',
            'errors': errors
        }
    
    scores.sort()
    
    return {
        'count': len(scores),
        'min': min(scores),
        'max': max(scores),
        'mean': sum(scores) / len(scores),
        'median': scores[len(scores) // 2],
        'q1': scores[len(scores) // 4],
        'q3': scores[len(scores) * 3 // 4],
        'errors': errors
    }



