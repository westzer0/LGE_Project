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
        prompt = f"""사용자의 자연어 요청을 분석하여 제품 추천에 필요한 정보를 JSON 형식으로 추출해주세요.

이전 대화 맥락: {context if context else "없음"}

사용자 요청: "{user_message}"

다음 JSON 형식으로 응답하세요:
{{
    "household_size": 숫자 또는 null,
    "budget": 숫자 (만원 단위) 또는 null,
    "categories": ["TV", "냉장고", "세탁기", "에어컨", "청소기"] 또는 [],
    "priority": "design" | "tech" | "eco" | "value" 또는 null,
    "housing_type": "apartment" | "house" | "officetel" 또는 null,
    "pyung": 숫자 또는 null,
    "vibe": "modern" | "cozy" | "natural" | "luxury" 또는 null,
    "additional_info": "문자열"
}}

예시:
- "2인 가구, 작은 주방, 예산 200만원" → {{"household_size": 2, "budget": 200, "categories": ["냉장고"], "priority": "value", "housing_type": "apartment", "pyung": null, "vibe": null, "additional_info": "작은 주방에 적합한 컴팩트한 제품 선호"}}
- "큰 거실에 4K TV 추천해줘" → {{"household_size": null, "budget": null, "categories": ["TV"], "priority": "tech", "housing_type": null, "pyung": null, "vibe": null, "additional_info": "4K 해상도 TV 선호"}}"""

        try:
            # ChatGPT로 정보 추출 (JSON 형식 강제)
            response_text = chatgpt_service.chat_response(
                user_message=prompt,
                context={'history': []},
                require_json=True
            )
            
            # JSON 파싱 - 더 견고한 추출 로직
            extracted_info = cls._extract_json_from_response(response_text)
            
            # JSON 파싱 실패 시 사용자 메시지에서 직접 정보 추출
            if extracted_info is None:
                print(f"[AI 추천] JSON 파싱 실패, 사용자 메시지에서 직접 추출 시도: {user_message}")
                extracted_info = cls._extract_info_from_message(user_message)
            
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
            
        except Exception as e:
            print(f"[AI 추천] 추천 실패: {e}")
            import traceback
            print(f"[AI 추천] 트레이스백: {traceback.format_exc()}")
            
            # 최후의 수단: 기본값으로 추천 시도
            try:
                print(f"[AI 추천] 기본값으로 추천 시도")
                extracted_info = cls._extract_info_from_message(user_message)
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
                
                result = recommendation_engine.get_recommendations(
                    user_profile=user_profile,
                    limit=5
                )
                
                if result.get('success'):
                    result['extracted_info'] = extracted_info
                    result['user_message'] = user_message
                
                return result
            except Exception as fallback_error:
                print(f"[AI 추천] 기본값 추천도 실패: {fallback_error}")
                return {
                    'success': False,
                    'error': '추천 중 오류가 발생했어요. 다시 시도해주세요.'
                }
    
    @classmethod
    def _extract_json_from_response(cls, response_text: str) -> dict:
        """응답 텍스트에서 JSON 추출 (견고한 파싱)"""
        if not response_text:
            return None
        
        try:
            # 먼저 직접 파싱 시도 (response_format 사용 시 이미 JSON)
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass
            
            # 마크다운 코드 블록 제거
            cleaned_text = response_text
            if '```json' in cleaned_text:
                start = cleaned_text.find('```json') + 7
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            elif '```' in cleaned_text:
                start = cleaned_text.find('```') + 3
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            
            # JSON 부분만 추출
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return None
            
            json_str = cleaned_text[json_start:json_end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[AI 추천] JSON 추출 실패: {e}")
            print(f"[AI 추천] 원본 응답: {response_text[:200]}")
            return None
    
    @classmethod
    def _extract_info_from_message(cls, user_message: str) -> dict:
        """사용자 메시지에서 직접 정보 추출 (간단한 패턴 매칭)"""
        import re
        
        extracted = {
            'household_size': None,
            'budget': None,
            'categories': [],
            'priority': None,
            'housing_type': None,
            'pyung': None,
            'vibe': None,
            'additional_info': user_message
        }
        
        # 가구 인원 추출
        household_match = re.search(r'(\d+)\s*인\s*가구', user_message)
        if household_match:
            extracted['household_size'] = int(household_match.group(1))
        
        # 예산 추출 (만원 단위)
        budget_match = re.search(r'예산\s*(\d+)\s*만원', user_message)
        if budget_match:
            extracted['budget'] = int(budget_match.group(1))
        else:
            # 숫자 + 만원 패턴
            budget_match = re.search(r'(\d+)\s*만원', user_message)
            if budget_match:
                extracted['budget'] = int(budget_match.group(1))
        
        # 카테고리 추출
        categories_map = {
            '냉장고': '냉장고',
            '세탁기': '세탁기',
            'TV': 'TV',
            '티비': 'TV',
            '에어컨': '에어컨',
            '청소기': '청소기',
            '주방': '냉장고',
            '거실': 'TV'
        }
        
        for keyword, category in categories_map.items():
            if keyword in user_message:
                if category not in extracted['categories']:
                    extracted['categories'].append(category)
        
        # 주거 형태 추출
        if '아파트' in user_message or 'apt' in user_message.lower():
            extracted['housing_type'] = 'apartment'
        elif '주택' in user_message or '단독' in user_message:
            extracted['housing_type'] = 'house'
        elif '오피스텔' in user_message or '원룸' in user_message:
            extracted['housing_type'] = 'officetel'
        
        # 평수 추출
        pyung_match = re.search(r'(\d+)\s*평', user_message)
        if pyung_match:
            extracted['pyung'] = int(pyung_match.group(1))
        
        # 우선순위 추출
        if '가성비' in user_message or '저렴' in user_message or '예산' in user_message:
            extracted['priority'] = 'value'
        elif '디자인' in user_message or '예쁜' in user_message:
            extracted['priority'] = 'design'
        elif '기술' in user_message or '스마트' in user_message or 'AI' in user_message:
            extracted['priority'] = 'tech'
        elif '친환경' in user_message or '에코' in user_message:
            extracted['priority'] = 'eco'
        
        return extracted
    
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
        product_info_keywords = ['가구', '주방', '예산', '평수', '거실', '침실', '냉장고', '세탁기', 'TV', '에어컨', '청소기']
        number_keywords = ['인', '만원', '원', '평']
        
        # 명시적 추천 키워드 체크
        has_recommendation_keyword = any(keyword in user_message for keyword in recommendation_keywords)
        
        # 제품 관련 정보가 포함되어 있는지 체크 (가구, 주방, 예산 등)
        has_product_info = any(keyword in user_message for keyword in product_info_keywords)
        has_number = any(keyword in user_message for keyword in number_keywords) or any(char.isdigit() for char in user_message)
        
        # 추천 요청으로 판단: 명시적 키워드가 있거나, 제품 정보 + 숫자가 함께 있는 경우
        is_recommendation_request = has_recommendation_keyword or (has_product_info and has_number)
        
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
                error_msg = result.get('error', '알 수 없는 오류')
                print(f"[AI 추천] 추천 실패: {error_msg}")
                # 사용자에게 더 친절한 메시지 제공
                if 'OpenAI API' in error_msg:
                    response_text = "죄송해요, 현재 AI 서비스를 이용할 수 없어요. 잠시 후 다시 시도해주세요."
                else:
                    # 오류 상세 내용을 사용자에게 노출하지 않고 친절한 메시지 제공
                    response_text = "죄송해요, 요청을 이해하는데 문제가 있었어요. 예를 들어 '2인 가구, 작은 주방, 예산 200만원, 냉장고 추천해줘'처럼 구체적으로 말씀해주시면 더 정확한 추천을 드릴 수 있어요."
            
            return {
                'type': 'recommendation',
                'message': response_text,
                'recommendations': result.get('recommendations', []) if result.get('success') else [],
                'raw_result': result,
                'success': result.get('success', False),
                'error': result.get('error') if not result.get('success') else None
            }
        else:
            # 일반 대화인 경우 ChatGPT로 응답
            try:
                response_text = chatgpt_service.chat_response(
                    user_message=user_message,
                    context={'history': conversation_history or []}
                )
                
                return {
                    'type': 'chat',
                    'message': response_text,
                    'recommendations': [],
                    'success': True
                }
            except Exception as e:
                print(f"[AI 추천] ChatGPT 응답 오류: {e}")
                return {
                    'type': 'chat',
                    'message': '죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.',
                    'recommendations': [],
                    'success': False,
                    'error': str(e)
                }


# 싱글톤 인스턴스
ai_recommendation_service = AIRecommendationService()

