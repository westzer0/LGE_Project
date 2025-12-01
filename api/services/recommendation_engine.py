"""
Recommendation Engine Service Layer

책임:
1. 사용자 프로필 검증
2. Hard Filter (필터링)
3. Soft Score (스코어링)
4. 최종 추천 반환
"""
from typing import Dict, List
from django.db.models import QuerySet
from api.models import Product
from api.rule_engine import UserProfile, build_profile
from api.utils.scoring import calculate_product_score


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
        limit: int = 3
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
            
            # 3. Soft Scoring (가중치 기반 점수)
            scored_products = self._score_products(
                filtered_products,
                user_profile
            )
            
            # 4. 정렬 및 상위 K개 선택
            top_products = sorted(
                scored_products,
                key=lambda x: x['score'],
                reverse=True
            )[:limit]
            
            # 5. 최종 포맷팅
            recommendations = [
                self._format_recommendation(item, user_profile)
                for item in top_products
            ]
            
            return {
                'success': True,
                'count': len(recommendations),
                'recommendations': recommendations,
            }
        
        except ValueError as e:
            return {
                'success': False,
                'error': str(e),
                'recommendations': []
            }
        except Exception as e:
            import traceback
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
        Step 1: Hard Filtering
        - 카테고리 필터
        - 가격 범위 필터
        - 스펙 존재 필터
        - 가족 인원 필터 (ProductDemographics 기반)
        - 반려동물 필터 (제품 스펙/이름 기반)
        """
        # 예산 범위 계산
        budget_level = user_profile.get('budget_level', 'medium')
        min_price, max_price = self.budget_mapping.get(
            budget_level,
            self.budget_mapping['medium']
        )
        
        categories = user_profile.get('categories', [])
        household_size = user_profile.get('household_size', 2)
        has_pet = user_profile.get('has_pet', False)
        
        # Django ORM 쿼리
        products = (
            Product.objects
            .filter(
                is_active=True,
                category__in=categories,
                price__gte=min_price,
                price__lte=max_price,
                price__gt=0,  # 가격 0 제외
            )
        )
        
        # 스펙이 있는 제품만 (ProductSpec이 연결된 제품)
        products = products.filter(spec__isnull=False)
        
        # 가족 인원 기반 필터링 (ProductDemographics 활용)
        if household_size == 1:
            # 1인 가구: 작은 용량의 제품 우선
            # ProductDemographics의 family_types에 '1인가구'가 포함된 제품 우선
            pass  # 하드 필터링보다는 스코어링에서 처리
        elif household_size >= 4:
            # 4인 이상 가족: 대용량 제품 필터링
            # 큰 용량을 나타내는 키워드가 있는 제품만
            pass  # 하드 필터링보다는 스코어링에서 처리
        
        # 반려동물 기반 필터링
        if has_pet:
            # 반려동물이 있는 경우: 반려동물 관련 기능이 있는 제품만 필터링
            # 실제로는 스코어링에서 처리하되, 제품 이름/스펙에 '펫', 'pet', '반려동물' 등이 포함된 것만
            pass  # 하드 필터링보다는 스코어링에서 처리
        else:
            # 반려동물이 없는 경우: 반려동물 전용 기능이 있는 제품은 제외하지 않음
            # 다만 스코어링에서 점수 감점 가능
            pass
        
        print(f"[Filter] 카테고리: {categories}, 가격: {min_price}~{max_price}원, 가족: {household_size}명, 반려동물: {has_pet}, 결과: {products.count()}개")
        
        return products
    
    def _score_products(self, products: QuerySet, user_profile: dict) -> List[dict]:
        """
        Step 2: Soft Scoring
        - 각 제품 점수 계산 (스코어링 함수 호출)
        """
        scored = []
        
        # UserProfile 객체 생성 (scoring 함수 호환성)
        profile = UserProfile(
            vibe=user_profile.get('vibe', ''),
            household_size=str(user_profile.get('household_size', 2)),
            has_pet=user_profile.get('has_pet', False),  # 반려동물 정보 추가
            housing_type=user_profile.get('housing_type', ''),
            main_space=user_profile.get('main_space', 'living'),
            space_size=user_profile.get('space_size', 'medium'),
            priority=user_profile.get('priority', 'value'),
            budget_level=user_profile.get('budget_level', 'medium'),
            target_categories=user_profile.get('categories', []),
        )
        
        # 추가 사용자 정보를 profile 객체에 저장 (스코어링에서 사용)
        profile._household_size_int = user_profile.get('household_size', 2)
        profile._has_pet = user_profile.get('has_pet', False)
        profile._cooking = user_profile.get('cooking', 'sometimes')
        profile._laundry = user_profile.get('laundry', 'weekly')
        
        for idx, product in enumerate(products[:50], 1):  # 최대 50개까지만 처리
            try:
                # 스코어링 함수 호출
                score = calculate_product_score(
                    product=product,
                    profile=profile
                )
                
                scored.append({
                    'product': product,
                    'score': score,
                })
                
                if idx <= 3:
                    print(f"[Score] {idx}. {product.name}: {score:.2f}")
            
            except Exception as e:
                print(f"[Score Error] {product.name}: {e}")
                # 스코어 계산 실패 시 기본값 0.5
                scored.append({
                    'product': product,
                    'score': 0.5,
                })
        
        return scored
    
    def _format_recommendation(self, item: dict, user_profile: dict) -> dict:
        """
        Step 3: 최종 포맷팅
        - API 응답 형식으로 변환
        """
        product = item['product']
        score = item['score']
        
        # 추천 이유 생성
        reason = self._build_recommendation_reason(product, user_profile, score)
        
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
    
    def _build_recommendation_reason(
        self,
        product: Product,
        user_profile: dict,
        score: float
    ) -> str:
        """
        추천 이유 생성
        """
        reasons = []
        
        # 점수 기반 이유
        if score >= 0.8:
            priority = user_profile.get('priority', 'value')
            priority_labels = {
                'design': '디자인',
                'tech': '기술 사양',
                'eco': '에너지 효율',
                'value': '가성비',
            }
            reasons.append(
                f"당신의 선호도({priority_labels.get(priority, '개인맞춤')})에 "
                f"가장 잘 맞는 제품입니다."
            )
        elif score >= 0.6:
            reasons.append("우수한 성능과 가성비를 갖춘 제품입니다.")
        else:
            reasons.append("조건에 맞는 추천 제품입니다.")
        
        # 할인 정보
        if product.discount_price and product.price and product.price > 0:
            discount_pct = (
                (float(product.price) - float(product.discount_price)) / float(product.price) * 100
            )
            if discount_pct > 10:
                reasons.append(f"{int(discount_pct)}% 할인 중입니다.")
        
        return " ".join(reasons)


# ============================================================
# Singleton 인스턴스
# ============================================================
recommendation_engine = RecommendationEngine()

