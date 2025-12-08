"""
제품 비교 AI 분석 서비스
"""
import json
from .chatgpt_service import chatgpt_service
from api.models import Product


class ProductComparisonService:
    """제품 비교 AI 분석 서비스"""
    
    @classmethod
    def compare_products(cls, product_ids: list, user_context: dict = None):
        """
        여러 제품을 AI로 비교 분석
        
        Args:
            product_ids: 비교할 제품 ID 리스트 (2-5개)
            user_context: 사용자 컨텍스트 (가족 구성, 예산 등)
            
        Returns:
            비교 분석 결과
        """
        if len(product_ids) < 2 or len(product_ids) > 5:
            return {
                'success': False,
                'error': '제품은 2개 이상 5개 이하로 비교할 수 있습니다.'
            }
        
        if not chatgpt_service.is_available():
            return {
                'success': False,
                'error': 'OpenAI API를 사용할 수 없습니다.'
            }
        
        try:
            # 제품 정보 조회
            products = Product.objects.filter(id__in=product_ids, is_active=True)
            if products.count() != len(product_ids):
                return {
                    'success': False,
                    'error': '일부 제품을 찾을 수 없습니다.'
                }
            
            # 제품 정보 정리
            products_data = []
            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'model_number': product.model_number,
                    'category': product.category,
                    'price': float(product.price) if product.price else 0,
                    'discount_price': float(product.discount_price) if product.discount_price else 0,
                    'specs': {}
                }
                
                # 스펙 정보 추가 (간단한 예시)
                if hasattr(product, 'productspec'):
                    try:
                        spec = product.productspec
                        product_data['specs'] = {
                            'capacity': getattr(spec, 'capacity', None),
                            'power_consumption': getattr(spec, 'power_consumption', None),
                            'dimensions': getattr(spec, 'dimensions', None),
                        }
                    except:
                        pass
                
                products_data.append(product_data)
            
            # 사용자 컨텍스트 정보
            context_info = ""
            if user_context:
                context_info = f"""
## 사용자 정보
- 가족 구성: {user_context.get('household_size', '미지정')}인
- 예산: {user_context.get('budget', '미지정')}만원
- 주거 형태: {user_context.get('housing_type', '미지정')}
- 우선순위: {user_context.get('priority', '미지정')}
"""
            
            # AI 비교 분석 프롬프트
            prompt = f"""당신은 LG전자 가전 전문가입니다. 다음 제품들을 비교 분석해주세요.

{context_info}

## 비교할 제품들
{json.dumps(products_data, ensure_ascii=False, indent=2)}

## 요청사항
다음 JSON 형식으로 응답해주세요:
{{
    "summary": "전체 비교 요약 (3-4문장)",
    "comparison": [
        {{
            "product_id": 제품ID,
            "product_name": "제품명",
            "strengths": ["장점1", "장점2", "장점3"],
            "weaknesses": ["단점1", "단점2"],
            "best_for": "이 제품이 가장 적합한 사용자/상황"
        }}
    ],
    "recommendation": {{
        "best_choice": 제품ID,
        "reason": "추천 이유",
        "alternative": 제품ID (대안, 선택),
        "alternative_reason": "대안 추천 이유 (선택)"
    }},
    "price_analysis": "가격 대비 가치 분석",
    "final_advice": "최종 구매 조언"
}}

JSON 형식으로만 응답하고, 다른 설명은 하지 마세요."""
            
            # ChatGPT 호출
            response_text = chatgpt_service.chat_response(
                user_message=prompt,
                context={}
            )
            
            # JSON 파싱
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON 형식이 아닙니다.")
            
            comparison_result = json.loads(response_text[json_start:json_end])
            
            return {
                'success': True,
                'products': products_data,
                'analysis': comparison_result
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'분석 결과 파싱 실패: {str(e)}',
                'raw_response': response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'비교 분석 실패: {str(e)}'
            }
    
    @classmethod
    def get_simple_comparison(cls, product_ids: list):
        """
        간단한 제품 비교 (AI 없이 기본 정보만)
        
        Args:
            product_ids: 비교할 제품 ID 리스트
            
        Returns:
            간단한 비교 결과
        """
        try:
            products = Product.objects.filter(id__in=product_ids, is_active=True)
            
            comparison = []
            for product in products:
                comparison.append({
                    'id': product.id,
                    'name': product.name,
                    'model_number': product.model_number,
                    'category': product.category,
                    'price': float(product.price) if product.price else 0,
                    'discount_price': float(product.discount_price) if product.discount_price else 0,
                })
            
            return {
                'success': True,
                'products': comparison
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 싱글톤 인스턴스
product_comparison_service = ProductComparisonService()

