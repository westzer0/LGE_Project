"""
고급 AI 추천 서비스 (자연어 대화 기반)
"""
import json
from .chatgpt_service import chatgpt_service
from .recommendation_engine import recommendation_engine


class AIRecommendationService:
    """자연어 대화 기반 AI 추천 서비스"""
    
    @classmethod
    def recommend_from_conversation(cls, user_message: str, conversation_history: list = None):
        """
        자연어 대화를 통한 제품 추천
        
        Args:
            user_message: 사용자 메시지 (예: "2인 가구, 작은 주방, 예산 200만원")
            conversation_history: 이전 대화 기록 (선택)
            
        Returns:
            추천 결과 딕셔너리
        """
        if not chatgpt_service.is_available():
            return {
                'success': False,
                'error': 'OpenAI API를 사용할 수 없습니다.'
            }
        
        # 대화 맥락 구성
        context = ""
        if conversation_history:
            context = "\n".join([f"사용자: {h.get('user', '')}\nAI: {h.get('assistant', '')}" 
                               for h in conversation_history[-3:]])  # 최근 3개만
        
        # 추천 정보 추출을 위한 프롬프트
        prompt = f"""당신은 LG전자 가전 추천 전문가입니다. 사용자의 자연어 요청을 분석하여 제품 추천에 필요한 정보를 추출해주세요.

## 이전 대화 맥락
{context if context else "없음"}

## 사용자 요청
"{user_message}"

## 요청사항
다음 JSON 형식으로 응답해주세요:
{{
    "household_size": 숫자 (가족 구성원 수, 없으면 null),
    "budget": 숫자 (예산, 만원 단위, 없으면 null),
    "categories": ["TV", "냉장고", "세탁기", "에어컨", "청소기"] (관심 카테고리, 없으면 []),
    "priority": "design" | "tech" | "eco" | "value" (우선순위, 없으면 null),
    "housing_type": "apartment" | "house" | "officetel" (주거 형태, 없으면 null),
    "pyung": 숫자 (평수, 없으면 null),
    "vibe": "modern" | "cozy" | "natural" | "luxury" (스타일, 없으면 null),
    "additional_info": "추가로 파악한 정보나 요청사항"
}}

## 예시
사용자: "2인 가구, 작은 주방, 예산 200만원"
응답: {{"household_size": 2, "budget": 200, "categories": ["냉장고"], "priority": "value", "housing_type": "apartment", "pyung": null, "vibe": null, "additional_info": "작은 주방에 적합한 컴팩트한 제품 선호"}}

사용자: "큰 거실에 4K TV 추천해줘"
응답: {{"household_size": null, "budget": null, "categories": ["TV"], "priority": "tech", "housing_type": null, "pyung": null, "vibe": null, "additional_info": "4K 해상도 TV 선호"}}

JSON 형식으로만 응답하고, 다른 설명은 하지 마세요."""

        try:
            # ChatGPT로 정보 추출
            response_text = chatgpt_service.chat_response(
                user_message=prompt,
                context={'history': []}
            )
            
            # JSON 파싱
            # 응답에서 JSON 부분만 추출
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON 형식이 아닙니다.")
            
            extracted_info = json.loads(response_text[json_start:json_end])
            
            # 기본값 설정
            user_profile = {
                'vibe': extracted_info.get('vibe') or 'modern',
                'household_size': extracted_info.get('household_size') or 2,
                'housing_type': extracted_info.get('housing_type') or 'apartment',
                'pyung': extracted_info.get('pyung') or 25,
                'priority': extracted_info.get('priority') or 'value',
                'budget_level': cls._calculate_budget_level(extracted_info.get('budget')),
                'categories': extracted_info.get('categories') or ['TV', '냉장고', '세탁기'],
                'additional_info': extracted_info.get('additional_info', '')
            }
            
            # 추천 엔진 호출
            result = recommendation_engine.get_recommendations(
                user_profile=user_profile,
                limit=5
            )
            
            # 추가 정보 포함
            if result.get('success'):
                result['extracted_info'] = extracted_info
                result['user_message'] = user_message
            
            return result
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'정보 추출 실패: JSON 파싱 오류 - {str(e)}',
                'raw_response': response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'추천 실패: {str(e)}'
            }
    
    @classmethod
    def _calculate_budget_level(cls, budget):
        """예산을 예산 레벨로 변환"""
        if budget is None:
            return 'medium'
        
        if budget < 300:
            return 'low'
        elif budget < 700:
            return 'medium'
        else:
            return 'high'
    
    @classmethod
    def chat_recommendation(cls, user_message: str, conversation_history: list = None):
        """
        대화형 추천 (사용자와 대화하며 추천)
        
        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 기록
            
        Returns:
            AI 응답 및 추천 결과
        """
        # 먼저 일반적인 대화인지 추천 요청인지 판단
        recommendation_keywords = ['추천', '추천해', '추천해줘', '어떤', '뭐가', '제품', '가전', '구매', '살까']
        is_recommendation_request = any(keyword in user_message for keyword in recommendation_keywords)
        
        if is_recommendation_request:
            # 추천 요청인 경우
            result = cls.recommend_from_conversation(user_message, conversation_history)
            
            if result.get('success'):
                recommendations = result.get('recommendations', [])
                if recommendations:
                    # 추천 결과를 자연어로 변환
                    response_text = "다음 제품들을 추천드려요:\n\n"
                    for i, rec in enumerate(recommendations[:3], 1):
                        response_text += f"{i}. {rec.get('name', '제품')} - {rec.get('price', 0):,}원\n"
                        if rec.get('reason'):
                            response_text += f"   {rec.get('reason')}\n"
                    response_text += "\n더 자세한 정보가 필요하시면 말씀해주세요!"
                else:
                    response_text = "조건에 맞는 제품을 찾지 못했어요. 다른 조건으로 다시 말씀해주세요."
            else:
                response_text = f"죄송해요, 추천 중 오류가 발생했어요: {result.get('error', '알 수 없는 오류')}"
            
            return {
                'type': 'recommendation',
                'message': response_text,
                'recommendations': result.get('recommendations', []) if result.get('success') else [],
                'raw_result': result
            }
        else:
            # 일반 대화인 경우 ChatGPT로 응답
            response_text = chatgpt_service.chat_response(
                user_message=user_message,
                context={'history': conversation_history or []}
            )
            
            return {
                'type': 'chat',
                'message': response_text,
                'recommendations': []
            }


# 싱글톤 인스턴스
ai_recommendation_service = AIRecommendationService()

