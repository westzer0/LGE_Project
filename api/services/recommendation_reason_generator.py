"""
추천 문구 생성 서비스

구매리뷰 분석 + 고객 취향 데이터 → 제품을 고객에게 추천하는 이유를 한 줄로 설명
"""
import re
from typing import Dict, List, Optional
from collections import Counter
from functools import lru_cache
from ..models import Product, ProductReview, ProductRecommendReason


class RecommendationReasonGenerator:
    """추천 문구 생성기"""
    
    def __init__(self):
        # 리뷰 캐시 (제품 ID -> 리뷰 텍스트 리스트)
        self._reviews_cache = {}
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
        
        # 취향 조합별 1:1 매칭 템플릿
        # 키: (vibe, priority, household_size_category) 튜플
        # 값: 추천 이유 템플릿 리스트
        self.taste_reason_templates = self._build_taste_templates()
    
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
        # 0순위: 취향 조합별 1:1 템플릿 매칭 (가장 정확한 매칭)
        template_reason = self._get_taste_template_reason(user_profile, product)
        if template_reason:
            return template_reason
        
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
        priority_raw = user_profile.get('priority', '')
        if isinstance(priority_raw, list):
            priority = ', '.join(priority_raw).lower() if priority_raw else ''
        else:
            priority = str(priority_raw).lower() if priority_raw else ''
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
        """리뷰 분석 기반 추천 문구 생성 (캐싱 적용)"""
        # 제품 리뷰 가져오기 (캐싱 적용)
        review_texts = self._get_cached_reviews(product.id)
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
        priority_raw = user_profile.get('priority', '')
        if isinstance(priority_raw, list):
            priority = ', '.join(priority_raw).lower() if priority_raw else ''
        else:
            priority = str(priority_raw).lower() if priority_raw else ''
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
    
    def _get_cached_reviews(self, product_id: int) -> List[str]:
        """제품 리뷰를 캐시에서 가져오기"""
        if product_id not in self._reviews_cache:
            reviews = ProductReview.objects.filter(product_id=product_id)[:20]
            review_texts = [r.review_text for r in reviews if r.review_text]
            self._reviews_cache[product_id] = review_texts
        return self._reviews_cache[product_id]
    
    def clear_cache(self):
        """캐시 초기화"""
        self._reviews_cache.clear()
    
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
    
    def _build_taste_templates(self) -> Dict:
        """
        취향 조합별 1:1 매칭 템플릿 구축
        
        Returns:
            {(vibe, priority, household_category): [템플릿 리스트]} 딕셔너리
        """
        import random
        
        templates = {
            # Modern + Tech 조합
            ('modern', 'tech', 'single'): [
                "1인 가구를 위한 미니멀한 디자인과 최신 기술이 결합된 제품이에요. 깔끔한 공간에 어울리는 컴팩트한 사이즈와 뛰어난 성능을 갖췄어요.",
                "혼자 사는 공간에 딱 맞는 세련된 디자인과 스마트 기능을 갖춘 제품이에요. 공간 활용도 높고 사용하기 편리해요.",
            ],
            ('modern', 'tech', 'couple'): [
                "2인 가구를 위한 모던한 디자인과 최신 기술이 만난 제품이에요. 깔끔한 인테리어와 뛰어난 기능성으로 일상이 더 편리해져요.",
                "신혼부부에게 적합한 세련된 디자인과 스마트 기능을 갖춘 제품이에요. 공간을 효율적으로 활용할 수 있어요.",
            ],
            ('modern', 'tech', 'family'): [
                "가족을 위한 모던한 디자인과 최신 기술이 결합된 제품이에요. 넉넉한 용량과 뛰어난 성능으로 가족 모두가 만족할 거예요.",
                "4인 이상 가족에게 적합한 세련된 디자인과 스마트 기능을 갖춘 제품이에요. 대용량이면서도 공간을 효율적으로 활용해요.",
            ],
            
            # Modern + Design 조합
            ('modern', 'design', 'single'): [
                "1인 가구를 위한 미니멀하고 세련된 디자인이 돋보이는 제품이에요. 깔끔한 공간에 완벽하게 어울려요.",
                "혼자 사는 공간에 딱 맞는 모던한 디자인의 제품이에요. 인테리어 포인트가 되어줄 거예요.",
            ],
            ('modern', 'design', 'couple'): [
                "2인 가구를 위한 모던하고 세련된 디자인이 매력적인 제품이에요. 깔끔한 인테리어와 완벽하게 조화를 이뤄요.",
                "신혼부부에게 적합한 미니멀한 디자인의 제품이에요. 세련된 공간 연출에 도움이 될 거예요.",
            ],
            ('modern', 'design', 'family'): [
                "가족을 위한 모던하고 세련된 디자인이 돋보이는 제품이에요. 넉넉한 용량과 아름다운 외관을 동시에 갖췄어요.",
                "4인 이상 가족에게 적합한 세련된 디자인의 제품이에요. 대용량이면서도 공간을 아름답게 연출해요.",
            ],
            
            # Cozy + Value 조합
            ('cozy', 'value', 'single'): [
                "1인 가구를 위한 따뜻한 분위기와 합리적인 가격이 매력적인 제품이에요. 혼자 사는 공간에 포근함을 더해줘요.",
                "혼자 사는 공간에 어울리는 아늑한 디자인과 가성비 좋은 제품이에요. 실용적이면서도 따뜻한 느낌을 줘요.",
            ],
            ('cozy', 'value', 'couple'): [
                "2인 가구를 위한 따뜻하고 포근한 분위기와 합리적인 가격이 매력적인 제품이에요. 신혼부부에게 딱 맞아요.",
                "신혼부부에게 적합한 아늑한 디자인과 가성비 좋은 제품이에요. 따뜻한 분위기의 집을 완성해줘요.",
            ],
            ('cozy', 'value', 'family'): [
                "4인 이상 가족을 위한 따뜻한 분위기와 넉넉한 용량, 합리적인 가격이 매력적인 제품이에요. 가족 모두가 만족할 거예요.",
                "가족을 위한 아늑한 디자인과 대용량, 가성비 좋은 제품이에요. 따뜻한 분위기의 집을 완성해줘요.",
            ],
            
            # Cozy + Eco 조합
            ('cozy', 'eco', 'single'): [
                "1인 가구를 위한 따뜻한 분위기와 에너지 효율이 뛰어난 제품이에요. 전기요금 절약에도 도움이 돼요.",
                "혼자 사는 공간에 어울리는 아늑한 디자인과 친환경 기능을 갖춘 제품이에요. 환경도 생각하고 전기요금도 절약해요.",
            ],
            ('cozy', 'eco', 'couple'): [
                "2인 가구를 위한 따뜻하고 포근한 분위기와 에너지 효율이 뛰어난 제품이에요. 친환경 라이프스타일에 딱 맞아요.",
                "신혼부부에게 적합한 아늑한 디자인과 친환경 기능을 갖춘 제품이에요. 환경을 생각하는 따뜻한 집을 완성해줘요.",
            ],
            ('cozy', 'eco', 'family'): [
                "4인 이상 가족을 위한 따뜻한 분위기와 넉넉한 용량, 뛰어난 에너지 효율이 매력적인 제품이에요. 가족 모두가 만족하고 전기요금도 절약해요.",
                "가족을 위한 아늑한 디자인과 대용량, 친환경 기능을 갖춘 제품이에요. 환경을 생각하는 따뜻한 집을 완성해줘요.",
            ],
            
            # Luxury + Design 조합
            ('luxury', 'design', 'single'): [
                "1인 가구를 위한 프리미엄 디자인과 고급스러운 마감이 돋보이는 제품이에요. 혼자 사는 공간을 더욱 특별하게 만들어줘요.",
                "혼자 사는 공간에 어울리는 럭셔리한 디자인의 제품이에요. 고급스러운 인테리어 포인트가 되어줄 거예요.",
            ],
            ('luxury', 'design', 'couple'): [
                "2인 가구를 위한 프리미엄 디자인과 고급스러운 마감이 매력적인 제품이에요. 신혼부부의 특별한 공간을 완성해줘요.",
                "신혼부부에게 적합한 럭셔리한 디자인의 제품이에요. 고급스러운 인테리어 연출에 도움이 될 거예요.",
            ],
            ('luxury', 'design', 'family'): [
                "4인 이상 가족을 위한 프리미엄 디자인과 넉넉한 용량, 고급스러운 마감이 매력적인 제품이에요. 가족 모두가 만족할 거예요.",
                "가족을 위한 럭셔리한 디자인과 대용량을 갖춘 제품이에요. 고급스러운 공간 연출에 도움이 될 거예요.",
            ],
            
            # Unique + Tech 조합
            ('unique', 'tech', 'single'): [
                "1인 가구를 위한 독특하고 개성 있는 디자인과 최신 기술이 결합된 제품이에요. 나만의 특별한 공간을 완성해줘요.",
                "혼자 사는 공간에 어울리는 유니크한 디자인과 스마트 기능을 갖춘 제품이에요. 개성을 살린 인테리어에 딱 맞아요.",
            ],
            ('unique', 'tech', 'couple'): [
                "2인 가구를 위한 독특하고 개성 있는 디자인과 최신 기술이 만난 제품이에요. 신혼부부의 특별한 공간을 완성해줘요.",
                "신혼부부에게 적합한 유니크한 디자인과 스마트 기능을 갖춘 제품이에요. 개성을 살린 인테리어 연출에 도움이 될 거예요.",
            ],
            ('unique', 'tech', 'family'): [
                "4인 이상 가족을 위한 독특하고 개성 있는 디자인과 넉넉한 용량, 최신 기술이 결합된 제품이에요. 가족 모두가 만족할 거예요.",
                "가족을 위한 유니크한 디자인과 대용량, 스마트 기능을 갖춘 제품이에요. 개성을 살린 인테리어 연출에 도움이 될 거예요.",
            ],
        }
        
        return templates
    
    def _get_household_category(self, household_size: int) -> str:
        """가족 구성원 수를 카테고리로 변환"""
        if household_size == 1:
            return 'single'
        elif household_size == 2:
            return 'couple'
        else:
            return 'family'
    
    def _get_taste_template_reason(
        self,
        user_profile: dict,
        product: Product
    ) -> Optional[str]:
        """
        취향 조합별 템플릿에서 추천 이유 가져오기 (1:1 매칭)
        
        Returns:
            매칭된 추천 이유 문자열, 없으면 None
        """
        import random
        
        vibe = user_profile.get('vibe', '').lower()
        priority_raw = user_profile.get('priority', '')
        if isinstance(priority_raw, list):
            priority = ', '.join(priority_raw).lower() if priority_raw else ''
        else:
            priority = str(priority_raw).lower() if priority_raw else ''
        household_size = user_profile.get('household_size', 2)
        household_category = self._get_household_category(household_size)
        
        # 정확한 매칭 시도
        key = (vibe, priority, household_category)
        if key in self.taste_reason_templates:
            templates = self.taste_reason_templates[key]
            # 제품 카테고리에 맞게 템플릿 선택
            selected = random.choice(templates)
            # 제품 정보로 개인화
            return self._customize_template(selected, user_profile, product)
        
        # 부분 매칭 시도 (vibe만 매칭)
        for (v, p, h), templates in self.taste_reason_templates.items():
            if v == vibe and h == household_category:
                selected = random.choice(templates)
                return self._customize_template(selected, user_profile, product)
        
        # 기본 매칭 시도 (household만 매칭)
        for (v, p, h), templates in self.taste_reason_templates.items():
            if h == household_category:
                selected = random.choice(templates)
                return self._customize_template(selected, user_profile, product)
        
        return None
    
    def _customize_template(
        self,
        template: str,
        user_profile: dict,
        product: Product
    ) -> str:
        """템플릿을 사용자 프로필과 제품 정보로 개인화"""
        household_size = user_profile.get('household_size', 2)
        category = product.category if hasattr(product, 'category') else ''
        product_name = product.name if hasattr(product, 'name') else ''
        
        # 가족 구성원 수로 치환
        template = template.replace('{household_size}', str(household_size))
        
        # 제품 이름에서 카테고리 파악 (category 필드가 없거나 부정확한 경우 대비)
        if '냉장고' in product_name or '디오스' in product_name:
            category = 'KITCHEN'
            product_type = '냉장고'
        elif '오븐' in product_name or '광파' in product_name:
            category = 'KITCHEN'
            product_type = '오븐'
        elif '식기세척기' in product_name or '세척기' in product_name:
            category = 'KITCHEN'
            product_type = '식기세척기'
        elif 'TV' in product_name or '티비' in product_name:
            category = 'TV'
            product_type = 'TV'
        else:
            product_type = '제품'
        
        # 카테고리별 특화 문구로 템플릿 수정
        if category == 'TV':
            template = template.replace('제품', 'TV').replace('용량', '화질').replace('넉넉한', '선명한')
            template += " 선명한 화질로 몰입감 있는 시청이 가능해요."
        elif category == 'KITCHEN':
            # 제품 타입별로 다른 문구
            if product_type == '냉장고':
                template = template.replace('제품', '냉장고')
                if '용량' not in template:
                    template = template.replace('넉넉한', '넉넉한 용량의')
                template += " 넉넉한 수납 공간으로 가족의 식재료를 충분히 보관할 수 있어요."
            elif product_type == '오븐':
                template = template.replace('제품', '오븐').replace('냉장고', '오븐')
                template += " 다양한 요리를 쉽고 빠르게 만들 수 있어요."
            elif product_type == '식기세척기':
                template = template.replace('제품', '식기세척기').replace('냉장고', '식기세척기')
                template += " 설거지 없이 깨끗하게 식기를 세척해줘요."
            else:
                template += " 주방 공간을 효율적으로 활용할 수 있어요."
        elif category == 'LIVING':
            template = template.replace('제품', '생활가전')
            template += " 생활을 더욱 편리하게 만들어줘요."
        
        return template


# Singleton 인스턴스
reason_generator = RecommendationReasonGenerator()

