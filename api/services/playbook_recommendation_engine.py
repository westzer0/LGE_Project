"""
Playbook 설계 기반 추천 엔진

기존 RecommendationEngine과 병행하여 사용 가능
"""
import logging
import traceback
from typing import Dict, List
from django.db.models import QuerySet
from api.models import Product
from api.rule_engine import UserProfile, build_profile
from api.utils.playbook_scoring import playbook_scoring_model, ScoreBreakdown
from api.utils.playbook_filters import playbook_hard_filter
from api.services.playbook_explanation_generator import playbook_explanation_generator
from api.services.chatgpt_service import chatgpt_service
from api.utils.product_type_classifier import extract_product_type

logger = logging.getLogger(__name__)


class PlaybookRecommendationEngine:
    """Playbook 설계 기반 추천 엔진"""
    
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
    
    def get_recommendations(
        self,
        user_profile: dict,
        limit: int = 3,
        onboarding_data: dict = None
    ) -> dict:
        """
        Playbook 기반 추천 반환
        
        Args:
            user_profile: 사용자 프로필
            limit: 추천 개수
            onboarding_data: 온보딩 데이터 (생활 패턴 등)
            
        Returns:
            추천 결과 딕셔너리 (점수 breakdown 포함)
        """
        try:
            # 1. 입력 검증
            self._validate_user_profile(user_profile)
            
            # 온보딩 데이터 초기화
            if onboarding_data is None:
                onboarding_data = {}
            
            # 2. Step 1: Hard Filter
            # 카테고리 기반 필터링 (모든 카테고리 포함)
            categories = user_profile.get('categories', ['TV', 'KITCHEN', 'LIVING', 'AIR'])
            if not categories:
                categories = ['TV', 'KITCHEN', 'LIVING', 'AIR']
            
            # 모든 카테고리에서 제품 가져오기
            all_filtered_products = []
            for category in categories:
                temp_profile = user_profile.copy()
                temp_profile['categories'] = [category]
                filtered = self._apply_hard_filter(temp_profile, onboarding_data)
                all_filtered_products.extend(filtered)
            
            # 중복 제거
            seen_product_ids = set()
            filtered_products = []
            for p in all_filtered_products:
                if p.id not in seen_product_ids:
                    seen_product_ids.add(p.id)
                    filtered_products.append(p)
            
            if not filtered_products:
                return {
                    'success': False,
                    'message': '조건에 맞는 제품이 없습니다.',
                    'recommendations': []
                }
            
            print(f"[Playbook Hard Filter] 전체 필터링 후: {len(filtered_products)}개")
            
            # 3. Step 2: 제품 타입별 추천 (필수 + 조건부)
            # 필수 제품 타입: TV, 냉장고, 에어컨, 세탁기
            required_product_types = ['TV', '냉장고', '에어컨', '세탁기']
            
            # 조건부 제품 타입 결정 (평수, 가구원수, 가격대 기반)
            optional_product_types = self._determine_optional_product_types(
                user_profile, onboarding_data
            )
            
            # 전체 추천할 제품 타입 목록
            target_product_types = required_product_types + optional_product_types
            
            print(f"[Playbook Recommendation] 필수 제품 타입: {required_product_types}")
            print(f"[Playbook Recommendation] 조건부 제품 타입: {optional_product_types}")
            print(f"[Playbook Recommendation] 전체 제품 타입: {target_product_types}")
            
            all_recommendations = []
            
            # 제품 타입별로 추천
            for product_type in target_product_types:
                # 제품 타입별 제품 필터링
                type_products = []
                for p in filtered_products:
                    p_type = extract_product_type(p)
                    if p_type == product_type:
                        type_products.append(p)
                
                if not type_products:
                    print(f"[Playbook Recommendation] 제품 타입 '{product_type}': 추천 제품 없음")
                    continue
                
                # 제품 타입별 스코어링
                scored_products = self._score_products(
                    type_products,
                    user_profile,
                    onboarding_data
                )
                
                # 제품 타입별 상위 3개 선택
                top_type_products = sorted(
                    scored_products,
                    key=lambda x: x['score_breakdown'].total_score,
                    reverse=True
                )[:3]  # 각 제품 타입별로 최대 3개
                
                # 제품 타입별 추천 포맷팅 (GPT Explanation 포함)
                type_recommendations = [
                    self._format_recommendation_with_explanation(
                        item,
                        user_profile,
                        onboarding_data
                    )
                    for item in top_type_products
                ]
                
                all_recommendations.extend(type_recommendations)
                print(f"[Playbook Recommendation] 제품 타입 '{product_type}': {len(type_recommendations)}개 추천")
            
            # 중복 제품 제거 (product_id 및 name 기반)
            seen_product_ids = set()
            seen_product_names = set()
            unique_recommendations = []
            for rec in all_recommendations:
                product_id = rec.get('product_id')
                product_name = rec.get('name') or rec.get('model', '')
                
                # product_id로 먼저 체크
                if product_id and product_id not in seen_product_ids:
                    seen_product_ids.add(product_id)
                    if product_name:
                        seen_product_names.add(product_name)
                    unique_recommendations.append(rec)
                # product_id가 없거나 중복이면 name으로 체크
                elif product_name and product_name not in seen_product_names:
                    seen_product_names.add(product_name)
                    if product_id:
                        seen_product_ids.add(product_id)
                    unique_recommendations.append(rec)
                # 둘 다 중복이면 스킵
            
            # 제품 타입별로 그룹화하여 순위 매기기 (각 타입별 3개씩)
            # 제품 타입 우선순위: 필수 제품 타입 먼저, 그 다음 조건부
            product_type_priority = {}
            for idx, pt in enumerate(required_product_types):
                product_type_priority[pt] = idx
            for idx, pt in enumerate(optional_product_types):
                product_type_priority[pt] = len(required_product_types) + idx
            
            # 제품 타입별로 그룹화
            by_product_type = {}
            for rec in unique_recommendations:
                product_type = rec.get('product_type', '기타')
                if product_type not in by_product_type:
                    by_product_type[product_type] = []
                by_product_type[product_type].append(rec)
            
            # 제품 타입 우선순위대로 정렬하여 순위 매기기
            sorted_product_types = sorted(
                by_product_type.keys(),
                key=lambda pt: product_type_priority.get(pt, 999)
            )
            
            final_recommendations = []
            rank = 1
            for product_type in sorted_product_types:
                type_recs = sorted(
                    by_product_type[product_type],
                    key=lambda x: x.get('total_score', 0),
                    reverse=True
                )[:3]  # 각 타입별 최대 3개
                
                for rec in type_recs:
                    rec['rank'] = rank
                    final_recommendations.append(rec)
                    rank += 1
            
            recommendations = final_recommendations
            
            print(f"[Playbook Recommendation] 최종 추천: {len(recommendations)}개 (제품 타입별 3개씩)")
            
            return {
                'success': True,
                'count': len(recommendations),
                'recommendations': recommendations,
                'user_profile_summary': self._generate_user_profile_summary(user_profile, onboarding_data)
            }
        
        except Exception as e:
            logger.error(f"Playbook recommendation error: {str(e)}", exc_info=True)
            print(f"Playbook Recommendation Error: {traceback.format_exc()}")
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
    
    def _apply_hard_filter(
        self,
        user_profile: dict,
        onboarding_data: dict
    ) -> list:
        """
        Step 1: Hard Filter 적용
        
        정책 테이블 기반 필터링
        """
        # 기본 필터 (카테고리, 가격)
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
                price__gte=min_price,
                price__lte=max_price,
                price__gt=0,
            )
            .filter(spec__isnull=False)
        )
        
        products_list = list(products)
        
        # Playbook Hard Filter 적용
        filtered = playbook_hard_filter.apply_filters(
            products_list,
            user_profile,
            onboarding_data
        )
        
        return filtered
    
    def _score_products(
        self,
        products: list,
        user_profile: dict,
        onboarding_data: dict
    ) -> List[Dict]:
        """
        Step 2: Scoring Model
        
        5개 컴포넌트 합산 방식
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
            priority=user_profile.get('priority', 'value') if isinstance(user_profile.get('priority'), str) else (user_profile.get('priority', ['value'])[0] if isinstance(user_profile.get('priority'), list) else 'value'),
            budget_level=user_profile.get('budget_level', 'medium'),
            target_categories=user_profile.get('categories', []),
        )
        
        for idx, product in enumerate(products[:50], 1):
            try:
                # Playbook Scoring Model 사용
                score_breakdown = playbook_scoring_model.calculate_product_score(
                    product=product,
                    profile=profile,
                    user_profile=user_profile,
                    onboarding_data=onboarding_data
                )
                
                scored.append({
                    'product': product,
                    'score_breakdown': score_breakdown,
                })
                
                if idx <= 3:
                    print(f"[Playbook Score] {idx}. {product.name}: Total={score_breakdown.total_score:.1f} "
                          f"(Spec={score_breakdown.spec_score:.1f}, Preference={score_breakdown.preference_score:.1f}, "
                          f"Lifestyle={score_breakdown.lifestyle_score:.1f}, Review={score_breakdown.review_score:.1f}, "
                          f"Price={score_breakdown.price_score:.1f})")
            
            except Exception as e:
                logger.warning(f"Score calculation failed for product {product.id}: {str(e)}", exc_info=True)
                print(f"[Playbook Score Error] {product.name}: {e}")
                # 기본 점수
                score_breakdown = ScoreBreakdown()
                scored.append({
                    'product': product,
                    'score_breakdown': score_breakdown,
                })
        
        return scored
    
    def _format_recommendation_with_explanation(
        self,
        item: dict,
        user_profile: dict,
        onboarding_data: dict
    ) -> dict:
        """
        Step 3: GPT Explanation Layer
        
        점수 breakdown을 활용한 설명 생성
        """
        product = item['product']
        score_breakdown = item['score_breakdown']
        
        # 제품 타입 추출
        product_type = extract_product_type(product) or '기타'
        
        # 기본 정보
        recommendation = {
            'product_id': product.id,
            'model': product.name,
            'name': product.name,
            'model_number': product.model_number,
            'category': product.category,
            'category_display': product.get_category_display(),
            'product_type': product_type,  # 제품 타입 추가
            'price': float(product.price) if product.price else 0,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_url': product.image_url or '',
            'total_score': round(score_breakdown.total_score, 1),
            'score_breakdown': score_breakdown.to_dict(),
        }
        
        # GPT Explanation 생성
        explanation = playbook_explanation_generator.generate_explanation(
            product=product,
            score_breakdown=score_breakdown,
            user_profile=user_profile,
            onboarding_data=onboarding_data
        )
        
        recommendation['explanation'] = explanation
        
        return recommendation
    
    def _generate_user_profile_summary(
        self,
        user_profile: dict,
        onboarding_data: dict
    ) -> str:
        """사용자 프로필 요약 생성"""
        parts = []
        
        household_size = user_profile.get('household_size', 2)
        housing_type = user_profile.get('housing_type', 'apartment')
        pyung = user_profile.get('pyung', 25)
        vibe = user_profile.get('vibe', 'modern')
        
        housing_map = {
            'studio': '원룸',
            'apartment': '아파트',
            'detached': '단독주택',
            'villa': '빌라/연립',
            'officetel': '오피스텔'
        }
        
        vibe_map = {
            'modern': '모던한',
            'cozy': '따뜻한',
            'luxury': '럭셔리한',
            'pop': '트렌디한'
        }
        
        parts.append(f"{household_size}인 가족이")
        parts.append(f"{housing_map.get(housing_type, '아파트')} {pyung}평에 살며")
        parts.append(f"{vibe_map.get(vibe, '모던한')} 인테리어 스타일을 선호합니다.")
        
        return " ".join(parts)
    
    def _determine_optional_product_types(
        self,
        user_profile: dict,
        onboarding_data: dict
    ) -> list:
        """
        평수, 가구원수, 가격대에 따라 조건부 제품 타입 결정
        
        Args:
            user_profile: 사용자 프로필
            onboarding_data: 온보딩 데이터
            
        Returns:
            조건부 제품 타입 목록
        """
        optional_types = []
        
        household_size = user_profile.get('household_size', 2)
        pyung = user_profile.get('pyung', 25)
        budget_level = user_profile.get('budget_level', 'medium')
        budget_amount = user_profile.get('budget_amount', 0)
        
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        # 가구원수 기반 추가 제품
        if household_size >= 4:
            # 4인 이상: 건조기, 식기세척기 추천
            optional_types.append('건조기')
            optional_types.append('식기세척기')
        elif household_size >= 3:
            # 3인: 건조기 추천
            optional_types.append('건조기')
        
        # 평수 기반 추가 제품
        if pyung >= 35:
            # 35평 이상: 공기청정기, 제습기, 가습기 등 공기 관리 제품
            optional_types.append('공기청정기')
            if pyung >= 40:
                optional_types.append('제습기')
        elif pyung >= 25:
            # 25평 이상: 공기청정기
            optional_types.append('공기청정기')
        
        # 가격대 기반 추가 제품
        if budget_level in ['high', 'premium', 'luxury'] or budget_amount >= 5000000:
            # 고가 예산: 와인셀러, 안마의자 등 프리미엄 제품
            optional_types.append('와인셀러')
            if pyung >= 30:
                optional_types.append('안마의자')
        elif budget_level in ['medium', 'standard'] or (budget_amount >= 2000000 and budget_amount < 5000000):
            # 중가 예산: 정수기, 청소기 등
            optional_types.append('정수기')
            optional_types.append('청소기')
        
        # 온보딩 데이터 기반 추가 제품
        if cooking in ['high', 'often']:
            # 요리를 자주 하는 경우
            optional_types.append('식기세척기')
            optional_types.append('전기레인지')
            if budget_level in ['high', 'premium']:
                optional_types.append('오븐')
        
        if laundry in ['daily', 'weekly']:
            # 세탁을 자주 하는 경우
            if household_size >= 3:
                optional_types.append('건조기')
            if household_size >= 4:
                optional_types.append('의류건조기')
        
        if media in ['gaming', 'ott', 'movie', 'heavy']:
            # 미디어를 많이 사용하는 경우
            # TV는 이미 필수에 포함되어 있음
            pass
        
        # 중복 제거 및 정렬
        optional_types = list(dict.fromkeys(optional_types))  # 순서 유지하며 중복 제거
        
        return optional_types


# Singleton 인스턴스
playbook_recommendation_engine = PlaybookRecommendationEngine()

