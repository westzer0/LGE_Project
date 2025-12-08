"""
Playbook 설계 기반 Scoring 모델

TotalScore = SpecScore + PreferenceScore + LifestyleScore + ReviewScore + PriceScore
각 Score는 정수/실수로 합산 가능한 형태
"""
import json
from typing import Dict, Optional, List
from dataclasses import dataclass
from ..models import Product, ProductReview
from .policy_loader import policy_loader
from .scoring import (
    parse_spec_json, get_spec_value, parse_number,
    score_resolution, score_brightness, score_refresh_rate,
    score_panel_type, score_power_consumption, score_size,
    score_capacity, score_energy_efficiency, score_design
)
from ..rule_engine import UserProfile


@dataclass
class ScoreBreakdown:
    """점수 Breakdown 구조"""
    spec_score: float = 0.0
    preference_score: float = 0.0
    lifestyle_score: float = 0.0
    review_score: float = 0.0
    price_score: float = 0.0
    
    @property
    def total_score(self) -> float:
        """총점 계산"""
        return (
            self.spec_score +
            self.preference_score +
            self.lifestyle_score +
            self.review_score +
            self.price_score
        )
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "SpecScore": round(self.spec_score, 1),
            "PreferenceScore": round(self.preference_score, 1),
            "LifestyleScore": round(self.lifestyle_score, 1),
            "ReviewScore": round(self.review_score, 1),
            "PriceScore": round(self.price_score, 1),
            "TotalScore": round(self.total_score, 1)
        }


