"""
ERD 기반 온보딩 데이터 저장 헬퍼 함수
"""
from .models import (
    OnboardingQuestion, OnboardingAnswer, OnboardingUserResponse,
    OnboardingSessionCategories, OnboardingSessionMainSpaces, OnboardingSessionPriorities,
    OnboardSessRecProducts, Product
)


def save_onboarding_to_erd_models(session, data):
    """
    온보딩 세션 데이터를 ERD 기반 모델에 저장
    
    Args:
        session: OnboardingSession 객체
        data: 요청 데이터
    """
    # 1. OnboardingUserResponse 저장 (각 단계별 응답)
    save_user_responses(session, data)
    
    # 2. OnboardingSessionCategories 저장
    save_session_categories(session, data)
    
    # 3. OnboardingSessionMainSpaces 저장
    save_session_main_spaces(session, data)
    
    # 4. OnboardingSessionPriorities 저장
    save_session_priorities(session, data)


def save_user_responses(session, data):
    """OnboardingUserResponse에 각 단계별 응답 저장"""
    try:
        # Step 1: Vibe
        if data.get('vibe'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='vibe_question',
                defaults={
                    'question_text': '새로운 가전과 함께할 공간, 어떤 분위기를 꿈꾸시나요?',
                    'question_type': 'vibe',
                    'is_required': 'Y'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('vibe'),
                defaults={'answer_text': data.get('vibe')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 2: Household Size
        if data.get('household_size'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='household_question',
                defaults={
                    'question_text': '이 공간에서 함께 생활하는 메이트는 누구인가요?',
                    'question_type': 'household',
                    'is_required': 'Y'
                }
            )
            household_size = data.get('household_size')
            if isinstance(household_size, str):
                household_size = household_size.replace('인', '').replace(' 이상', '').strip()
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'input_value': str(household_size)}
            )
        
        # Step 2: Has Pet
        if 'has_pet' in data:
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='pet_question',
                defaults={
                    'question_text': '혹시 반려동물과 함께하시나요?',
                    'question_type': 'pet',
                    'is_required': 'N'
                }
            )
            has_pet = data.get('has_pet')
            answer_value = 'yes' if has_pet else 'no'
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=answer_value,
                defaults={'answer_text': '네' if has_pet else '아니요'}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 3: Housing Type
        if data.get('housing_type'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='housing_question',
                defaults={
                    'question_text': '가전을 설치할 곳의 주거 형태는 무엇인가요?',
                    'question_type': 'housing',
                    'is_required': 'Y'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('housing_type'),
                defaults={'answer_text': data.get('housing_type')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 3: Pyung
        if data.get('pyung'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='pyung_question',
                defaults={
                    'question_text': '해당 공간의 크기는 대략 어느 정도인가요?',
                    'question_type': 'pyung',
                    'is_required': 'Y'
                }
            )
            pyung = data.get('pyung')
            if isinstance(pyung, str):
                pyung = pyung.replace('평', '').strip()
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'input_value': str(pyung)}
            )
        
        # Step 4: Cooking
        if data.get('cooking'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='cooking_question',
                defaults={
                    'question_text': '평소 집에서 요리는 얼마나 자주 하시나요?',
                    'question_type': 'cooking',
                    'is_required': 'N'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('cooking'),
                defaults={'answer_text': data.get('cooking')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 4: Laundry
        if data.get('laundry'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='laundry_question',
                defaults={
                    'question_text': '세탁은 주로 어떻게 하시나요?',
                    'question_type': 'laundry',
                    'is_required': 'N'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('laundry'),
                defaults={'answer_text': data.get('laundry')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 4: Media
        if data.get('media'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='media_question',
                defaults={
                    'question_text': '집에서 TV나 영상을 주로 어떻게 즐기시나요?',
                    'question_type': 'media',
                    'is_required': 'N'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('media'),
                defaults={'answer_text': data.get('media')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 5: Priority
        if data.get('priority'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='priority_question',
                defaults={
                    'question_text': '구매 시 가장 중요하게 생각하는 것은 무엇인가요?',
                    'question_type': 'priority',
                    'is_required': 'Y'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('priority'),
                defaults={'answer_text': data.get('priority')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
        
        # Step 6: Budget Level
        if data.get('budget_level'):
            question, _ = OnboardingQuestion.objects.get_or_create(
                question_code='budget_question',
                defaults={
                    'question_text': '예산 범위를 선택해주세요',
                    'question_type': 'budget',
                    'is_required': 'Y'
                }
            )
            answer, _ = OnboardingAnswer.objects.get_or_create(
                question=question,
                answer_value=data.get('budget_level'),
                defaults={'answer_text': data.get('budget_level')}
            )
            OnboardingUserResponse.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
            
    except Exception as e:
        print(f"[ERD 저장] OnboardingUserResponse 저장 실패: {e}")
        raise


def save_session_categories(session, data):
    """OnboardingSessionCategories에 카테고리 저장"""
    try:
        selected_categories = data.get('selected_categories', [])
        if not isinstance(selected_categories, list):
            selected_categories = []
        
        # 기존 카테고리 삭제 후 재생성
        OnboardingSessionCategories.objects.filter(session=session).delete()
        
        for category in selected_categories:
            OnboardingSessionCategories.objects.get_or_create(
                session=session,
                category_name=category
            )
    except Exception as e:
        print(f"[ERD 저장] OnboardingSessionCategories 저장 실패: {e}")
        raise


def save_session_main_spaces(session, data):
    """OnboardingSessionMainSpaces에 주요 공간 저장"""
    try:
        main_spaces = data.get('main_space', [])
        if isinstance(main_spaces, str):
            try:
                import json
                main_spaces = json.loads(main_spaces)
            except:
                main_spaces = [main_spaces] if main_spaces else []
        if not isinstance(main_spaces, list):
            main_spaces = []
        
        # 기존 주요 공간 삭제 후 재생성
        OnboardingSessionMainSpaces.objects.filter(session=session).delete()
        
        for space in main_spaces:
            OnboardingSessionMainSpaces.objects.get_or_create(
                session=session,
                main_space=space
            )
    except Exception as e:
        print(f"[ERD 저장] OnboardingSessionMainSpaces 저장 실패: {e}")
        raise


def save_session_priorities(session, data):
    """OnboardingSessionPriorities에 우선순위 저장"""
    try:
        priority_list = data.get('priority_list', [])
        if isinstance(priority_list, str):
            try:
                import json
                priority_list = json.loads(priority_list)
            except:
                priority_list = [priority_list] if priority_list else []
        if not isinstance(priority_list, list):
            priority_list = [data.get('priority', 'value')]
        if len(priority_list) == 0:
            priority_list = [data.get('priority', 'value')]
        
        # 기존 우선순위 삭제 후 재생성
        OnboardingSessionPriorities.objects.filter(session=session).delete()
        
        for idx, priority in enumerate(priority_list, 1):
            OnboardingSessionPriorities.objects.get_or_create(
                session=session,
                priority_order=idx,
                defaults={'priority': priority}
            )
    except Exception as e:
        print(f"[ERD 저장] OnboardingSessionPriorities 저장 실패: {e}")
        raise


def save_recommended_products_to_erd(session, recommendations):
    """OnboardSessRecProducts에 추천 제품 저장"""
    try:
        # 기존 추천 제품 삭제 후 재생성
        OnboardSessRecProducts.objects.filter(session=session).delete()
        
        for idx, rec in enumerate(recommendations, 1):
            product_id = rec.get('product_id') or rec.get('id')
            if not product_id:
                continue
            
            try:
                product = Product.objects.get(product_id=product_id)
                category = rec.get('category') or rec.get('main_category') or '기타'
                score = rec.get('score') or rec.get('taste_score') or None
                
                OnboardSessRecProducts.objects.get_or_create(
                    session=session,
                    product=product,
                    defaults={
                        'category_name': category,
                        'rank_order': idx,
                        'score': score
                    }
                )
            except Product.DoesNotExist:
                print(f"[ERD 저장] 제품을 찾을 수 없음: {product_id}")
                continue
            except Exception as e:
                print(f"[ERD 저장] 추천 제품 저장 실패 (product_id={product_id}): {e}")
                continue
                
    except Exception as e:
        print(f"[ERD 저장] OnboardSessRecProducts 저장 실패: {e}")
        raise

