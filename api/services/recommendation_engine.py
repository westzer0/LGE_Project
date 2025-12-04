"""
Recommendation Engine Service Layer

책임:
1. 사용자 프로필 검증
2. Hard Filter (필터링)
3. Soft Score (스코어링)
4. 최종 추천 반환
"""
import logging
import traceback
from typing import Dict, List
from django.db.models import QuerySet, Count
from api.models import Product
from api.rule_engine import UserProfile, build_profile
from api.utils.scoring import calculate_product_score
from api.utils.taste_scoring import calculate_product_score_with_taste_logic
from .recommendation_reason_generator import reason_generator

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """추천 엔진 서비스 클래스 (Singleton 패턴)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecommendationEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.budget_mapping = {
            'low': (0, 500000),
            'medium': (500000, 2000000),
            'high': (2000000, 10000000),
            # 기존 매핑과의 호환성
            'budget': (0, 500000),
            'standard': (500000, 2000000),
            'premium': (2000000, 5000000),
            'luxury': (5000000, 10000000),
        }
        self._initialized = True
    
    # ============================================================
    # PUBLIC INTERFACE
    # ============================================================
    
    def get_recommendations(
        self,
        user_profile: dict,
        limit: int = 3,
        taste_id: int = None,
        taste_info: dict = None
    ) -> dict:
        """
        최종 추천 반환 (View에서만 호출)
        
        입력:
        {
            'vibe': 'modern',
            'household_size': 4,
            'housing_type': 'apartment',
            'pyung': 30,
            'priority': 'tech',  # design/tech/eco/value
            'budget_level': 'medium',
            'categories': ['TV', 'LIVING'],
        }
        
        출력:
        {
            'success': True,
            'count': 3,
            'recommendations': [
                {
                    'product_id': 1,
                    'model': 'LG OLED55C5',
                    'category': 'TV',
                    'price': 1500000,
                    'discount_price': 1200000,
                    'image_url': '...',
                    'score': 0.85,
                    'reason': '...',
                },
                ...
            ]
        }
        """
        try:
            # 1. 입력 검증
            self._validate_user_profile(user_profile)
            
            # 2. Hard Filtering (조건에 맞는 제품만)
            filtered_products = self._filter_products(user_profile)
            
            if not filtered_products.exists():
                return {
                    'success': False,
                    'message': '조건에 맞는 제품이 없습니다.',
                    'recommendations': []
                }
            
            # 3. 제품 종류별로 그룹화 및 각 제품 종류에서 상위 3개씩 추천
            from api.utils.product_type_classifier import (
                group_products_by_type,
                get_product_types_for_scenario,
                extract_product_type
            )
            
            # 필터링된 제품을 리스트로 변환
            products_list = list(filtered_products)
            
            # 제품 종류별로 그룹화
            products_by_type = group_products_by_type(products_list)
            
            # 시나리오별 추천할 제품 종류 목록 결정
            onboarding_data = user_profile.get('onboarding_data', {})
            target_product_types = get_product_types_for_scenario(user_profile, onboarding_data)
            
            all_recommendations = []
            
            # 각 제품 종류별로 처리
            for product_type in target_product_types:
                if product_type not in products_by_type:
                    print(f"[Recommendation] 제품 종류 '{product_type}': 추천 제품 없음")
                    continue
                
                type_products = products_by_type[product_type]
                
                if not type_products:
                    continue
                
                # 제품 종류별 스코어링 (시나리오별 점수 산정 방식 적용)
                scored_products = self._score_products_by_type(
                    type_products,
                    user_profile,
                    product_type,
                    taste_id=taste_id
                )
                
                # 제품 종류별 상위 3개 선택
                top_type_products = sorted(
                    scored_products,
                    key=lambda x: x['score'],
                    reverse=True
                )[:3]  # 각 제품 종류별로 최대 3개
                
                # 제품 종류별 추천 포맷팅
                type_recommendations = [
                    self._format_recommendation(item, user_profile, taste_id=taste_id, taste_info=taste_info)
                    for item in top_type_products
                ]
                
                all_recommendations.extend(type_recommendations)
                print(f"[Recommendation] 제품 종류 '{product_type}': {len(type_recommendations)}개 추천")
            
            recommendations = all_recommendations
            
            return {
                'success': True,
                'count': len(recommendations),
                'recommendations': recommendations,
            }
        
        except ValueError as e:
            logger.warning(f"Recommendation validation error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'recommendations': []
            }
        except Exception as e:
            logger.error(f"Recommendation engine error: {str(e)}", exc_info=True)
            print(f"Recommendation Error: {traceback.format_exc()}")
            return {
                'success': False,
                'error': '추천 엔진 오류',
                'recommendations': []
            }
    
    # ============================================================
    # PRIVATE METHODS
    # ============================================================
    
    def _validate_user_profile(self, profile: dict) -> None:
        """입력값 검증"""
        required_keys = ['budget_level', 'categories']
        for key in required_keys:
            if key not in profile:
                raise ValueError(f"필수 필드 누락: {key}")
        
        budget_level = profile.get('budget_level', 'medium')
        if budget_level not in self.budget_mapping:
            raise ValueError(
                f"유효하지 않은 예산: {budget_level}. "
                f"(valid: {list(self.budget_mapping.keys())})"
            )
        
        categories = profile.get('categories', [])
        if not categories:
            raise ValueError("최소 1개 이상 카테고리 선택 필요")
        
        if not isinstance(categories, list):
            raise ValueError("categories는 리스트 형식이어야 함")
    
    def _filter_products(self, user_profile: dict) -> QuerySet:
        """
        Step 1: Hard Filtering (엄격한 필터링)
        - 카테고리 필터
        - 가격 범위 필터
        - 스펙 존재 필터
        - 반려동물 필터
        - 가족 구성 기반 용량 필터 (NEW)
        - 주거 형태/평수 기반 크기 필터 (NEW)
        - 생활 패턴 기반 필터 (NEW)
        - 우선순위 기반 필터 (NEW)
        """
        from api.utils.product_filters import apply_all_filters
        
        # 예산 범위 계산
        budget_level = user_profile.get('budget_level', 'medium')
        min_price, max_price = self.budget_mapping.get(
            budget_level,
            self.budget_mapping['medium']
        )
        
        categories = user_profile.get('categories', [])
        household_size = user_profile.get('household_size', 2)
        has_pet = user_profile.get('has_pet', False)
        
        # Step 1: 기본 필터 (Django ORM 쿼리)
        # 카테고리 필터링: 정확히 일치하는 카테고리만
        products = (
            Product.objects
            .filter(
                is_active=True,
                category__in=categories,  # 정확히 선택한 카테고리만
                price__gte=min_price,
                price__lte=max_price,
                price__gt=0,  # 가격 0 제외
            )
        )
        
        # 디버깅: 필터링된 제품 카테고리 확인
        category_counts = products.values('category').annotate(count=Count('id'))
        if category_counts:
            print(f"[Filter Debug] 카테고리별 제품 수:")
            for item in category_counts:
                print(f"  {item['category']}: {item['count']}개")
        
        # 스펙이 있는 제품만 (ProductSpec이 연결된 제품)
        products = products.filter(spec__isnull=False)
        
        # 펫 관련 필터링: 반려동물이 없으면 펫 전용 제품 제외
        # has_pet 값을 다양한 형태로 받을 수 있도록 처리
        has_pet = user_profile.get('has_pet', False) or user_profile.get('pet') in ['yes', 'Y', True, 'true', 'True']
        if not has_pet:
            # 펫 관련 키워드가 있는 제품 제외
            from django.db.models import Q
            pet_keywords = ['펫', 'PET', '반려동물', '애완동물', '동물케어', '펫케어', 'PET CARE']
            
            # 제품명이나 설명에 펫 키워드가 포함된 제품 제외
            pet_filter = Q()
            for keyword in pet_keywords:
                pet_filter |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
            
            if pet_filter:
                products = products.exclude(pet_filter)
                print(f"[Filter] 펫 관련 제품 제외 (반려동물 없음)")
        
        print(f"[Filter Step 1] 기본 필터: 카테고리={categories}, 가격={min_price}~{max_price}원, 가족={household_size}명, 반려동물={has_pet}, 결과={products.count()}개")
        
        # Step 2: 추가 필터링 (Python 레벨에서 처리)
        # QuerySet을 리스트로 변환하여 상세 필터링 적용
        products_list = list(products)
        
        # 엄격한 필터링 적용
        filtered_products = apply_all_filters(products_list, user_profile)
        
        # 필터링된 제품 ID 리스트로 QuerySet 재생성
        if filtered_products:
            product_ids = [p.id for p in filtered_products]
            products = Product.objects.filter(id__in=product_ids)
        else:
            # 필터링 결과가 없으면 빈 QuerySet 반환
            products = Product.objects.none()
        
        print(f"[Filter Step 2] 추가 필터링 후: {products.count()}개")
        
        return products
    
    def _score_products_by_type(
        self,
        products: List[Product],
        user_profile: dict,
        product_type: str,
        taste_id: int = None
    ) -> List[dict]:
        """
        제품 종류별 스코어링 (시나리오별 점수 산정 방식 차등화)
        
        Args:
            products: 제품 리스트
            user_profile: 사용자 프로필
            product_type: 제품 종류 (예: '세탁기', '청소기', '냉장고')
            taste_id: 취향 ID
            
        Returns:
            스코어링된 제품 리스트
        """
        scored = []
        
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
        
        # 추가 사용자 정보
        profile._household_size_int = user_profile.get('household_size', 2)
        profile._has_pet = has_pet_value
        profile._cooking = user_profile.get('cooking', 'sometimes')
        profile._laundry = user_profile.get('laundry', 'weekly')
        
        for idx, product in enumerate(products[:50], 1):
            try:
                # 제품 종류별 가중치 적용 (시나리오별 차등화)
                base_score = 0.0
                
                if taste_id is not None:
                    base_score = calculate_product_score_with_taste_logic(
                        product=product,
                        profile=profile,
                        taste_id=taste_id
                    )
                else:
                    base_score = calculate_product_score(
                        product=product,
                        profile=profile
                    )
                
                # 제품 종류별 추가 점수 조정 (시나리오별 차등화)
                type_multiplier = self._get_product_type_multiplier(
                    product_type,
                    user_profile,
                    user_profile.get('onboarding_data', {})
                )
                
                final_score = base_score * type_multiplier
                
                # 점수 범위 검증 (0.0 ~ 1.0)
                if final_score < 0.0:
                    final_score = 0.0
                elif final_score > 1.0:
                    final_score = 1.0
                
                scored.append({
                    'product': product,
                    'score': final_score,
                })
                
                if idx <= 3:
                    print(f"[Score by Type] {idx}. [{product_type}] {product.name}: {final_score:.2f} (base: {base_score:.2f}, multiplier: {type_multiplier:.2f})")
            
            except Exception as e:
                logger.warning(f"Score calculation failed for product {product.id}: {str(e)}", exc_info=True)
                print(f"[Score Error] {product.name}: {e}")
                scored.append({
                    'product': product,
                    'score': 0.5,
                })
        
        return scored
    
    def _get_product_type_multiplier(
        self,
        product_type: str,
        user_profile: dict,
        onboarding_data: dict
    ) -> float:
        """
        제품 종류별 가중치 배율 반환 (시나리오별 차등화)
        
        예시:
        - 4인 가족 + 세탁기 → 높은 가중치
        - 1인 가구 + 대형 냉장고 → 낮은 가중치
        """
        household_size = user_profile.get('household_size', 2)
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        priority = user_profile.get('priority', 'value')
        
        multiplier = 1.0  # 기본 배율
        
        # 제품 종류별 + 시나리오별 가중치 조정
        if product_type == '세탁기':
            if laundry in ['daily', 'few_times'] and household_size >= 3:
                multiplier = 1.2  # 세탁 빈도 높고 가족이 많으면
            elif household_size == 1:
                multiplier = 0.9  # 1인 가구는 조금 낮게
        
        elif product_type == '워시타워':
            if household_size >= 4:
                multiplier = 1.3  # 4인 이상 가족에게 높은 가중치
            elif household_size == 1:
                multiplier = 0.7  # 1인 가구는 낮게
        
        elif product_type == '냉장고':
            if household_size >= 4:
                multiplier = 1.2  # 큰 가족에게 높은 가중치
            elif household_size == 1:
                multiplier = 0.8  # 1인 가구는 낮게
        
        elif product_type == '식기세척기':
            if cooking in ['high', 'often'] and household_size >= 3:
                multiplier = 1.3  # 요리 많이 하는 가족에게 높은 가중치
            elif cooking == 'rarely':
                multiplier = 0.7  # 요리 안 하는 경우 낮게
        
        elif product_type == 'TV':
            if media in ['gaming', 'heavy', 'ott']:
                multiplier = 1.3  # 미디어 소비 많으면 높은 가중치
            elif media == 'none':
                multiplier = 0.5  # 미디어 안 보면 낮게
        
        elif product_type == '청소기':
            # 청소기는 모든 시나리오에서 기본적으로 필요
            if priority == 'tech':
                multiplier = 1.1  # 기술 선호 시 조금 높게
        
        elif product_type == '에어컨':
            housing_type = user_profile.get('housing_type', 'apartment')
            if housing_type in ['apartment', 'detached']:
                multiplier = 1.1  # 아파트/단독주택은 높게
        
        elif product_type == '공기청정기':
            housing_type = user_profile.get('housing_type', 'apartment')
            if housing_type in ['apartment', 'detached']:
                multiplier = 1.1
        
        elif product_type == '스타일러':
            if household_size >= 3:
                multiplier = 1.2  # 큰 가족에게 높은 가중치
            else:
                multiplier = 0.8  # 작은 가족은 낮게
        
        return multiplier
    
    def _score_products(self, products: QuerySet, user_profile: dict, taste_id: int = None) -> List[dict]:
        """
        Step 2: Soft Scoring
        - 각 제품 점수 계산 (스코어링 함수 호출)
        """
        scored = []
        
        # UserProfile 객체 생성 (scoring 함수 호환성)
        # has_pet 값을 다양한 형태로 받을 수 있도록 처리
        has_pet_value = user_profile.get('has_pet', False) or user_profile.get('pet') in ['yes', 'Y', True, 'true', 'True']
        profile = UserProfile(
            vibe=user_profile.get('vibe', ''),
            household_size=str(user_profile.get('household_size', 2)),
            has_pet=has_pet_value,  # 반려동물 정보 추가
            housing_type=user_profile.get('housing_type', ''),
            main_space=user_profile.get('main_space', 'living'),
            space_size=user_profile.get('space_size', 'medium'),
            priority=user_profile.get('priority', 'value'),
            budget_level=user_profile.get('budget_level', 'medium'),
            target_categories=user_profile.get('categories', []),
        )
        
        # 추가 사용자 정보를 profile 객체에 저장 (스코어링에서 사용)
        profile._household_size_int = user_profile.get('household_size', 2)
        profile._has_pet = has_pet_value
        profile._cooking = user_profile.get('cooking', 'sometimes')
        profile._laundry = user_profile.get('laundry', 'weekly')
        
        for idx, product in enumerate(products[:50], 1):  # 최대 50개까지만 처리
            try:
                # 스코어링 함수 호출 (taste_id가 있으면 취향별 logic 사용)
                if taste_id is not None:
                    score = calculate_product_score_with_taste_logic(
                        product=product,
                        profile=profile,
                        taste_id=taste_id
                    )
                else:
                    score = calculate_product_score(
                        product=product,
                        profile=profile
                    )
                
                # 점수 범위 검증 (0.0 ~ 1.0)
                if score < 0.0:
                    score = 0.0
                elif score > 1.0:
                    score = 1.0
                
                scored.append({
                    'product': product,
                    'score': score,
                })
                
                if idx <= 3:
                    print(f"[Score] {idx}. {product.name}: {score:.2f}")
            
            except Exception as e:
                logger.warning(f"Score calculation failed for product {product.id}: {str(e)}", exc_info=True)
                print(f"[Score Error] {product.name}: {e}")
                # 스코어 계산 실패 시 기본값 0.5
                scored.append({
                    'product': product,
                    'score': 0.5,
                })
        
        return scored
    
    def _format_recommendation(
        self, 
        item: dict, 
        user_profile: dict,
        taste_id: int = None,
        taste_info: dict = None
    ) -> dict:
        """
        Step 3: 최종 포맷팅
        - API 응답 형식으로 변환
        """
        product = item['product']
        score = item['score']
        
        # 추천 이유 생성 (새로운 로직 사용)
        reason = reason_generator.generate_reason(
            product=product,
            user_profile=user_profile,
            taste_info=taste_info,
            score=score
        )
        
        return {
            'product_id': product.id,
            'model': product.name,
            'name': product.name,  # 호환성
            'model_number': product.model_number,
            'category': product.category,
            'category_display': product.get_category_display(),
            'price': float(product.price) if product.price else 0,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_url': product.image_url or '',
            'score': round(score, 2),
            'reason': reason,
        }
    
    # _build_recommendation_reason 메서드는 제거됨
    # 추천 이유 생성은 recommendation_reason_generator.py의 RecommendationReasonGenerator를 사용


# ============================================================
# Singleton 인스턴스
# ============================================================
recommendation_engine = RecommendationEngine()

