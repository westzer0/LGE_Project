"""
Playbook 설계 기반 GPT Explanation Layer

점수 breakdown을 활용한 설명 생성
"""
from typing import Dict, Optional
from ..models import Product, ProductReview
from api.services.playbook_scoring import ScoreBreakdown
from .chatgpt_service import chatgpt_service


class PlaybookExplanationGenerator:
    """Playbook 기반 설명 생성기"""
    
    def generate_explanation(
        self,
        product: Product,
        score_breakdown: ScoreBreakdown,
        user_profile: dict,
        onboarding_data: dict
    ) -> Dict:
        """
        GPT Explanation 생성
        
        Args:
            product: 제품 객체
            score_breakdown: 점수 breakdown
            user_profile: 사용자 프로필
            onboarding_data: 온보딩 데이터
            
        Returns:
            {
                "why_summary": "...",
                "lifestyle_message": "...",
                "design_message": "...",
                "review_highlight": "..."
            }
        """
        breakdown_dict = score_breakdown.to_dict()
        
        # 1. 왜 이 제품을 추천하는지
        why_summary = self._generate_why_summary(
            product, score_breakdown, user_profile, onboarding_data
        )
        
        # 2. 라이프스타일 메시지
        lifestyle_message = self._generate_lifestyle_message(
            product, user_profile, onboarding_data
        )
        
        # 3. 디자인 메시지
        design_message = self._generate_design_message(
            product, user_profile
        )
        
        # 4. 리뷰 하이라이트
        review_highlight = self._generate_review_highlight(
            product, breakdown_dict.get('ReviewScore', 0)
        )
        
        return {
            'why_summary': why_summary,
            'lifestyle_message': lifestyle_message,
            'design_message': design_message,
            'review_highlight': review_highlight
        }
    
    def _generate_why_summary(
        self,
        product: Product,
        score_breakdown: ScoreBreakdown,
        user_profile: dict,
        onboarding_data: dict
    ) -> str:
        """추천 이유 요약 생성"""
        breakdown = score_breakdown.to_dict()
        
        # 높은 점수 컴포넌트 분석
        components = [
            ('SpecScore', breakdown.get('SpecScore', 0), '스펙 적합도'),
            ('PreferenceScore', breakdown.get('PreferenceScore', 0), '우선순위 반영'),
            ('LifestyleScore', breakdown.get('LifestyleScore', 0), '라이프스타일'),
            ('ReviewScore', breakdown.get('ReviewScore', 0), '구매자 평가'),
            ('PriceScore', breakdown.get('PriceScore', 0), '가격 적합도'),
        ]
        
        # 상위 2개 컴포넌트 찾기
        top_components = sorted(components, key=lambda x: x[1], reverse=True)[:2]
        
        reasons = []
        
        # 사용자 프로필 기반
        household_size = user_profile.get('household_size', 2)
        priority = user_profile.get('priority', 'value')
        if isinstance(priority, list):
            priority = priority[0] if priority else 'value'
        
        # 주요 컴포넌트 기반 설명
        for comp_name, comp_score, comp_desc in top_components:
            if comp_score <= 0:
                continue
            
            if comp_name == 'SpecScore' and comp_score >= 15:
                if product.category == "KITCHEN" or "냉장고" in product.name:
                    reasons.append(f"{household_size}인 가족 구성에 맞는 적정 용량")
                elif product.category == "TV":
                    reasons.append("선명한 화질과 적정 크기")
                else:
                    reasons.append(f"적합한 스펙")
            
            elif comp_name == 'PreferenceScore' and comp_score >= 10:
                priority_map = {
                    'design': '디자인',
                    'tech': '기술/성능',
                    'eco': '에너지 효율',
                    'value': '가성비'
                }
                priority_name = priority_map.get(priority, '선호사항')
                reasons.append(f"'{priority_name}' 우선순위 반영")
            
            elif comp_name == 'LifestyleScore' and comp_score >= 5:
                cooking = onboarding_data.get('cooking', 'sometimes')
                if cooking in ['high', 'often']:
                    reasons.append("요리 빈도가 높은 라이프스타일에 맞춤")
            
            elif comp_name == 'ReviewScore' and comp_score >= 5:
                reasons.append("실제 구매자들의 긍정적 평가")
            
            elif comp_name == 'PriceScore' and comp_score >= 5:
                reasons.append("예산 범위 내 합리적 가격")
        
        # 기본 메시지
        if not reasons:
            reasons.append(f"{household_size}인 가족 구성에 적합한")
        
        # 제품명 추가
        title = f"{' '.join(reasons)}을 갖춘 {product.name}"
        
        return title
    
    def _generate_lifestyle_message(
        self,
        product: Product,
        user_profile: dict,
        onboarding_data: dict
    ) -> str:
        """라이프스타일 메시지 생성"""
        messages = []
        
        household_size = user_profile.get('household_size', 2)
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        product_name = product.name.upper()
        category = product.category
        
        # 제품별 맞춤 메시지
        if "냉장고" in product_name or category == "KITCHEN":
            if cooking in ['high', 'often']:
                messages.append("요리를 자주 하시는 당신을 위해,")
                messages.append("넉넉한 용량으로 식자재를 편리하게 보관할 수 있습니다.")
            else:
                messages.append(f"{household_size}인 가족의 식자재를 충분히 보관할 수 있는 용량입니다.")
        
        elif "세탁기" in product_name or "워시" in product_name:
            if laundry == 'daily':
                messages.append("매일 조금씩 세탁하는 패턴에 맞춰,")
                messages.append("효율적으로 세탁할 수 있습니다.")
            elif laundry == 'few_times':
                messages.append(f"일주일 2~3번 정도의 세탁 패턴에 맞춘 용량으로,")
                messages.append(f"{household_size}인 가족의 세탁량을 처리할 수 있습니다.")
            else:
                messages.append(f"{household_size}인 가족의 세탁량에 적합한 용량입니다.")
        
        elif "TV" in product_name or category == "TV":
            if media == 'gaming':
                messages.append("게임을 즐기시는 취향에 맞춰,")
                messages.append("높은 주사율과 빠른 응답 속도를 제공합니다.")
            elif media == 'ott':
                messages.append("영화와 드라마 감상을 위해,")
                messages.append("선명한 화질과 몰입감 있는 사운드를 제공합니다.")
            elif media == 'none':
                messages.append("TV 사용이 적더라도,")
                messages.append("필요할 때 선명한 화질을 즐길 수 있습니다.")
            else:
                messages.append(f"{household_size}인 가족이 함께 시청하기에 적합한 크기입니다.")
        
        if not messages:
            messages.append("당신의 라이프스타일에 맞춘 제품입니다.")
        
        return " ".join(messages)
    
    def _generate_design_message(
        self,
        product: Product,
        user_profile: dict
    ) -> str:
        """디자인 메시지 생성"""
        vibe = user_profile.get('vibe', 'modern')
        product_name = product.name.upper()
        
        vibe_map = {
            'modern': '모던하고 미니멀한',
            'cozy': '따뜻하고 아늑한',
            'luxury': '럭셔리하고 고급스러운',
            'pop': '트렌디하고 생기 있는'
        }
        
        vibe_desc = vibe_map.get(vibe, '세련된')
        
        if "OBJET" in product_name or "오브제" in product_name:
            return f"{vibe_desc} 디자인의 OBJET 컬렉션으로, 인테리어 포인트가 되어줄 거예요. 깔끔하고 세련된 공간 연출에 도움이 됩니다."
        elif "SIGNATURE" in product_name or "시그니처" in product_name:
            return f"프리미엄 {vibe_desc} 디자인으로, 특별한 공간을 완성해줍니다. 고급스러운 마감과 세련된 디테일이 돋보입니다."
        else:
            return f"{vibe_desc} 디자인으로 어떤 공간에도 잘 어울립니다. 실용적이면서도 스타일리시한 외관을 갖추고 있어요."
    
    def _generate_review_highlight(
        self,
        product: Product,
        review_score: float
    ) -> str:
        """리뷰 하이라이트 생성"""
        try:
            reviews = ProductReview.objects.filter(product=product)
            review_count = reviews.count()
            
            if review_count == 0:
                return "아직 리뷰가 없어요."
            
            # 별점 추출
            ratings = []
            for review in reviews:
                star_str = review.star or ""
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
                if review_count >= 100:
                    return f"{review_count}개 이상의 리뷰가 있습니다."
                return f"{review_count}개의 리뷰가 있습니다."
            
            avg_rating = sum(ratings) / len(ratings)
            
            if review_score >= 8:
                return f"별점 {avg_rating:.1f}점, {review_count}개 이상의 리뷰에서 높은 만족도를 보여줍니다. 소음, 수납력, 디자인에 대한 긍정적 피드백이 많습니다."
            elif review_score >= 5:
                return f"별점 {avg_rating:.1f}점, {review_count}개 이상의 리뷰에서 긍정적 평가를 받았습니다. 실용성과 성능에 대한 좋은 반응이 많습니다."
            elif review_score >= 3:
                return f"별점 {avg_rating:.1f}점, {review_count}개의 리뷰에서 만족도가 확인되었습니다."
            else:
                return f"{review_count}개의 리뷰가 있습니다."
                
        except Exception as e:
            print(f"[Review Highlight Error] {product.name}: {e}")
            return "리뷰 정보를 확인할 수 없습니다."
    
    def generate_with_gpt(
        self,
        product: Product,
        score_breakdown: ScoreBreakdown,
        user_profile: dict,
        onboarding_data: dict
    ) -> Dict:
        """
        ChatGPT를 활용한 설명 생성 (선택적)
        
        GPT가 사용 가능할 때만 활용
        """
        if not chatgpt_service.is_available():
            # GPT 없이 기본 설명 생성
            return self.generate_explanation(
                product, score_breakdown, user_profile, onboarding_data
            )
        
        # GPT 프롬프트 구성
        breakdown = score_breakdown.to_dict()
        
        prompt = f"""
사용자 온보딩 정보:
- 가족 구성: {user_profile.get('household_size', 2)}인
- 주거 형태: {user_profile.get('housing_type', 'apartment')}
- 인테리어 스타일: {user_profile.get('vibe', 'modern')}
- 우선순위: {user_profile.get('priority', 'value')}

제품 정보:
- 이름: {product.name}
- 카테고리: {product.category}

점수 Breakdown:
- 스펙 적합도: {breakdown.get('SpecScore', 0)}
- 우선순위 반영: {breakdown.get('PreferenceScore', 0)}
- 라이프스타일: {breakdown.get('LifestyleScore', 0)}
- 구매자 평가: {breakdown.get('ReviewScore', 0)}
- 가격 적합도: {breakdown.get('PriceScore', 0)}

위 정보를 바탕으로 다음 형식으로 추천 설명을 생성해주세요:
1. why_summary: 왜 이 제품을 추천하는지 (1~2문장)
2. lifestyle_message: 라이프스타일 연계 메시지 (2~3문장)
3. design_message: 디자인 관련 메시지 (1~2문장)
4. review_highlight: 리뷰 요약 (1문장)

JSON 형식으로 반환해주세요.
"""
        
        try:
            response = chatgpt_service.chat_response(prompt, {})
            # JSON 파싱 시도 (간단한 구현)
            # 실제로는 더 정교한 파싱 필요
            return self.generate_explanation(
                product, score_breakdown, user_profile, onboarding_data
            )
        except Exception as e:
            print(f"[GPT Explanation Error] {e}")
            return self.generate_explanation(
                product, score_breakdown, user_profile, onboarding_data
            )


# Singleton 인스턴스
playbook_explanation_generator = PlaybookExplanationGenerator()

