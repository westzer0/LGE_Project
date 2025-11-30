"""
ChatGPT API 연동 서비스
- 추천 이유 자동 생성
- 스타일 메시지 생성
- 리뷰 요약
"""
import json
from django.conf import settings

try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ OpenAI 초기화 실패: {e}")
    client = None
    OPENAI_AVAILABLE = False


class ChatGPTService:
    """ChatGPT API 서비스"""
    
    MODEL = "gpt-4o-mini"  # 비용 효율적인 모델
    
    @classmethod
    def is_available(cls):
        return OPENAI_AVAILABLE and client is not None
    
    @classmethod
    def generate_recommendation_reason(cls, product_info: dict, user_profile: dict) -> str:
        """
        제품 추천 이유 생성
        
        Args:
            product_info: 제품 정보 (name, category, specs 등)
            user_profile: 사용자 프로필 (household_size, style, budget 등)
        
        Returns:
            추천 이유 문자열
        """
        if not cls.is_available():
            return cls._fallback_recommendation_reason(product_info, user_profile)
        
        try:
            prompt = f"""
당신은 LG전자 가전 전문가입니다. 사용자에게 맞춤 추천 이유를 친근하게 설명해주세요.

## 사용자 정보
- 가족 구성: {user_profile.get('household_size', 2)}인 가구
- 주거 형태: {user_profile.get('housing_type', '아파트')}
- 평수: {user_profile.get('pyung', 25)}평
- 스타일 선호: {user_profile.get('style', '모던')}
- 예산: {user_profile.get('budget', '표준형')}
- 우선순위: {user_profile.get('priority', '가성비')}

## 추천 제품
- 제품명: {product_info.get('name', '')}
- 카테고리: {product_info.get('category', '')}
- 주요 스펙: {product_info.get('specs', '')}

## 요청사항
1. 왜 이 제품이 사용자에게 적합한지 2-3문장으로 설명
2. 친근하고 따뜻한 말투 사용
3. 구체적인 수치나 기능 언급
4. 이모지 사용 금지
5. 한국어로 작성
"""
            
            response = client.chat.completions.create(
                model=cls.MODEL,
                messages=[
                    {"role": "system", "content": "당신은 LG전자 가전 전문 컨설턴트입니다. 친근하고 전문적인 톤으로 답변합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"ChatGPT 추천 이유 생성 오류: {e}")
            return cls._fallback_recommendation_reason(product_info, user_profile)
    
    @classmethod
    def _fallback_recommendation_reason(cls, product_info: dict, user_profile: dict) -> str:
        """ChatGPT 실패 시 기본 추천 이유"""
        household = user_profile.get('household_size', 2)
        category = product_info.get('category', '가전')
        
        reasons = {
            'refrigerator': f"{household}인 가족에게 딱 맞는 용량이에요. 넉넉한 수납공간으로 식재료 관리가 편해져요.",
            'washer': f"세탁 빈도를 고려한 최적의 용량이에요. AI가 최적의 세탁 코스를 자동 선택해줘요.",
            'tv': f"거실 크기에 최적화된 화면 사이즈예요. 선명한 화질로 몰입감 있는 시청이 가능해요.",
            'air': f"평수에 맞는 냉방 용량으로 효율적인 온도 관리가 가능해요.",
        }
        
        return reasons.get(category.lower(), "사용자 조건에 맞춰 선정된 추천 제품이에요.")
    
    @classmethod
    def generate_style_message(cls, user_profile: dict) -> dict:
        """
        스타일 분석 메시지 생성 (타이틀 + 서브타이틀)
        
        Args:
            user_profile: 사용자 프로필
        
        Returns:
            {"title": "...", "subtitle": "..."}
        """
        if not cls.is_available():
            return cls._fallback_style_message(user_profile)
        
        try:
            prompt = f"""
당신은 LG전자 홈스타일링 전문가입니다. 사용자 프로필을 분석하여 스타일 메시지를 만들어주세요.

## 사용자 정보
- 가족 구성: {user_profile.get('household_size', 2)}인 가구
- 주거 형태: {user_profile.get('housing_type', '아파트')}
- 평수: {user_profile.get('pyung', 25)}평
- 스타일 선호: {user_profile.get('style', 'modern')}
- 예산: {user_profile.get('budget', 'standard')}
- 요리 빈도: {user_profile.get('cooking', 'sometimes')}
- 반려동물: {user_profile.get('pet', 'no')}

## 요청사항
JSON 형식으로 응답해주세요:
{{
    "title": "스타일 타이틀 (15자 이내, 예: '모던 & 미니멀 라이프를 위한 오브제 스타일')",
    "subtitle": "스타일 설명 (50자 이내, 사용자 특성 반영)"
}}

타이틀 예시:
- "모던 & 미니멀 라이프를 위한 오브제 스타일"
- "따뜻하고 자연스러운 코지 패밀리 스타일"
- "나만의 컬러 플레이, 유니크 MoodUP 스타일"

서브타이틀은 사용자의 구체적인 조건을 반영해서 작성해주세요.
"""
            
            response = client.chat.completions.create(
                model=cls.MODEL,
                messages=[
                    {"role": "system", "content": "당신은 인테리어 스타일 전문가입니다. JSON 형식으로만 응답합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "title": result.get("title", "나에게 딱 맞는 스타일"),
                "subtitle": result.get("subtitle", "당신의 라이프스타일에 맞춰 구성했어요.")
            }
        
        except Exception as e:
            print(f"ChatGPT 스타일 메시지 생성 오류: {e}")
            return cls._fallback_style_message(user_profile)
    
    @classmethod
    def _fallback_style_message(cls, user_profile: dict) -> dict:
        """ChatGPT 실패 시 기본 스타일 메시지"""
        style = user_profile.get('style', 'modern')
        
        messages = {
            'modern': {
                "title": "모던 & 미니멀 라이프를 위한 오브제 스타일",
                "subtitle": "깔끔하고 세련된 공간에 어울리는 화이트 톤 중심 구성이에요."
            },
            'cozy': {
                "title": "따뜻하고 자연스러운 코지 패밀리 스타일",
                "subtitle": "Nature Beige 톤으로 포근한 분위기를 완성해요."
            },
            'natural': {
                "title": "자연을 닮은 내추럴 라이프스타일",
                "subtitle": "편안하고 자연스러운 무드의 가전 조합이에요."
            },
            'luxury': {
                "title": "프리미엄 감성의 럭셔리 스타일",
                "subtitle": "고급스러운 스테인리스 & 글라스 라인업 중심이에요."
            }
        }
        
        return messages.get(style, messages['modern'])
    
    @classmethod
    def summarize_reviews(cls, reviews: list, product_name: str = "") -> str:
        """
        리뷰 요약
        
        Args:
            reviews: 리뷰 텍스트 리스트
            product_name: 제품명
        
        Returns:
            요약된 리뷰 문자열
        """
        if not cls.is_available() or not reviews:
            return "다양한 고객들이 만족하며 사용 중인 제품이에요."
        
        try:
            # 최대 20개 리뷰만 사용 (토큰 제한)
            sample_reviews = reviews[:20]
            reviews_text = "\n".join([f"- {r}" for r in sample_reviews])
            
            prompt = f"""
다음은 "{product_name}" 제품의 고객 리뷰입니다. 핵심 내용을 3줄로 요약해주세요.

## 리뷰
{reviews_text}

## 요청사항
1. 장점 위주로 요약
2. 구체적인 기능이나 특징 언급
3. 친근한 말투로 작성
4. 이모지 사용 금지
5. 각 줄은 한 문장으로
"""
            
            response = client.chat.completions.create(
                model=cls.MODEL,
                messages=[
                    {"role": "system", "content": "당신은 제품 리뷰 분석 전문가입니다. 핵심만 간결하게 요약합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"ChatGPT 리뷰 요약 오류: {e}")
            return "다양한 고객들이 만족하며 사용 중인 제품이에요."
    
    @classmethod
    def chat_response(cls, user_message: str, context: dict = None) -> str:
        """
        AI 상담 챗봇 응답
        
        Args:
            user_message: 사용자 메시지
            context: 대화 컨텍스트 (선택)
        
        Returns:
            AI 응답 문자열
        """
        if not cls.is_available():
            return "죄송해요, 현재 AI 상담 서비스를 이용할 수 없어요. 잠시 후 다시 시도해주세요."
        
        try:
            system_prompt = """
당신은 LG전자 가전 전문 상담사 'LG 홈스타일링 AI'입니다.

역할:
- 가전 제품 추천 및 상담
- 제품 스펙, 기능 설명
- 설치 및 사용 관련 안내

톤앤매너:
- 친근하고 따뜻한 말투
- 전문적이면서도 이해하기 쉽게
- 이모지 적절히 사용 (1-2개)
- 한국어로 답변

제한사항:
- 가전 관련 질문에만 답변
- 가격 정보는 정확하지 않을 수 있다고 안내
- 구매는 LG전자 공식 사이트 안내
"""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # 컨텍스트가 있으면 추가
            if context and context.get('history'):
                for msg in context['history'][-5:]:  # 최근 5개 대화만
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=cls.MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"ChatGPT 챗봇 오류: {e}")
            return "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요."


# 싱글톤 인스턴스
chatgpt_service = ChatGPTService()

