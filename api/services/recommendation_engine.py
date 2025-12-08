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
            # 1. Taste 기반 MAIN CATEGORY 선택 (필터링 전에 먼저 선택)
            onboarding_data = user_profile.get('onboarding_data', {})
            
            if taste_id is not None:
                # Taste 기반 MAIN CATEGORY 선택
                from api.utils.taste_category_selector import get_categories_for_taste
                selected_main_categories = get_categories_for_taste(
                    taste_id=taste_id,
                    onboarding_data=onboarding_data,
                    num_categories=None  # 자동 결정
                )
                # user_profile에 선택된 카테고리 설정 (검증 전에)
                user_profile['categories'] = selected_main_categories
            else:
                # 기존 categories 사용 (MAIN_CATEGORY 형식)
                selected_main_categories = user_profile.get('categories', [])
                # MAIN_CATEGORY가 없으면 기본값
                if not selected_main_categories:
                    selected_main_categories = ['TV', '냉장고', '에어컨']
                    user_profile['categories'] = selected_main_categories
            
            # 2. 입력 검증 (카테고리 선택 후)
            self._validate_user_profile(user_profile)
            
            # 3. Hard Filtering (조건에 맞는 제품만, MAIN_CATEGORY 기반)
            filtered_products = self._filter_products(user_profile)
            
            if not filtered_products.exists():
                return {
                    'success': False,
                    'message': '조건에 맞는 제품이 없습니다.',
                    'recommendations': []
                }
            
            # 4. MAIN CATEGORY별로 그룹화 및 각 카테고리에서 상위 3개씩 추천
            
            if not selected_main_categories:
                return {
                    'success': False,
                    'message': '선택된 카테고리가 없습니다.',
                    'recommendations': []
                }
            
            # MAIN_CATEGORY를 Django category로 매핑
            from api.utils.category_mapping import get_django_categories_for_main_categories, validate_category_match
            django_categories = get_django_categories_for_main_categories(selected_main_categories)
            
            # 필터링된 제품이 없으면 저예산 대가족 fallback 로직
            if not filtered_products.exists():
                budget_level = user_profile.get('budget_level', 'medium')
                household_size = user_profile.get('household_size', 2)
                
                # 저예산 대가족인 경우 예산 범위 확대
                if budget_level == 'low' and household_size >= 4:
                    print(f"[Fallback] 저예산 대가족 감지: 예산 범위 확대")
                    min_price, max_price = self.budget_mapping.get('medium', (500000, 2000000))
                    filtered_products = self._filter_products_with_budget(
                        user_profile, 
                        min_price=min_price, 
                        max_price=max_price
                    )
                    if not filtered_products.exists():
                        print(f"[Fallback] 예산 확대 후에도 제품 없음")
                        return {
                            'success': False,
                            'message': '조건에 맞는 제품이 없습니다.',
                            'recommendations': []
                        }
            
            all_recommendations = []
            
            # 각 MAIN CATEGORY별로 처리
            for main_category in selected_main_categories:
                # MAIN_CATEGORY를 Django category로 매핑 (fallback용)
                django_category = get_django_categories_for_main_categories([main_category])[0] if main_category else 'LIVING'
                
                # MAIN_CATEGORY 기반으로 제품 필터링 (spec_json에서 MAIN_CATEGORY 확인)
                import json
                valid_products = []
                for product in filtered_products:
                    matched = False
                    
                    # spec_json에서 MAIN_CATEGORY 확인
                    if hasattr(product, 'spec') and product.spec and product.spec.spec_json:
                        try:
                            spec_data = json.loads(product.spec.spec_json)
                            main_cat_from_spec = spec_data.get('MAIN_CATEGORY', '').strip()
                            product_type = spec_data.get('PRODUCT_TYPE', '').strip()
                            
                            # MAIN_CATEGORY가 일치하는지 확인
                            if main_cat_from_spec == main_category or product_type == main_category:
                                valid_products.append(product)
                                matched = True
                        except:
                            pass
                    
                    # MAIN_CATEGORY 매칭 실패 시 Django category로 fallback
                    if not matched and product.category == django_category:
                        valid_products.append(product)
                
                if not valid_products:
                    print(f"[Recommendation] MAIN_CATEGORY '{main_category}' (Django: '{django_category}'): 추천 제품 없음")
                    continue
                
                # QuerySet으로 변환
                product_ids = [p.id for p in valid_products]
                category_products = filtered_products.filter(id__in=product_ids)
                
                if not category_products.exists():
                    print(f"[Recommendation] MAIN_CATEGORY '{main_category}': 추천 제품 없음")
                    continue
                
                # 카테고리별 스코어링
                scored_products = self._score_products(
                    category_products,
                    user_profile,
                    taste_id=taste_id
                )
                
                # 카테고리별 상위 3개 선택
                top_category_products = sorted(
                    scored_products,
                    key=lambda x: x['score'],
                    reverse=True
                )[:3]  # 각 카테고리별로 최대 3개
                
                # 카테고리별 추천 포맷팅
                category_recommendations = [
                    self._format_recommendation(item, user_profile, taste_id=taste_id, taste_info=taste_info)
                    for item in top_category_products
                ]
                
                # category 정보 추가 (MAIN_CATEGORY와 Django category 모두)
                django_category = get_django_categories_for_main_categories([main_category])[0] if main_category else 'LIVING'
                for rec in category_recommendations:
                    rec['category'] = django_category  # Django category (호환성)
                    rec['main_category'] = main_category  # 원본 MAIN_CATEGORY
                
                all_recommendations.extend(category_recommendations)
                print(f"[Recommendation] MAIN_CATEGORY '{main_category}': {len(category_recommendations)}개 추천")
            
            recommendations = all_recommendations
            
            # Category별로 그룹화 (프론트엔드 표시용) - PRD 요구사항
            recommendations_by_category = {}
            for rec in recommendations:
                main_cat = rec.get('main_category', '기타')
                if main_cat not in recommendations_by_category:
                    recommendations_by_category[main_cat] = []
                recommendations_by_category[main_cat].append(rec)
            
            # taste_id가 있으면 RECOMMENDED_PRODUCT_SCORES 추가 및 메시지 생성
            recommended_product_scores = None
            taste_title = None
            taste_description = None
            
            if taste_id is not None:
                from .taste_based_product_scorer import taste_based_product_scorer
                taste_config = taste_based_product_scorer._get_taste_config(taste_id)
                
                if taste_config:
                    recommended_products = taste_config.get('recommended_products', {})
                    recommended_product_scores = taste_config.get('recommended_product_scores', {})
                    
                    # 각 추천 제품에 점수 매핑 (product_id 기반)
                    if recommended_products and recommended_product_scores:
                        for rec in recommendations:
                            main_cat = rec.get('main_category')
                            product_id = rec.get('product_id')
                            
                            if main_cat and product_id and main_cat in recommended_products:
                                category_product_ids = recommended_products[main_cat]
                                category_scores = recommended_product_scores.get(main_cat, [])
                                
                                # product_id로 정확히 매핑
                                if product_id in category_product_ids:
                                    score_index = category_product_ids.index(product_id)
                                    if score_index < len(category_scores):
                                        rec['taste_score'] = category_scores[score_index]  # 백엔드에서 계산한 점수
                                # product_id 매핑 실패 시 순서 기반 fallback
                                elif category_scores and len(category_scores) > 0:
                                    category_recs = [r for r in recommendations if r.get('main_category') == main_cat]
                                    if rec in category_recs:
                                        score_index = category_recs.index(rec)
                                        if score_index < len(category_scores):
                                            rec['taste_score'] = category_scores[score_index]
                    
                    # taste별 메시지 생성
                    representative_taste = taste_config.get('representative_taste', {})
                    if representative_taste:
                        taste_title, taste_description = self._generate_taste_messages(
                            representative_taste, 
                            user_profile,
                            recommendations
                        )
            
            return {
                'success': True,
                'count': len(recommendations),
                'recommendations': recommendations,  # 전체 리스트 (하위 호환성)
                'recommendations_by_category': recommendations_by_category,  # Category별 그룹화 (PRD 요구사항)
                'selected_categories': selected_main_categories,  # 선택된 카테고리 목록
                'taste_id': taste_id,  # 사용된 taste_id
                'recommended_product_scores': recommended_product_scores,  # 전체 점수 정보도 포함
                'taste_title': taste_title,  # taste별 제목
                'taste_description': taste_description,  # taste별 설명
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
    
    def _filter_products(self, user_profile: dict, taste_id: int = None) -> QuerySet:
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
        
        # user_profile의 categories 사용 (이미 MAIN_CATEGORY 형식으로 설정됨)
        main_categories = user_profile.get('categories', [])
        
        household_size = user_profile.get('household_size', 2)
        has_pet = user_profile.get('has_pet', False)
        
        # Step 1: 기본 필터 (가격, 활성화 여부만)
        # 성능 최적화: select_related로 관련 객체 미리 로드
        products = (
            Product.objects
            .select_related('spec')  # ProductSpec 미리 로드
            .filter(
                is_active=True,
                price__gt=0,  # 가격 0원 제외
                price__isnull=False,  # 가격 null 제외
                price__gte=min_price,
                price__lte=max_price,
            )
        )
        
        # 스펙이 있는 제품만 (ProductSpec이 연결된 제품, MAIN_CATEGORY 확인을 위해 필요)
        products = products.filter(spec__isnull=False)
        
        # Step 2: MAIN_CATEGORY 기반 필터링 (spec_json에서 MAIN_CATEGORY 추출)
        if main_categories:
            import json
            from api.utils.category_mapping import get_django_categories_for_main_categories
            
            # MAIN_CATEGORY를 Django category로 매핑 (fallback용)
            django_categories = get_django_categories_for_main_categories(main_categories)
            
            valid_product_ids = []
            for product in products:
                matched = False
                
                if hasattr(product, 'spec') and product.spec and product.spec.spec_json:
                    try:
                        spec_data = json.loads(product.spec.spec_json)
                        main_cat_from_spec = spec_data.get('MAIN_CATEGORY', '').strip()
                        product_type = spec_data.get('PRODUCT_TYPE', '').strip()
                        
                        # MAIN_CATEGORY가 선택된 카테고리 중 하나와 일치하는지 확인
                        if main_cat_from_spec in main_categories or product_type in main_categories:
                            valid_product_ids.append(product.id)
                            matched = True
                    except:
                        pass
                
                # MAIN_CATEGORY가 없거나 매칭 실패 시 Django category로 fallback
                if not matched and product.category in django_categories:
                    valid_product_ids.append(product.id)
            
            if valid_product_ids:
                products = products.filter(id__in=valid_product_ids)
            else:
                # MAIN_CATEGORY 매칭 실패 시 Django category로 fallback
                products = products.filter(category__in=django_categories)
        
        # 디버깅: MAIN_CATEGORY별 제품 수 확인
        if main_categories:
            main_cat_counts = {}
            for product in products[:100]:  # 샘플링
                if hasattr(product, 'spec') and product.spec and product.spec.spec_json:
                    try:
                        spec_data = json.loads(product.spec.spec_json)
                        main_cat = spec_data.get('MAIN_CATEGORY', '').strip()
                        if main_cat:
                            main_cat_counts[main_cat] = main_cat_counts.get(main_cat, 0) + 1
                    except:
                        pass
            
            if main_cat_counts:
                print(f"[Filter Debug] MAIN_CATEGORY별 제품 수:")
                for main_cat, count in sorted(main_cat_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {main_cat}: {count}개 이상")
        
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
        
        print(f"[Filter Step 1] 기본 필터: MAIN_CATEGORY={main_categories}, 가격={min_price}~{max_price}원, 가족={household_size}명, 반려동물={has_pet}, 결과={products.count()}개")
        
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
    
    def _filter_products_with_budget(self, user_profile: dict, min_price: int, max_price: int) -> QuerySet:
        """
        예산 범위를 지정하여 제품 필터링 (fallback용)
        """
        from api.utils.product_filters import apply_all_filters
        
        categories = user_profile.get('categories', [])
        household_size = user_profile.get('household_size', 2)
        has_pet = user_profile.get('has_pet', False)
        
        # MAIN_CATEGORY를 Django category로 매핑
        from api.utils.category_mapping import get_django_categories_for_main_categories
        django_categories = get_django_categories_for_main_categories(categories)
        
        # 기본 필터
        products = (
            Product.objects
            .filter(
                is_active=True,
                category__in=django_categories,
                price__gt=0,
                price__isnull=False,
                price__gte=min_price,
                price__lte=max_price,
            )
        )
        
        # 스펙이 있는 제품만
        products = products.filter(spec__isnull=False)
        
        # 펫 관련 필터링
        has_pet = user_profile.get('has_pet', False) or user_profile.get('pet') in ['yes', 'Y', True, 'true', 'True']
        if not has_pet:
            from django.db.models import Q
            pet_keywords = ['펫', 'PET', '반려동물', '애완동물', '동물케어', '펫케어', 'PET CARE']
            pet_filter = Q()
            for keyword in pet_keywords:
                pet_filter |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
            if pet_filter:
                products = products.exclude(pet_filter)
        
        # 추가 필터링
        products_list = list(products)
        filtered_products = apply_all_filters(products_list, user_profile)
        
        if filtered_products:
            product_ids = [p.id for p in filtered_products]
            products = Product.objects.filter(id__in=product_ids)
        else:
            products = Product.objects.none()
        
        return products
    
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
        
        # 추천 이유 생성 (새로운 로직 사용, 제품 카테고리 포함)
        reason = reason_generator.generate_reason(
            product=product,
            user_profile=user_profile,
            taste_info=taste_info,
            score=score
        )
        
        # 제품 카테고리 확인 및 이유 검증
        product_name = product.name if hasattr(product, 'name') else ''
        product_category = product.category if hasattr(product, 'category') else ''
        
        # 제품 이름으로 카테고리 파악
        detected_category = None
        if '냉장고' in product_name or ('디오스' in product_name and '냉장고' in product_name):
            detected_category = '냉장고'
        elif '오븐' in product_name or '광파' in product_name:
            detected_category = '오븐'
        elif '식기세척기' in product_name or '세척기' in product_name:
            detected_category = '식기세척기'
        elif 'TV' in product_name or '티비' in product_name:
            detected_category = 'TV'
        
        # 추천 이유에 잘못된 카테고리가 포함되어 있으면 수정
        if detected_category and detected_category != '냉장고':
            # 냉장고가 아닌데 추천 이유에 '냉장고'가 포함되어 있으면 수정
            if '냉장고' in reason and detected_category in reason:
                # 이미 올바른 카테고리가 포함되어 있으면 그대로 사용
                pass
            elif '냉장고' in reason and detected_category not in reason:
                # 냉장고가 잘못 포함되어 있으면 수정
                reason = reason.replace('냉장고', detected_category)
                # 가족 수 정보 유지하면서 카테고리만 변경
                household_size = user_profile.get('household_size', 2)
                if f"{household_size}인 가구" in reason or "가족" in reason:
                    # 가족 정보는 유지하고 카테고리만 수정
                    pass
        elif detected_category == '냉장고':
            # 냉장고인데 다른 카테고리가 포함되어 있으면 수정
            if '오븐' in reason or '식기세척기' in reason:
                reason = reason.replace('오븐', '냉장고').replace('식기세척기', '냉장고')
        
        # Oracle DB의 PRODUCT_IMAGE 테이블에서 이미지 URL 가져오기 (우선)
        image_url = product.image_url or ''
        
        # PRODUCT_IMAGE 테이블에서 이미지 가져오기 시도
        # 모델명 또는 제품명으로 Oracle DB의 PRODUCT_ID 찾아서 이미지 가져오기
        if not image_url:
            try:
                from api.utils.product_image_loader import get_image_url_from_product_image_table
                # 모델명 또는 제품명으로 Oracle DB에서 이미지 가져오기
                oracle_image_url = get_image_url_from_product_image_table(
                    product_name=product.name,
                    model_number=product.model_number
                )
                if oracle_image_url:
                    image_url = oracle_image_url
            except Exception as e:
                # Oracle DB 조회 실패해도 계속 진행
                pass
        
        # 가격 처리: price가 0이거나 None인 경우 경고
        price = float(product.price) if product.price and product.price > 0 else 0
        if price == 0:
            print(f"[가격 경고] 제품 {product.id} ({product.name}): 가격이 0원입니다. (DB price={product.price})")
        
        discount_price = None
        if product.discount_price and product.discount_price > 0:
            discount_price = float(product.discount_price)
        elif price > 0:
            discount_price = price  # discount_price가 없으면 정가를 할인가로 사용
        
        return {
            'product_id': product.id,
            'model': product.name,
            'name': product.name,  # 호환성
            'model_number': product.model_number,
            'category': product.category,
            'category_display': product.get_category_display(),
            'price': price,
            'discount_price': discount_price,
            'image_url': image_url,
            'score': round(score, 2),
            'reason': reason,
        }
    
    def _generate_taste_messages(
        self,
        representative_taste: dict,
        user_profile: dict,
        recommendations: List[dict]
    ) -> tuple:
        """
        taste 정보를 기반으로 제목과 설명 메시지 생성
        
        Args:
            representative_taste: taste_scoring_logics.json의 representative_taste 정보
            user_profile: 사용자 프로필 정보
            recommendations: 추천 제품 리스트
        
        Returns:
            (title, description) 튜플
        """
        vibe = representative_taste.get('vibe', '')
        mate = representative_taste.get('mate', '')
        priority = representative_taste.get('priority', '')
        budget = representative_taste.get('budget', '')
        lineup = representative_taste.get('lineup', '')
        
        # vibe에 따른 스타일 키워드 추출
        vibe_keywords = {
            '유니크 & 팝': ('유니크하고 컬러풀한', '개성 있는'),
            '유니크 & 팝 (Unique & Pop)': ('유니크하고 컬러풀한', '개성 있는'),
            '모던/심플': ('모던하고 심플한', '세련된'),
            '따뜻한 톤': ('따뜻한', '코지한'),
            '럭셔리/고급': ('럭셔리한', '프리미엄'),
        }
        
        # priority에 따른 키워드 추출
        priority_keywords = {
            '삶을 편하게 해주는 AI/스마트 기능': 'AI/스마트 기능',
            '인테리어를 완성하는 디자인': '디자인',
            '에너지 효율과 친환경': '에너지 효율',
            '가성비와 실용성': '가성비',
        }
        
        # vibe 키워드 찾기
        style_keyword = '개성 있는'
        for key, (desc, title) in vibe_keywords.items():
            if key in vibe:
                style_keyword = title
                break
        
        # 추천 제품 카테고리 확인
        categories = set()
        product_names = []
        for rec in recommendations[:3]:  # 최대 3개
            cat = rec.get('main_category', '')
            if cat:
                categories.add(cat)
            name = rec.get('name', '')
            if name:
                product_names.append(name)
        
        # 카테고리별 제품명 추출
        category_product_map = {
            '냉장고': [],
            '오븐': [],
            '식기세척기': [],
        }
        
        for name in product_names:
            if '냉장고' in name or '디오스' in name:
                category_product_map['냉장고'].append(name)
            elif '오븐' in name or '광파' in name:
                category_product_map['오븐'].append(name)
            elif '식기세척기' in name or '세척기' in name:
                category_product_map['식기세척기'].append(name)
        
        # 제품 구성 설명
        product_composition = []
        if category_product_map['냉장고']:
            product_composition.append('냉장고')
        if category_product_map['오븐']:
            product_composition.append('광파오븐')
        if category_product_map['식기세척기']:
            product_composition.append('식기세척기')
        
        product_str = ', '.join(product_composition) if product_composition else '가전제품'
        
        # 컬러 정보 (vibe에 따라)
        color_map = {
            '유니크 & 팝': '다양한 컬러',
            '모던/심플': 'Essence White',
            '따뜻한 톤': 'Nature Beige',
            '럭셔리/고급': '프리미엄',
        }
        color = 'Essence White'
        for key, val in color_map.items():
            if key in vibe:
                color = val
                break
        
        # 제목 생성
        title_parts = []
        if mate:
            if '1인' in mate:
                title_parts.append('1인 가구')
            elif '신혼' in mate:
                title_parts.append('신혼부부')
            elif '가족' in mate:
                title_parts.append('가족')
        
        if vibe:
            vibe_clean = vibe.replace(' (Unique & Pop)', '').replace('/', '')
            if title_parts:
                title = f"{title_parts[0]}을 위한 {style_keyword} {vibe_clean} 스타일"
            else:
                title = f"{style_keyword} {vibe_clean} 스타일"
        else:
            title = "당신만의 스타일"
        
        # 설명 생성
        description_parts = []
        
        # 첫 번째 문장: 사용자 특성 반영
        if mate and priority:
            description_parts.append(
                f"당신의 {mate} 구성과 {priority}를 반영해"
            )
        elif mate:
            description_parts.append(f"당신의 {mate} 구성에 맞춰")
        elif priority:
            description_parts.append(f"당신의 {priority}을 고려해")
        else:
            description_parts.append("당신의 라이프스타일을 반영해")
        
        # 컬러 및 제품 구성
        if color and product_composition:
            description_parts.append(f"{color} 컬러의 오브제컬렉션 {product_str}로 구성했어요.")
        elif product_composition:
            description_parts.append(f"오브제컬렉션 {product_str}로 구성했어요.")
        else:
            description_parts.append("오브제컬렉션으로 구성했어요.")
        
        # 두 번째 문장: 예산/특징
        if budget:
            if '고급형' in budget or '프리미엄' in budget:
                description_parts.append("완성도와 기능성을 모두 갖춘 프리미엄 추천이에요.")
            elif '표준형' in budget:
                description_parts.append("완성도와 기능성을 모두 갖춘 표준 예산 범위 내의 추천이에요.")
            else:
                description_parts.append("완성도와 기능성을 모두 갖춘 추천이에요.")
        else:
            description_parts.append("완성도와 기능성을 모두 갖춘 추천이에요.")
        
        description = ' '.join(description_parts)
        description = description.replace('. ', '.<br>').replace(' ', ' ')
        
        return title, description
    
    # _build_recommendation_reason 메서드는 제거됨
    # 추천 이유 생성은 recommendation_reason_generator.py의 RecommendationReasonGenerator를 사용


# ============================================================
# Singleton 인스턴스
# ============================================================
recommendation_engine = RecommendationEngine()

