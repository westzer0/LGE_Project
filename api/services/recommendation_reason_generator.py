"""
추천 문구 생성 서비스

구매리뷰 분석 + 고객 취향 데이터 → 제품을 고객에게 추천하는 이유를 한 줄로 설명
"""
import re
from typing import Dict, List, Optional
from collections import Counter
from ..models import Product, ProductReview, ProductRecommendReason


class RecommendationReasonGenerator:
    """추천 문구 생성기"""
    
    def __init__(self):
        # 취향별 키워드 매핑
        self.taste_keywords = {
            'modern': ['모던', '미니멀', '깔끔', '심플', '세련'],
            'cozy': ['코지', '따뜻', '포근', '아늑', '편안'],
            'luxury': ['럭셔리', '프리미엄', '고급', '하이엔드', '시그니처'],
            'unique': ['유니크', '개성', '특별', '독특', '오브제'],
        }
        
        # 우선순위별 키워드
        self.priority_keywords = {
            'design': ['디자인', '외관', '스타일', '예쁘', '이쁘', '예쁜', '이쁜', '멋', '세련'],
            'tech': ['기능', '성능', '사양', '스마트', 'AI', '편리', '편리함'],
            'eco': ['에너지', '전력', '효율', '절약', '친환경'],
            'value': ['가격', '가성비', '저렴', '합리', '실용'],
        }
    
    def generate_reason(
        self,
        product: Product,
        user_profile: dict,
        taste_info: Optional[Dict] = None,
        score: float = 0.0
    ) -> str:
        """
        추천 문구 생성
        
        Args:
            product: 추천 제품
            user_profile: 사용자 프로필
            taste_info: 취향 정보 (CSV에서 가져온 정보)
            score: 추천 점수
        
        Returns:
            추천 문구 (한 줄)
        """
        # 1순위: CSV의 리뷰_기반_추천문구 활용 (taste_info가 있는 경우)
        if taste_info and taste_info.get('리뷰_기반_추천문구'):
            base_reason = taste_info['리뷰_기반_추천문구']
            # 개인화 처리
            personalized = self._personalize_reason(base_reason, user_profile, product)
            if personalized:
                return personalized
        
        # 2순위: DB에 저장된 추천 이유 활용
        if hasattr(product, 'recommend_reason') and product.recommend_reason:
            db_reason = product.recommend_reason.reason_text
            if db_reason:
                personalized = self._personalize_reason(db_reason, user_profile, product)
                if personalized:
                    return personalized
        
        # 3순위: 리뷰 분석 기반 생성
        review_based = self._generate_from_reviews(product, user_profile, taste_info)
        if review_based:
            return review_based
        
        # 4순위: 기본 문구 (점수 기반)
        return self._generate_default_reason(product, user_profile, score)
    
    def _personalize_reason(
        self,
        base_reason: str,
        user_profile: dict,
        product: Product
    ) -> str:
        """기존 추천 문구를 사용자 취향에 맞게 개인화"""
        # 취향 정보 추출
        vibe = user_profile.get('vibe', '').lower()
        priority = user_profile.get('priority', '').lower()
        household_size = user_profile.get('household_size', 2)
        budget = user_profile.get('budget_level', 'medium')
        
        # 개인화 요소 추가
        personalization = []
        
        # 가족 구성원 정보
        if household_size == 1:
            personalization.append("1인 가구에 적합한")
        elif household_size >= 4:
            personalization.append(f"{household_size}인 가족에 적합한")
        
        # 우선순위 정보
        if priority == 'design' and '디자인' not in base_reason:
            personalization.append("디자인을 중시하는")
        elif priority == 'tech' and '기능' not in base_reason:
            personalization.append("기능을 중시하는")
        elif priority == 'eco' and '에너지' not in base_reason:
            personalization.append("에너지 효율을 중시하는")
        elif priority == 'value' and '가성비' not in base_reason:
            personalization.append("가성비를 중시하는")
        
        # 개인화 요소가 있으면 추가
        if personalization:
            prefix = " ".join(personalization) + " 당신을 위해, "
            # 기존 문구가 너무 길면 요약
            if len(base_reason) > 100:
                base_reason = base_reason[:80] + "..."
            return prefix + base_reason
        
        return base_reason
    
    def _generate_from_reviews(
        self,
        product: Product,
        user_profile: dict,
        taste_info: Optional[Dict] = None
    ) -> str:
        """리뷰 분석 기반 추천 문구 생성"""
        # 제품 리뷰 가져오기
        reviews = ProductReview.objects.filter(product=product)[:20]
        if not reviews:
            return None
        
        # 리뷰 텍스트 수집
        review_texts = [r.review_text for r in reviews if r.review_text]
        if not review_texts:
            return None
        
        # 취향 키워드 추출
        target_keywords = self._extract_taste_keywords(user_profile, taste_info)
        
        # 리뷰에서 취향과 관련된 키워드 찾기
        matched_keywords = self._find_matching_keywords(review_texts, target_keywords)
        
        # 리뷰에서 자주 언급되는 긍정 키워드 추출
        positive_keywords = self._extract_positive_keywords(review_texts)
        
        # 추천 문구 생성
        reason_parts = []
        
        # 취향 매칭 키워드가 있으면 사용
        if matched_keywords:
            top_keyword = matched_keywords[0][0]
            count = matched_keywords[0][1]
            reason_parts.append(f"리뷰에서 '{top_keyword}'에 대한 긍정적 피드백이 {count}회 이상 나타났습니다.")
        
        # 긍정 키워드 활용
        if positive_keywords and not reason_parts:
            top_positive = positive_keywords[0][0]
            reason_parts.append(f"많은 사용자들이 '{top_positive}'를 칭찬했습니다.")
        
        # 기본 문구
        if not reason_parts:
            reason_parts.append("실제 구매자들의 긍정적 리뷰가 많은 제품입니다.")
        
        # 사용자 맞춤 정보 추가
        household_size = user_profile.get('household_size', 2)
        if household_size == 1:
            reason_parts.append("1인 가구에 적합합니다.")
        elif household_size >= 4:
            reason_parts.append(f"{household_size}인 가족 구성에 적합합니다.")
        
        return " ".join(reason_parts)
    
    def _extract_taste_keywords(
        self,
        user_profile: dict,
        taste_info: Optional[Dict] = None
    ) -> List[str]:
        """취향 정보에서 키워드 추출"""
        keywords = []
        
        # Vibe 키워드
        vibe = user_profile.get('vibe', '').lower()
        if vibe in self.taste_keywords:
            keywords.extend(self.taste_keywords[vibe])
        
        # 우선순위 키워드
        priority = user_profile.get('priority', '').lower()
        if priority in self.priority_keywords:
            keywords.extend(self.priority_keywords[priority])
        
        # CSV 취향 정보에서 키워드 추출
        if taste_info:
            interior = taste_info.get('인테리어_스타일', '')
            priority_text = taste_info.get('우선순위', '')
            
            # 인테리어 스타일에서 키워드 추출
            for vibe_key, vibe_words in self.taste_keywords.items():
                if any(word in interior for word in vibe_words):
                    keywords.extend(vibe_words)
            
            # 우선순위에서 키워드 추출
            for prio_key, prio_words in self.priority_keywords.items():
                if any(word in priority_text for word in prio_words):
                    keywords.extend(prio_words)
        
        return list(set(keywords))  # 중복 제거
    
    def _find_matching_keywords(
        self,
        review_texts: List[str],
        target_keywords: List[str]
    ) -> List[tuple]:
        """리뷰에서 취향 키워드와 매칭되는 키워드 찾기"""
        matches = Counter()
        
        for review in review_texts:
            review_lower = review.lower()
            for keyword in target_keywords:
                if keyword in review_lower:
                    matches[keyword] += 1
        
        # 빈도순으로 정렬
        return matches.most_common(3)
    
    def _extract_positive_keywords(self, review_texts: List[str]) -> List[tuple]:
        """리뷰에서 긍정 키워드 추출"""
        positive_words = [
            '좋', '만족', '추천', '훌륭', '최고', '완벽', '뛰어', '우수',
            '편리', '깔끔', '예쁘', '이쁘', '멋', '세련', '실용', '가성비'
        ]
        
        matches = Counter()
        for review in review_texts:
            review_lower = review.lower()
            for word in positive_words:
                if word in review_lower:
                    matches[word] += 1
        
        return matches.most_common(3)
    
    def _generate_default_reason(
        self,
        product: Product,
        user_profile: dict,
        score: float
    ) -> str:
        """기본 추천 문구 생성 (점수 기반)"""
        priority = user_profile.get('priority', 'value')
        priority_labels = {
            'design': '디자인',
            'tech': '기술 사양',
            'eco': '에너지 효율',
            'value': '가성비',
        }
        
        if score >= 0.8:
            return f"당신의 선호도({priority_labels.get(priority, '개인맞춤')})에 가장 잘 맞는 제품입니다."
        elif score >= 0.6:
            return "우수한 성능과 가성비를 갖춘 제품입니다."
        else:
            return "조건에 맞는 추천 제품입니다."


# Singleton 인스턴스
reason_generator = RecommendationReasonGenerator()