class PlaybookScoringModel:
    """Playbook 설계 기반 Scoring 모델"""
    
    def calculate_product_score(
        self,
        product: Product,
        profile: UserProfile,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> ScoreBreakdown:
        """
        제품 점수 계산 (5개 컴포넌트 합산)
        
        Args:
            product: 제품 객체
            profile: UserProfile 객체
            user_profile: 사용자 프로필 딕셔너리
            onboarding_data: 온보딩 데이터 딕셔너리
            
        Returns:
            ScoreBreakdown 객체
        """
        breakdown = ScoreBreakdown()
        
        # 1. SpecScore 계산
        breakdown.spec_score = self._calculate_spec_score(
            product, profile, user_profile, onboarding_data
        )
        
        # 2. PreferenceScore 계산
        breakdown.preference_score = self._calculate_preference_score(
            product, profile, user_profile
        )
        
        # 3. LifestyleScore 계산
        breakdown.lifestyle_score = self._calculate_lifestyle_score(
            product, profile, user_profile, onboarding_data
        )
        
        # 4. ReviewScore 계산
        breakdown.review_score = self._calculate_review_score(product)
        
        # 5. PriceScore 계산
        breakdown.price_score = self._calculate_price_score(
            product, profile, user_profile
        )
        
        return breakdown
    
    def _calculate_spec_score(
        self,
        product: Product,
        profile: UserProfile,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> float:
        """
        SpecScore 계산
        
        온보딩과 카테고리별 스펙 적정 구간 매칭을 통해 점수 부여
        """
        spec = parse_spec_json(product)
        if not spec:
            return 0.0
        
        score = 0.0
        category = product.category
        family_size = user_profile.get('household_size', 2)
        
        # 가족 구성 기반 용량 점수
        if category == "KITCHEN" or "냉장고" in product.name:
            capacity = self._extract_capacity(spec)
            if capacity:
                rule = policy_loader.get_spec_score_rules(
                    (f"{family_size}인", category, "capacity_l")
                )
                if rule:
                    ideal_range = rule.get('ideal_range', [])
                    tolerance = rule.get('tolerance', 50)
                    base_score = rule.get('score', 10)
                    
                    if ideal_range:
                        min_val, max_val = ideal_range
                        if min_val - tolerance <= capacity <= max_val + tolerance:
                            # 적정 범위 내
                            diff = min(abs(capacity - min_val), abs(capacity - max_val))
                            score += base_score * (1 - diff / tolerance)
                        elif capacity < min_val - tolerance:
                            # 용량 부족: 감점
                            score += max(0, base_score * 0.3)
                        else:
                            # 용량 과다: 약간 감점
                            score += max(0, base_score * 0.5)
        
        # TV 패널 타입 점수
        if category == "TV":
            panel_type = get_spec_value(spec, "패널 타입", "").upper()
            media_focus = onboarding_data.get('media', 'balanced')
            
            if media_focus in ['ott', 'movie'] and 'OLED' in panel_type:
                rule = policy_loader.get_spec_score_rules(
                    ("영화", category, "panel_type")
                )
                if rule:
                    score += rule.get('score', 15)  # OLED는 높은 점수
                else:
                    score += 15
            elif media_focus in ['ott', 'movie']:
                # OLED가 아니어도 영화 감상용 TV는 기본 점수
                score += 5
        
        # 게임 관련 점수
        if category == "TV":
            refresh_rate_str = get_spec_value(spec, "주사율", "")
            refresh_rate = parse_number(refresh_rate_str, 0)
            
            if refresh_rate >= 120:
                rule = policy_loader.get_spec_score_rules(
                    ("게임", category, "refresh_rate")
                )
                if rule:
                    score += rule.get('score', 15)  # 고주사율은 높은 점수
                else:
                    score += 15
            elif refresh_rate >= 60:
                score += 5  # 기본 주사율도 약간의 점수
        
        # 드레스룸 선택 시 세탁기/건조기 보너스
        main_space = user_profile.get('main_space', '')
        if main_space in ['dressing', 'all']:
            if category == "LIVING" or "세탁기" in product.name or "건조기" in product.name:
                rule = policy_loader.get_spec_score_rules(
                    ("드레스룸", category, "category_bonus")
                )
                if rule:
                    score += rule.get('score', 5)
        
        return max(0.0, score)
    
    def _calculate_preference_score(
        self,
        product: Product,
        profile: UserProfile,
        user_profile: Dict
    ) -> float:
        """
        PreferenceScore 계산
        
        사용자가 선택한 우선순위에 따라 배율 적용
        """
        priority_list = user_profile.get('priority', [])
        if not priority_list:
            priority = profile.priority or 'value'
            priority_list = [priority]
        
        score = 0.0
        spec = parse_spec_json(product)
        
        # 우선순위별 배율 적용
        for rank, priority in enumerate(priority_list[:3], 1):
            rule = policy_loader.get_preference_score_rules(priority, rank)
            if not rule:
                continue
            
            multiplier = rule.get('multiplier', 1.0)
            target_specs = rule.get('target_specs', [])
            
            # 관련 스펙 점수 계산
            spec_score_sum = 0.0
            spec_count = 0
            
            if 'design' in target_specs:
                design_score = score_design(product, profile)
                spec_score_sum += design_score * 10  # 0~1.0을 0~10으로 변환
                spec_count += 1
            
            if 'panel_type' in target_specs and spec:
                panel_score = score_panel_type(spec, profile)
                spec_score_sum += panel_score * 10
                spec_count += 1
            
            if 'ai_feature' in target_specs or 'thinq' in target_specs or 'smart' in target_specs:
                # AI 기능 키워드 확인
                product_name = product.name.upper()
                keywords = rule.get('keywords', ['AI', 'ThinQ', '스마트'])
                has_ai = any(kw in product_name for kw in keywords)
                
                if has_ai:
                    spec_score_sum += 8
                spec_count += 1
            
            if 'energy_efficiency' in target_specs:
                energy_score = score_energy_efficiency(spec, profile)
                spec_score_sum += energy_score * 10
                spec_count += 1
            
            if spec_count > 0:
                avg_spec_score = spec_score_sum / spec_count
                score += avg_spec_score * (multiplier - 1.0)  # 추가 점수만
        
        return max(0.0, score)
    
    def _calculate_lifestyle_score(
        self,
        product: Product,
        profile: UserProfile,
        user_profile: Dict,
        onboarding_data: Dict
    ) -> float:
        """
        LifestyleScore 계산
        
        라이프스타일 응답 기반으로 특정 스펙·제품군 강화
        """
        score = 0.0
        spec = parse_spec_json(product)
        category = product.category
        
        # 요리 빈도
        cooking = onboarding_data.get('cooking', 'sometimes')
        if cooking in ['high', 'often']:
            if category == "KITCHEN" or "냉장고" in product.name:
                capacity = self._extract_capacity(spec)
                if capacity and capacity >= 700:
                    rule = policy_loader.get_lifestyle_score_rules(
                        "요리_high", category, "capacity_l"
                    )
                    if rule:
                        score += rule.get('score', 10)  # 요리 빈도 높으면 더 높은 점수
                    else:
                        score += 10
        
        # 세탁 패턴
        laundry = onboarding_data.get('laundry', 'weekly')
        if laundry == 'daily':
            if "세탁기" in product.name:
                capacity = self._extract_capacity(spec)
                if capacity:
                    rule = policy_loader.get_lifestyle_score_rules(
                        "세탁_daily_small", category, "capacity_kg"
                    )
                    if rule:
                        ideal_range = rule.get('ideal_range', [])
                        if ideal_range and ideal_range[0] <= capacity <= ideal_range[1]:
                            score += rule.get('score', 5)
        
        # 미디어/게임
        media = onboarding_data.get('media', 'balanced')
        if media == 'gaming' and category == "TV":
            refresh_rate_str = get_spec_value(spec, "주사율", "")
            refresh_rate = parse_number(refresh_rate_str, 0)
            
            if refresh_rate >= 120:
                rule = policy_loader.get_lifestyle_score_rules(
                    "게임", category, "refresh_rate"
                )
                if rule:
                    score += rule.get('score', 12)  # 게임용 고주사율은 높은 점수
                else:
                    score += 12
        
        return max(0.0, score)
    
    def _calculate_review_score(self, product: Product) -> float:
        """
        ReviewScore 계산
        
        배치 전처리 또는 실시간 계산
        """
        try:
            reviews = ProductReview.objects.filter(product=product)
            review_count = reviews.count()
            
            if review_count == 0:
                return 0.0
            
            # 별점 추출 (간단한 구현)
            ratings = []
            for review in reviews:
                star_str = review.star or ""
                # 별점 파싱 (예: "4.5", "5점" 등)
                import re
                rating_match = re.search(r'(\d+\.?\d*)', star_str)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            ratings.append(rating)
                    except ValueError:
                        pass
            
            if not ratings:
                # 별점 정보가 없으면 리뷰 개수만 고려
                if review_count >= 200:
                    return 3.0
                elif review_count >= 100:
                    return 2.0
                elif review_count >= 50:
                    return 1.0
                return 0.0
            
            avg_rating = sum(ratings) / len(ratings)
            
            # 규칙 적용
            rules = policy_loader.get_review_score_rules()
            
            for rule in rules:
                condition = rule.get('condition', '')
                rule_score = rule.get('score', 0)
                
                if 'avg_rating >= 4.7 && review_count >= 200' in condition:
                    if avg_rating >= 4.7 and review_count >= 200:
                        return rule_score
                elif 'avg_rating >= 4.5 && review_count >= 100' in condition:
                    if avg_rating >= 4.5 and review_count >= 100:
                        return rule_score
                elif 'avg_rating >= 4.3 && review_count >= 50' in condition:
                    if avg_rating >= 4.3 and review_count >= 50:
                        return rule_score
                elif 'avg_rating < 3.5' in condition:
                    if avg_rating < 3.5:
                        return rule_score
            
            # 기본 점수 계산 (더 명확한 차별화)
            if avg_rating >= 4.5:
                return 12.0  # 매우 높은 평점: 높은 점수
            elif avg_rating >= 4.0:
                return 8.0   # 높은 평점: 중간 점수
            elif avg_rating >= 3.5:
                return 4.0   # 보통 평점: 낮은 점수
            else:
                return -3.0  # 낮은 평점: 감점
                
        except Exception as e:
            print(f"[ReviewScore Error] {product.name}: {e}")
            return 0.0
    
    def _calculate_price_score(
        self,
        product: Product,
        profile: UserProfile,
        user_profile: Dict
    ) -> float:
        """
        PriceScore 계산
        
        온보딩 예산과 제품 실가격 차이를 점수로 환산
        """
        price = float(product.price) if product.price else 0
        discount_price = float(product.discount_price) if product.discount_price else price
        
        budget_level = user_profile.get('budget_level', 'medium')
        budget_amount = user_profile.get('budget_amount', 2000000)
        
        # 예산 범위 매핑
        budget_ranges = {
            'low': 500000,
            'medium': 2000000,
            'high': 5000000,
        }
        
        if budget_amount == 0:
            budget_amount = budget_ranges.get(budget_level, 2000000)
        
        # 규칙 적용
        rules = policy_loader.get_price_score_rules()
        
        for rule in rules:
            condition = rule.get('condition', '')
            rule_score = rule.get('score', 0)
            
            if 'price <= budget' in condition:
                if discount_price <= budget_amount:
                    return rule_score
            elif 'price <= budget * 1.1' in condition and 'price > budget' not in condition:
                if discount_price <= budget_amount * 1.1:
                    return rule_score
            elif 'price > budget * 1.1 && price <= budget * 1.3' in condition:
                if budget_amount * 1.1 < discount_price <= budget_amount * 1.3:
                    return rule_score
            elif 'price > budget * 1.3' in condition:
                if discount_price > budget_amount * 1.3:
                    return rule_score
        
        # 기본 점수 계산 (더 명확한 차별화)
        if discount_price <= budget_amount:
            return 15.0  # 예산 내: 높은 점수
        elif discount_price <= budget_amount * 1.1:
            return 8.0   # 예산 약간 초과: 중간 점수
        elif discount_price <= budget_amount * 1.3:
            return 2.0   # 예산 초과: 낮은 점수
        else:
            return -10.0  # 예산 크게 초과: 감점
    
    def _extract_capacity(self, spec: Dict) -> Optional[float]:
        """스펙에서 용량 추출"""
        if not spec:
            return None
        
        capacity_str = (
            get_spec_value(spec, "용량", "") or
            get_spec_value(spec, "총 용량", "") or
            get_spec_value(spec, "세탁 용량", "") or
            get_spec_value(spec, "냉장실 용량", "")
        )
        
        if not capacity_str:
            return None
        
        import re
        capacity_match = re.search(r'(\d+(?:\.\d+)?)', str(capacity_str).replace(',', ''))
        if capacity_match:
            return float(capacity_match.group(1))
        
        return None


# Singleton 인스턴스
playbook_scoring_model = PlaybookScoringModel()

