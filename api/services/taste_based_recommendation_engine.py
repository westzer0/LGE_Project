"""
Taste 기반 추천 엔진

1. Taste별로 MAIN CATEGORY를 N개 선택 (Oracle DB의 PRODUCT.MAIN_CATEGORY 기준)
2. 각 CATEGORY 내에서 PRODUCT ID 3개씩 선택
3. 결과적으로 3N개의 Product를 반환
"""
from typing import Dict, List, Optional
from ..rule_engine import UserProfile
from ..utils.taste_category_selector import get_categories_for_taste
from ..utils.taste_scoring import calculate_product_score_with_taste_logic
from ..utils.scoring import calculate_product_score
from ..db.oracle_client import get_connection


class TasteBasedRecommendationEngine:
    """
    Taste 기반 추천 엔진
    
    로직:
    1. Taste별로 MAIN CATEGORY를 N개 선택
    2. 각 CATEGORY 내에서 제품을 필터링하고 스코어링
    3. 각 CATEGORY에서 상위 3개씩 선택
    4. 총 3N개 제품 반환
    """
    
    def __init__(self):
        self.budget_mapping = {
            'low': (0, 5_000_000),
            'medium': (500_000, 20_000_000),
            'high': (2_000_000, 100_000_000),
            'budget': (0, 5_000_000),
            'standard': (500_000, 20_000_000),
            'premium': (2_000_000, 100_000_000),
            'luxury': (2_000_000, 100_000_000),
        }
    
    def get_recommendations(
        self,
        user_profile: dict,
        taste_id: int,
        num_categories: int = None,
        limit_per_category: int = 3
    ) -> dict:
        """
        Taste 기반 추천
        
        Args:
            user_profile: 사용자 프로필
            taste_id: 취향 ID
            num_categories: 선택할 카테고리 개수 (None이면 자동 결정)
            limit_per_category: 카테고리당 선택할 제품 개수 (기본 3개)
        
        Returns:
            {
                'success': True/False,
                'count': 총 제품 개수,
                'categories': 선택된 카테고리 리스트,
                'recommendations': [
                    {
                        'product_id': ...,
                        'category': ...,
                        'model': ...,
                        'price': ...,
                        'score': ...,
                        ...
                    },
                    ...
                ]
            }
        """
        try:
            # 1. 온보딩 데이터 추출
            onboarding_data = user_profile.get('onboarding_data', {})
            
            # 2. Taste별로 MAIN CATEGORY 선택
            selected_categories = get_categories_for_taste(
                taste_id=taste_id,
                onboarding_data=onboarding_data,
                num_categories=num_categories
            )
            
            if not selected_categories:
                return {
                    'success': False,
                    'message': '선택된 카테고리가 없습니다.',
                    'categories': [],
                    'recommendations': []
                }
            
            # 3. 각 카테고리별로 제품 선택
            all_recommendations = []
            
            for category in selected_categories:
                # 카테고리별 제품 필터링 (Oracle DB 직접 쿼리)
                category_products = self._filter_products_by_category(
                    category=category,
                    user_profile=user_profile
                )
                
                if not category_products:
                    print(f"[Recommendation] 카테고리 '{category}': 추천 제품 없음")
                    continue
                
                # 카테고리별 제품 스코어링
                scored_products = self._score_products_in_category(
                    products=category_products,
                    category=category,
                    user_profile=user_profile,
                    taste_id=taste_id,
                    onboarding_data=onboarding_data
                )
                
                # 상위 N개 선택
                top_products = sorted(
                    scored_products,
                    key=lambda x: x['score'],
                    reverse=True
                )[:limit_per_category]
                
                all_recommendations.extend(top_products)
            
            # 4. 결과 포맷팅
            formatted_recommendations = [
                self._format_recommendation(rec, user_profile)
                for rec in all_recommendations
            ]
            
            return {
                'success': True,
                'count': len(formatted_recommendations),
                'categories': selected_categories,
                'recommendations': formatted_recommendations
            }
            
        except Exception as e:
            import traceback
            print(f"[TasteBasedRecommendationEngine Error] {str(e)}")
            print(traceback.format_exc())
            return {
                'success': False,
                'message': f'추천 실패: {str(e)}',
                'categories': [],
                'recommendations': []
            }
    
    def _filter_products_by_category(
        self,
        category: str,
        user_profile: dict
    ) -> List[Dict]:
        """
        카테고리별 제품 필터링 (Oracle DB 직접 쿼리)
        
        Args:
            category: MAIN CATEGORY (Oracle DB의 MAIN_CATEGORY 컬럼 값)
            user_profile: 사용자 프로필
        
        Returns:
            필터링된 제품 리스트 (딕셔너리)
        """
        # 예산 필터
        budget_level = user_profile.get('budget_level', 'medium')
        min_price, max_price = self.budget_mapping.get(budget_level, (0, 100_000_000))
        
        # Oracle DB에서 직접 쿼리
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        PRODUCT_ID,
                        PRODUCT_NAME,
                        MAIN_CATEGORY,
                        SUB_CATEGORY,
                        MODEL_CODE,
                        PRICE,
                        RATING,
                        URL
                    FROM PRODUCT
                    WHERE MAIN_CATEGORY = :category
                      AND STATUS = '판매중'
                      AND PRICE > 0
                      AND PRICE IS NOT NULL
                      AND PRICE >= :min_price
                      AND PRICE <= :max_price
                    ORDER BY PRICE
                """, {
                    'category': category,
                    'min_price': min_price,
                    'max_price': max_price
                })
                
                # 딕셔너리로 변환
                col_names = [desc[0] for desc in cur.description]
                products = []
                for row in cur.fetchall():
                    product_dict = dict(zip(col_names, row))
                    products.append(product_dict)
                
                return products
    
    def _score_products_in_category(
        self,
        products: List[Dict],
        category: str,
        user_profile: dict,
        taste_id: int,
        onboarding_data: dict
    ) -> List[Dict]:
        """
        카테고리 내 제품 스코어링
        
        Args:
            products: 제품 리스트 (Oracle DB에서 가져온 딕셔너리)
            category: 카테고리
            user_profile: 사용자 프로필
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터
        
        Returns:
            스코어가 포함된 제품 리스트
        """
        from ..rule_engine import UserProfile as UserProfileClass
        from ..models import Product as DjangoProduct
        
        # UserProfile 생성
        profile = UserProfileClass(
            vibe=user_profile.get('vibe', 'modern'),
            household_size=user_profile.get('household_size', 2),
            housing_type=user_profile.get('housing_type', 'apartment'),
            priority=user_profile.get('priority', 'value'),
            budget_level=user_profile.get('budget_level', 'medium'),
        )
        
        # 추가 속성 설정
        profile._pyung = user_profile.get('pyung', 25)
        profile._has_pet = user_profile.get('has_pet', False)
        profile._cooking = user_profile.get('cooking', 'sometimes')
        profile._laundry = user_profile.get('laundry', 'weekly')
        profile._media = user_profile.get('media', 'balanced')
        
        scored_products = []
        
        for product_dict in products[:100]:  # 최대 100개만 처리
            try:
                # Oracle DB의 PRODUCT_ID로 Django Product 모델 가져오기
                # (scoring 로직이 Django Product 모델을 사용하므로)
                product_id = product_dict.get('PRODUCT_ID')
                if not product_id:
                    continue
                
                # Django Product 모델에서 가져오기 (없으면 스킵)
                try:
                    django_product = DjangoProduct.objects.get(id=product_id)
                except DjangoProduct.DoesNotExist:
                    # Oracle DB에만 있고 Django DB에 없으면 기본 스코어 사용
                    score = 0.5  # 기본 점수
                else:
                    # Taste 기반 스코어링
                    score = calculate_product_score_with_taste_logic(
                        product=django_product,
                        profile=profile,
                        taste_id=taste_id,
                        onboarding_data=onboarding_data
                    )
                
                scored_products.append({
                    'product_dict': product_dict,  # Oracle DB 원본 데이터
                    'django_product': django_product if 'django_product' in locals() else None,
                    'category': category,
                    'score': score,
                })
            except Exception as e:
                print(f"[Score Error] {product_dict.get('PRODUCT_NAME', 'Unknown')}: {str(e)}")
                continue
        
        return scored_products
    
    def _format_recommendation(self, rec: Dict, user_profile: dict) -> Dict:
        """
        추천 결과 포맷팅
        
        Args:
            rec: 스코어링된 제품 정보
            user_profile: 사용자 프로필
        
        Returns:
            포맷팅된 추천 결과
        """
        product_dict = rec.get('product_dict', {})
        django_product = rec.get('django_product')
        
        # Oracle DB 데이터 우선 사용
        product_id = product_dict.get('PRODUCT_ID')
        product_name = product_dict.get('PRODUCT_NAME', '')
        price = product_dict.get('PRICE', 0) or 0
        model_code = product_dict.get('MODEL_CODE', '')
        
        # Django Product가 있으면 추가 정보 사용
        if django_product:
            discount_price = int(django_product.discount_price) if django_product.discount_price else int(price)
            image_url = django_product.image_url or ''
        else:
            discount_price = int(price)
            image_url = product_dict.get('URL', '')
        
        return {
            'product_id': product_id,
            'category': rec['category'],
            'model': model_code or product_name,
            'name': product_name,
            'price': int(price),
            'discount_price': discount_price,
            'image_url': image_url,
            'score': rec['score'],
            'product_type': rec.get('product_type', rec['category']),
        }


# 싱글톤 인스턴스
taste_based_recommendation_engine = TasteBasedRecommendationEngine()

