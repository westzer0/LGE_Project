"""
칼럼 점수 기반 추천 엔진

Oracle DB PRODUCT SPEC 테이블의 SPEC_TYPE(COMMON/VARIANT)과 SPEC_KEY를 기반으로:
1. 칼럼 점수 산출 결과에 따라 패키지에 포함될 가전 종류 확인
2. 가전 종류별 상위 3개 모델 추천
"""
import logging
import traceback
from typing import Dict, List, Tuple
from collections import defaultdict
from django.db.models import QuerySet
from api.models import Product
from api.rule_engine import UserProfile
from api.utils.spec_column_scorer import spec_column_scorer
from api.utils.product_type_classifier import (
    group_products_by_type,
    extract_product_type,
    get_product_types_for_scenario
)
from api.utils.scoring import calculate_product_score
from api.utils.taste_scoring import calculate_product_score_with_taste_logic

logger = logging.getLogger(__name__)


class ColumnBasedRecommendationEngine:
    """칼럼 점수 기반 추천 엔진"""
    
    def __init__(self):
        self.budget_mapping = {
            'low': (0, 500000),
            'medium': (500000, 2000000),
            'high': (2000000, 10000000),
            'budget': (0, 500000),
            'standard': (500000, 2000000),
            'premium': (2000000, 5000000),
            'luxury': (5000000, 10000000),
        }
        
        # SPEC 구조 분석 완료 여부
        self.spec_structure_analyzed = False
    
    def get_recommendations(
        self,
        user_profile: dict,
        limit: int = 3,
        onboarding_data: dict = None,
        taste_id: int = None
    ) -> dict:
        """
        칼럼 점수 기반 추천 반환
        
        프로세스:
        1. 전체 제품 필터링 (예산, 카테고리 등)
        2. 제품 종류별로 그룹화
        3. SPEC 구조 분석 (COMMON/VARIANT 칼럼 식별)
        4. 제품 종류별 칼럼 점수 산출
        5. 칼럼 점수에 따라 패키지에 포함될 가전 종류 선정
        6. 각 가전 종류별 상위 3개 모델 추천
        
        Returns:
            추천 결과 딕셔너리
        """
        try:
            # 1. 입력 검증
            self._validate_user_profile(user_profile)
            
            if onboarding_data is None:
                onboarding_data = {}
            
            # 2. 전체 제품 필터링
            filtered_products = self._filter_products(user_profile)
            
            if not filtered_products.exists():
                return {
                    'success': False,
                    'message': '조건에 맞는 제품이 없습니다.',
                    'recommendations': []
                }
            
            products_list = list(filtered_products)
            
            # 3. 제품 종류별로 그룹화
            products_by_type = group_products_by_type(products_list)
            
            if not products_by_type:
                return {
                    'success': False,
                    'message': '제품 종류를 분류할 수 없습니다.',
                    'recommendations': []
                }
            
            # 4. SPEC 구조 분석 (최초 1회)
            if not self.spec_structure_analyzed:
                spec_column_scorer.analyze_spec_structure(products_list)
                self.spec_structure_analyzed = True
            
            # 5. 제품 종류별 칼럼 점수 산출
            product_type_column_scores = self._calculate_product_type_column_scores(
                products_by_type,
                user_profile,
                onboarding_data
            )
            
            # 6. 칼럼 점수에 따라 패키지에 포함될 가전 종류 선정
            selected_product_types = self._select_product_types_for_package(
                product_type_column_scores,
                user_profile,
                onboarding_data
            )
            
            print(f"[ColumnBased] 선정된 제품 종류: {selected_product_types}")
            
            # 7. 각 가전 종류별 상위 3개 모델 추천
            all_recommendations = []
            
            for product_type in selected_product_types:
                if product_type not in products_by_type:
                    continue
                
                type_products = products_by_type[product_type]
                
                # 제품 종류별 상위 3개 추천
                type_recommendations = self._recommend_top_products_by_type(
                    type_products,
                    product_type,
                    user_profile,
                    onboarding_data,
                    taste_id
                )
                
                all_recommendations.extend(type_recommendations)
                print(f"[ColumnBased] 제품 종류 '{product_type}': {len(type_recommendations)}개 추천")
            
            return {
                'success': True,
                'count': len(all_recommendations),
                'product_types': selected_product_types,
                'column_scores': product_type_column_scores,
                'recommendations': all_recommendations
            }
        
        except Exception as e:
            logger.error(f"Column-based recommendation error: {str(e)}", exc_info=True)
            print(f"Column-Based Recommendation Error: {traceback.format_exc()}")
            return {
                'success': False,
                'error': '추천 엔진 오류',
                'recommendations': []
            }
    
    def _validate_user_profile(self, profile: dict) -> None:
        """입력값 검증"""
        required_keys = ['budget_level', 'categories']
        for key in required_keys:
            if key not in profile:
                raise ValueError(f"필수 필드 누락: {key}")
    
    def _filter_products(self, user_profile: dict) -> QuerySet:
        """기본 필터링 (예산, 카테고리)"""
        budget_level = user_profile.get('budget_level', 'medium')
        min_price, max_price = self.budget_mapping.get(
            budget_level,
            self.budget_mapping['medium']
        )
        
        categories = user_profile.get('categories', [])
        
        products = (
            Product.objects
            .filter(
                is_active=True,
                category__in=categories,
                price__gt=0,  # 가격 0원 제외
                price__isnull=False,  # 가격 null 제외
                price__gte=min_price,
                price__lte=max_price,
            )
            .filter(spec__isnull=False)
        )
        
        return products
    
    def _calculate_product_type_column_scores(
        self,
        products_by_type: Dict[str, List[Product]],
        user_profile: dict,
        onboarding_data: dict
    ) -> Dict[str, float]:
        """
        제품 종류별 칼럼 점수 산출
        
        Returns:
            {제품_종류: 칼럼_점수} 딕셔너리
        """
        column_scores = {}
        
        print(f"[ColumnBased] 제품 종류별 칼럼 점수 산출 시작...")
        
        for product_type, products in products_by_type.items():
            if not products:
                continue
            
            # 제품 종류별 칼럼 점수 계산
            column_score = spec_column_scorer.calculate_product_type_column_score(
                product_type=product_type,
                products=products,
                user_profile=user_profile,
                onboarding_data=onboarding_data
            )
            
            column_scores[product_type] = column_score
            print(f"[ColumnBased] {product_type}: 칼럼 점수 {column_score:.3f}")
        
        return column_scores
    
    def _select_product_types_for_package(
        self,
        product_type_column_scores: Dict[str, float],
        user_profile: dict,
        onboarding_data: dict
    ) -> List[str]:
        """
        칼럼 점수에 따라 패키지에 포함될 가전 종류 선정
        
        기준:
        - 칼럼 점수가 높은 제품 종류 우선
        - 최소 점수 기준 (예: 0.3 이상)
        - 시나리오별 필수 제품 종류 포함
        - 최대 개수 제한
        
        Returns:
            선정된 제품 종류 리스트
        """
        # 1. 최소 점수 기준 이상인 제품 종류만
        min_score_threshold = 0.3
        qualified_types = [
            product_type
            for product_type, score in product_type_column_scores.items()
            if score >= min_score_threshold
        ]
        
        # 2. 칼럼 점수 순으로 정렬
        sorted_types = sorted(
            qualified_types,
            key=lambda t: product_type_column_scores[t],
            reverse=True
        )
        
        # 3. 시나리오별 필수 제품 종류 확인
        scenario_essential_types = get_product_types_for_scenario(
            user_profile,
            onboarding_data
        )
        
        # 필수 제품 종류 추가 (아직 포함되지 않은 경우)
        selected_types = set(sorted_types)
        for essential_type in scenario_essential_types:
            if essential_type in product_type_column_scores:
                selected_types.add(essential_type)
        
        # 4. 최대 개수 제한 (예: 최대 7개 제품 종류)
        max_product_types = 7
        final_types = list(selected_types)[:max_product_types]
        
        # 5. 최종 정렬 (칼럼 점수 순)
        final_types = sorted(
            final_types,
            key=lambda t: product_type_column_scores.get(t, 0.0),
            reverse=True
        )
        
        return final_types
    
    def _recommend_top_products_by_type(
        self,
        products: List[Product],
        product_type: str,
        user_profile: dict,
        onboarding_data: dict,
        taste_id: int = None
    ) -> List[dict]:
        """
        제품 종류별 상위 3개 모델 추천
        
        Returns:
            추천 제품 딕셔너리 리스트
        """
        if not products:
            return []
        
        # UserProfile 객체 생성
        has_pet_value = user_profile.get('has_pet', False) or user_profile.get('pet') in ['yes', 'Y', True, 'true', 'True']
        profile = UserProfile(
            vibe=user_profile.get('vibe', ''),
            household_size=str(user_profile.get('household_size', 2)),
            has_pet=has_pet_value,
            housing_type=user_profile.get('housing_type', ''),
            main_space=user_profile.get('main_space', 'living'),
            space_size=user_profile.get('space_size', 'medium'),
            priority=user_profile.get('priority', 'value'),
            budget_level=user_profile.get('budget_level', 'medium'),
            target_categories=user_profile.get('categories', []),
        )
        
        profile._household_size_int = user_profile.get('household_size', 2)
        profile._has_pet = has_pet_value
        profile._cooking = user_profile.get('cooking', 'sometimes')
        profile._laundry = user_profile.get('laundry', 'weekly')
        
        # 각 제품 스코어링
        scored_products = []
        
        for product in products[:50]:  # 최대 50개만 처리
            try:
                if taste_id is not None:
                    # onboarding_data 전달 (동적 logic 생성에 사용)
                    onboarding_data = user_profile.get('onboarding_data', {})
                    score = calculate_product_score_with_taste_logic(
                        product=product,
                        profile=profile,
                        taste_id=taste_id,
                        onboarding_data=onboarding_data
                    )
                else:
                    score = calculate_product_score(
                        product=product,
                        profile=profile
                    )
                
                # 점수 범위 검증
                if score < 0.0:
                    score = 0.0
                elif score > 1.0:
                    score = 1.0
                
                scored_products.append({
                    'product': product,
                    'score': score,
                    'product_type': product_type
                })
            except Exception as e:
                logger.warning(f"Score calculation failed: {str(e)}", exc_info=True)
                continue
        
        # 점수 순으로 정렬 및 상위 3개 선택
        top_products = sorted(
            scored_products,
            key=lambda x: x['score'],
            reverse=True
        )[:3]
        
        # 포맷팅
        recommendations = []
        for item in top_products:
            product = item['product']
            recommendation = {
                'product_id': product.id,
                'name': product.name,
                'model_number': product.model_number,
                'category': product.category,
                'category_display': product.get_category_display(),
                'product_type': product_type,
                'price': float(product.price) if product.price else 0,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'image_url': product.image_url or '',
                'score': round(item['score'], 2),
            }
            recommendations.append(recommendation)
        
        return recommendations


# Singleton 인스턴스
column_based_recommendation_engine = ColumnBasedRecommendationEngine()


