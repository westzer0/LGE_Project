"""
포트폴리오 서비스
PRD 기반 포트폴리오 관리 및 추천 로직
"""
import json
import random
from typing import Dict, List, Optional
from django.db.models import Q
from api.models import Product, Portfolio, OnboardingSession
from .recommendation_engine import recommendation_engine
from .style_analysis_service import style_analysis_service


class PortfolioService:
    """포트폴리오 서비스"""
    
    @staticmethod
    def create_portfolio_from_onboarding(
        session_id: str,
        user_id: str,
        exclude_product_ids: List[int] = None
    ) -> dict:
        """
        온보딩 세션 기반 포트폴리오 생성
        
        Args:
            session_id: 온보딩 세션 ID
            user_id: 사용자 ID
            exclude_product_ids: 제외할 제품 ID 리스트 (다시 추천받기용)
            
        Returns:
            {
                "success": True,
                "portfolio_id": "...",
                "style_analysis": {...},
                "recommendations": [...],
                "total_price": 0,
                "total_discount_price": 0
            }
        """
        try:
            print(f"[Portfolio Service] 포트폴리오 생성 시작: session_id={session_id}, user_id={user_id}")
            
            # 온보딩 세션 조회
            session = OnboardingSession.objects.get(session_id=session_id)
            print(f"[Portfolio Service] 온보딩 세션 조회 성공: {session_id}")
            
            # 사용자 프로필 생성
            user_profile = session.to_user_profile()
            print(f"[Portfolio Service] 사용자 프로필 생성 완료: {user_profile}")
            
            # 온보딩 데이터 추출 (정규화 테이블에서 읽기)
            from api.services.onboarding_db_service import onboarding_db_service
            
            session_data = onboarding_db_service.get_session(session_id)
            
            # main_space 정규화 테이블에서 읽기
            main_spaces = []
            if session_data and 'MAIN_SPACE' in session_data:
                import json
                try:
                    main_space_str = session_data['MAIN_SPACE']
                    if main_space_str:
                        main_spaces = json.loads(main_space_str) if isinstance(main_space_str, str) else main_space_str
                except:
                    main_spaces = []
            
            # 온보딩 데이터 병합
            onboarding_data = {
                'vibe': session.vibe,
                'household_size': session.household_size,
                'housing_type': session.housing_type,
                'pyung': session.pyung,
                'priority': session.priority,
                'budget_level': session.budget_level,
                'has_pet': session.has_pet if session.has_pet is not None else False,
                'cooking': session.cooking or 'sometimes',
                'laundry': session.laundry or 'weekly',
                'media': session.media or 'balanced',
                'main_space': main_spaces[0] if main_spaces else 'living',
            }
            
            # 스타일 분석 생성
            style_analysis = style_analysis_service.generate_style_analysis(
                onboarding_data=onboarding_data,
                user_profile=user_profile
            )
            
            # 추천 엔진 호출
            result = recommendation_engine.get_recommendations(
                user_profile=user_profile,
                limit=10  # 충분히 많은 제품 추천
            )
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', '추천 실패')
                }
            
            recommendations = result.get('recommendations', [])
            
            # 제외할 제품 필터링 (다시 추천받기용)
            if exclude_product_ids:
                recommendations = [
                    r for r in recommendations
                    if r.get('product_id') not in exclude_product_ids
                ]
            
            # 카테고리별로 최대 3개씩 선택
            category_products = {}
            for rec in recommendations:
                category = rec.get('category') or rec.get('main_category', '기타')
                if category not in category_products:
                    category_products[category] = []
                if len(category_products[category]) < 3:
                    category_products[category].append(rec)
            
            # 최종 추천 리스트 생성
            final_recommendations = []
            for category, products in category_products.items():
                final_recommendations.extend(products)
            
            if not final_recommendations:
                return {
                    'success': False,
                    'error': '추천 제품이 없습니다.'
                }
            
            # 가격 계산
            total_price = sum(r.get('price', 0) for r in final_recommendations)
            total_discount_price = sum(
                r.get('discount_price') or r.get('price', 0)
                for r in final_recommendations
            )
            
            # 포트폴리오 생성
            print(f"[Portfolio Service] 포트폴리오 생성 중: {len(final_recommendations)}개 제품, 총 가격={total_price}")
            try:
                portfolio = Portfolio.objects.create(
                    user_id=user_id,
                    onboarding_session=session,
                    style_type=style_analysis.get('style_type', 'modern'),
                    style_title=style_analysis.get('title', '나에게 딱 맞는 스타일'),
                    style_subtitle=style_analysis.get('subtitle', '당신의 라이프스타일에 맞춰 구성했어요.'),
                    onboarding_data=onboarding_data,
                    products=final_recommendations,
                    total_original_price=total_price,
                    total_discount_price=total_discount_price,
                    match_score=85,  # 기본 매칭 점수
                    status='draft'
                )
                print(f"[Portfolio Service] 포트폴리오 Django DB 저장 성공: portfolio_id={portfolio.portfolio_id}")
                
                # Oracle DB에도 저장
                try:
                    PortfolioService._save_portfolio_to_oracle(
                        portfolio=portfolio,
                        session_id=session_id,
                        member_id=session.member_id if hasattr(session, 'member_id') else None,
                        recommendations=final_recommendations
                    )
                    print(f"[Portfolio Service] 포트폴리오 Oracle DB 저장 성공")
                except Exception as oracle_error:
                    print(f"[Portfolio Service] 포트폴리오 Oracle DB 저장 실패 (계속 진행): {oracle_error}")
                    import traceback
                    traceback.print_exc()
                    # Oracle 저장 실패해도 계속 진행 (하위 호환성)
                    
            except Exception as create_error:
                print(f"[Portfolio Service] 포트폴리오 DB 저장 실패: {create_error}")
                import traceback
                traceback.print_exc()
                raise
            
            print(f"[Portfolio Service] 포트폴리오 생성 완료: portfolio_id={portfolio.portfolio_id}, internal_key={portfolio.internal_key}")
            
            return {
                'success': True,
                'portfolio_id': portfolio.portfolio_id,
                'internal_key': portfolio.internal_key,
                'style_analysis': style_analysis,
                'recommendations': final_recommendations,
                'total_price': total_price,
                'total_discount_price': total_discount_price,
                'match_score': portfolio.match_score
            }
        
        except OnboardingSession.DoesNotExist:
            print(f"[Portfolio Service] 온보딩 세션을 찾을 수 없음: {session_id}")
            return {
                'success': False,
                'error': '온보딩 세션을 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Portfolio Service Error] {e}")
            import traceback
            print(f"[Portfolio Service Error] Traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': f'포트폴리오 생성 실패: {str(e)}'
            }
    
    @staticmethod
    def refresh_portfolio(
        portfolio_id: str,
        exclude_product_ids: List[int] = None
    ) -> dict:
        """
        포트폴리오 다시 추천받기 (중복 제거)
        
        Args:
            portfolio_id: 포트폴리오 ID
            exclude_product_ids: 제외할 제품 ID 리스트
            
        Returns:
            새로운 추천 결과
        """
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            
            # 기존 제품 ID 수집
            existing_product_ids = [
                p.get('product_id') for p in portfolio.products
                if p.get('product_id')
            ]
            
            # 제외할 제품 ID 병합
            if exclude_product_ids:
                existing_product_ids.extend(exclude_product_ids)
            
            # 온보딩 세션 기반으로 새 포트폴리오 생성
            if portfolio.onboarding_session:
                return PortfolioService.create_portfolio_from_onboarding(
                    session_id=portfolio.onboarding_session.session_id,
                    user_id=portfolio.user_id,
                    exclude_product_ids=list(set(existing_product_ids))  # 중복 제거
                )
            else:
                return {
                    'success': False,
                    'error': '온보딩 세션 정보가 없습니다.'
                }
        
        except Portfolio.DoesNotExist:
            return {
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Portfolio Refresh Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_alternative_recommendations(
        portfolio_id: str,
        category: str = None
    ) -> dict:
        """
        다른 추천 후보 확인 (카테고리별 최대 3개)
        
        Args:
            portfolio_id: 포트폴리오 ID
            category: 특정 카테고리 (선택)
            
        Returns:
            {
                "success": True,
                "alternatives": [
                    {
                        "category": "TV",
                        "products": [...]
                    },
                    ...
                ]
            }
        """
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            
            # 온보딩 세션 기반으로 추천
            if not portfolio.onboarding_session:
                return {
                    'success': False,
                    'error': '온보딩 세션 정보가 없습니다.'
                }
            
            session = portfolio.onboarding_session
            user_profile = session.to_user_profile()
            
            # 온보딩 데이터 추출
            onboarding_data = portfolio.onboarding_data or {}
            
            # 기존 추천 제품 ID 수집
            existing_product_ids = [
                p.get('product_id') for p in portfolio.products
                if p.get('product_id')
            ]
            
            # 추천 엔진 호출
            result = recommendation_engine.get_recommendations(
                user_profile=user_profile,
                limit=20  # 충분히 많은 제품 추천
            )
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', '추천 실패')
                }
            
            recommendations = result.get('recommendations', [])
            
            # 기존 제품 제외
            recommendations = [
                r for r in recommendations
                if r.get('product_id') not in existing_product_ids
            ]
            
            # 카테고리별로 그룹화
            category_products = {}
            for rec in recommendations:
                rec_category = rec.get('category') or rec.get('main_category', '기타')
                
                # 특정 카테고리만 요청한 경우 필터링
                if category and rec_category != category:
                    continue
                
                if rec_category not in category_products:
                    category_products[rec_category] = []
                
                # 카테고리별 최대 3개
                if len(category_products[rec_category]) < 3:
                    category_products[rec_category].append(rec)
            
            # 결과 포맷팅
            alternatives = []
            for cat, products in category_products.items():
                alternatives.append({
                    'category': cat,
                    'products': products
                })
            
            return {
                'success': True,
                'alternatives': alternatives
            }
        
        except Portfolio.DoesNotExist:
            return {
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Alternative Recommendations Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def add_products_to_cart(
        portfolio_id: str,
        user_id: str
    ) -> dict:
        """
        포트폴리오 전체 제품을 장바구니에 추가
        
        Args:
            portfolio_id: 포트폴리오 ID
            user_id: 사용자 ID
            
        Returns:
            {
                "success": True,
                "added_count": 3,
                "cart_items": [...]
            }
        """
        try:
            from api.models import Cart
            
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            
            # 포트폴리오 제품 목록
            products = portfolio.products or []
            
            added_count = 0
            cart_items = []
            
            for product_data in products:
                product_id = product_data.get('product_id')
                if not product_id:
                    continue
                
                try:
                    product = Product.objects.get(id=product_id)
                    
                    # 장바구니에 추가 (기존 항목이 있으면 수량 증가)
                    cart_item, created = Cart.objects.get_or_create(
                        user_id=user_id,
                        product=product,
                        defaults={
                            'quantity': 1,
                            'extra_data': {
                                'price': product_data.get('price', 0),
                                'discount_price': product_data.get('discount_price'),
                                'from_portfolio': portfolio_id
                            }
                        }
                    )
                    
                    if not created:
                        # 기존 항목이 있으면 수량 증가
                        cart_item.quantity += 1
                        cart_item.save()
                    
                    cart_items.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'quantity': cart_item.quantity
                    })
                    added_count += 1
                
                except Product.DoesNotExist:
                    print(f"[Cart Add Error] 제품을 찾을 수 없습니다: {product_id}")
                    continue
            
            return {
                'success': True,
                'added_count': added_count,
                'cart_items': cart_items
            }
        
        except Portfolio.DoesNotExist:
            return {
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Add to Cart Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }


    @staticmethod
    def update_portfolio_products(
        portfolio_id: str,
        action: str,  # 'add', 'remove', 'replace', 'upgrade'
        product_id: int = None,
        new_product_id: int = None,
        category: str = None
    ) -> dict:
        """
        포트폴리오 제품 편집 (추가/삭제/교체/업그레이드)
        
        Args:
            portfolio_id: 포트폴리오 ID
            action: 작업 유형 ('add', 'remove', 'replace', 'upgrade')
            product_id: 대상 제품 ID (remove, replace, upgrade 시 필수)
            new_product_id: 새 제품 ID (add, replace, upgrade 시 필수)
            category: 카테고리 (add 시 특정 카테고리에서 선택)
            
        Returns:
            {
                "success": True,
                "portfolio_id": "...",
                "products": [...],
                "total_price": 0,
                "total_discount_price": 0
            }
        """
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            products = portfolio.products or []
            
            if action == 'add':
                # 제품 추가
                if not new_product_id:
                    return {
                        'success': False,
                        'error': 'new_product_id 필수'
                    }
                
                try:
                    new_product = Product.objects.get(id=new_product_id)
                    
                    # 이미 존재하는지 확인
                    existing = any(p.get('product_id') == new_product_id for p in products)
                    if existing:
                        return {
                            'success': False,
                            'error': '이미 포트폴리오에 포함된 제품입니다.'
                        }
                    
                    # 제품 정보 추가
                    product_data = {
                        'product_id': new_product.id,
                        'name': new_product.name,
                        'model_number': new_product.model_number,
                        'category': new_product.category,
                        'price': float(new_product.price),
                        'discount_price': float(new_product.discount_price) if new_product.discount_price else None,
                        'image_url': new_product.image_url or '',
                        'match_score': 80  # 기본 매칭 점수
                    }
                    products.append(product_data)
                    
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'제품을 찾을 수 없습니다: {new_product_id}'
                    }
            
            elif action == 'remove':
                # 제품 삭제
                if not product_id:
                    return {
                        'success': False,
                        'error': 'product_id 필수'
                    }
                
                products = [p for p in products if p.get('product_id') != product_id]
            
            elif action == 'replace':
                # 제품 교체
                if not product_id or not new_product_id:
                    return {
                        'success': False,
                        'error': 'product_id와 new_product_id 필수'
                    }
                
                try:
                    new_product = Product.objects.get(id=new_product_id)
                    
                    # 기존 제품 찾아서 교체
                    for i, p in enumerate(products):
                        if p.get('product_id') == product_id:
                            products[i] = {
                                'product_id': new_product.id,
                                'name': new_product.name,
                                'model_number': new_product.model_number,
                                'category': new_product.category,
                                'price': float(new_product.price),
                                'discount_price': float(new_product.discount_price) if new_product.discount_price else None,
                                'image_url': new_product.image_url or '',
                                'match_score': p.get('match_score', 80)
                            }
                            break
                    else:
                        return {
                            'success': False,
                            'error': f'포트폴리오에서 제품을 찾을 수 없습니다: {product_id}'
                        }
                
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'제품을 찾을 수 없습니다: {new_product_id}'
                    }
            
            elif action == 'upgrade':
                # 제품 업그레이드 (같은 카테고리의 상위 모델로 교체)
                if not product_id:
                    return {
                        'success': False,
                        'error': 'product_id 필수'
                    }
                
                # 기존 제품 찾기
                old_product_data = None
                for p in products:
                    if p.get('product_id') == product_id:
                        old_product_data = p
                        break
                
                if not old_product_data:
                    return {
                        'success': False,
                        'error': f'포트폴리오에서 제품을 찾을 수 없습니다: {product_id}'
                    }
                
                # 같은 카테고리의 더 비싼 제품 찾기
                try:
                    old_product = Product.objects.get(id=product_id)
                    category = old_product.category
                    
                    # 같은 카테고리의 더 비싼 제품 찾기
                    upgrade_candidates = Product.objects.filter(
                        category=category,
                        is_active=True,
                        price__gt=old_product.price
                    ).order_by('price')[:5]
                    
                    if not upgrade_candidates.exists():
                        return {
                            'success': False,
                            'error': '업그레이드 가능한 제품이 없습니다.'
                        }
                    
                    # 첫 번째 후보를 업그레이드 제품으로 선택
                    upgrade_product = upgrade_candidates.first()
                    
                    # 제품 교체
                    for i, p in enumerate(products):
                        if p.get('product_id') == product_id:
                            products[i] = {
                                'product_id': upgrade_product.id,
                                'name': upgrade_product.name,
                                'model_number': upgrade_product.model_number,
                                'category': upgrade_product.category,
                                'price': float(upgrade_product.price),
                                'discount_price': float(upgrade_product.discount_price) if upgrade_product.discount_price else None,
                                'image_url': upgrade_product.image_url or '',
                                'match_score': p.get('match_score', 80)
                            }
                            break
                
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'제품을 찾을 수 없습니다: {product_id}'
                    }
            
            else:
                return {
                    'success': False,
                    'error': f'지원하지 않는 작업: {action}'
                }
            
            # 가격 재계산
            total_price = sum(p.get('price', 0) for p in products)
            total_discount_price = sum(
                p.get('discount_price') or p.get('price', 0) for p in products
            )
            
            # 포트폴리오 업데이트
            portfolio.products = products
            portfolio.total_original_price = total_price
            portfolio.total_discount_price = total_discount_price
            portfolio.save()
            
            return {
                'success': True,
                'portfolio_id': portfolio.portfolio_id,
                'products': products,
                'total_price': total_price,
                'total_discount_price': total_discount_price
            }
        
        except Portfolio.DoesNotExist:
            return {
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Portfolio Edit Error] {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def calculate_estimated_price(
        portfolio_id: str,
        options: dict = None
    ) -> dict:
        """
        실시간 견적 계산 (옵션별 가격 계산)
        
        Args:
            portfolio_id: 포트폴리오 ID
            options: 옵션 정보
                {
                    "product_id": {
                        "installation": true,  # 설치 옵션
                        "warranty": "extended",  # 보증 옵션
                        "accessories": ["stand", "wall_mount"]  # 액세서리
                }
            }
            
        Returns:
            {
                "success": True,
                "base_price": 0,
                "options_price": 0,
                "total_price": 0,
                "breakdown": [...]
            }
        """
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            products = portfolio.products or []
            
            base_price = portfolio.total_discount_price or portfolio.total_original_price
            options_price = 0
            breakdown = []
            
            # 옵션별 가격 계산 (모의 구현)
            if options:
                option_prices = {
                    'installation': 50000,  # 설치비
                    'warranty_extended': 100000,  # 연장 보증
                    'warranty_premium': 200000,  # 프리미엄 보증
                    'stand': 50000,  # 스탠드
                    'wall_mount': 80000,  # 벽걸이
                    'cable': 20000,  # 케이블
                }
                
                for product_id_str, product_options in options.items():
                    try:
                        product_id = int(product_id_str)
                        product_data = next(
                            (p for p in products if p.get('product_id') == product_id),
                            None
                        )
                        
                        if not product_data:
                            continue
                        
                        product_options_price = 0
                        product_breakdown = []
                        
                        # 설치 옵션
                        if product_options.get('installation'):
                            price = option_prices.get('installation', 0)
                            product_options_price += price
                            product_breakdown.append({
                                'item': f"{product_data.get('name')} 설치",
                                'price': price
                            })
                        
                        # 보증 옵션
                        warranty = product_options.get('warranty')
                        if warranty:
                            key = f'warranty_{warranty}'
                            price = option_prices.get(key, 0)
                            if price > 0:
                                product_options_price += price
                                product_breakdown.append({
                                    'item': f"{product_data.get('name')} 보증 ({warranty})",
                                    'price': price
                                })
                        
                        # 액세서리
                        accessories = product_options.get('accessories', [])
                        for accessory in accessories:
                            price = option_prices.get(accessory, 0)
                            if price > 0:
                                product_options_price += price
                                product_breakdown.append({
                                    'item': f"{product_data.get('name')} {accessory}",
                                    'price': price
                                })
                        
                        options_price += product_options_price
                        breakdown.extend(product_breakdown)
                    
                    except (ValueError, TypeError):
                        continue
            
            total_price = base_price + options_price
            
            return {
                'success': True,
                'base_price': base_price,
                'options_price': options_price,
                'total_price': total_price,
                'breakdown': breakdown
            }
        
        except Portfolio.DoesNotExist:
            return {
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }
        except Exception as e:
            print(f"[Price Calculation Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _convert_portfolio_id_to_num(portfolio_id_str: str) -> int:
        """
        포트폴리오 ID 문자열을 숫자로 변환
        
        Args:
            portfolio_id_str: 포트폴리오 ID 문자열 (예: "PF-001", "PF-TEST01")
            
        Returns:
            숫자로 변환된 포트폴리오 ID
        """
        try:
            # "PF-001" -> 1 또는 직접 숫자 추출
            if portfolio_id_str.startswith('PF-'):
                portfolio_id_num = int(portfolio_id_str.replace('PF-', ''))
            else:
                # 숫자만 추출 시도
                import re
                numbers = re.findall(r'\d+', portfolio_id_str)
                portfolio_id_num = int(numbers[0]) if numbers else abs(hash(portfolio_id_str)) % 1000000
            return portfolio_id_num
        except:
            # 실패 시 해시값 사용
            return abs(hash(portfolio_id_str)) % 1000000

    @staticmethod
    def save_portfolio_to_oracle(portfolio_data: dict) -> dict:
        """
        PORTFOLIO 테이블에 포트폴리오 기본 정보 저장
        
        Args:
            portfolio_data: 포트폴리오 데이터 딕셔너리
                {
                    'portfolio_id': 'PF-001',
                    'internal_key': 'PF-001',
                    'user_id': 'user_123',
                    'style_type': 'modern',
                    'style_title': '모던 & 미니멀 스타일',
                    'style_subtitle': '당신의 라이프스타일에 맞춰 구성했어요.',
                    'total_original_price': 5000000,
                    'total_discount_price': 4500000,
                    'match_score': 85,
                    'status': 'draft'
                }
                
        Returns:
            {
                'success': True/False,
                'portfolio_id': 숫자 ID,
                'error': 에러 메시지 (실패 시)
            }
        """
        from api.db.oracle_client import get_connection
        
        try:
            portfolio_id_str = portfolio_data.get('portfolio_id') or portfolio_data.get('internal_key')
            if not portfolio_id_str:
                return {
                    'success': False,
                    'error': 'portfolio_id 또는 internal_key가 필요합니다.'
                }
            
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id_str)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PORTFOLIO 테이블 MERGE (INSERT 또는 UPDATE)
                    cur.execute("""
                        MERGE INTO PORTFOLIO p
                        USING (SELECT :portfolio_id AS PORTFOLIO_ID FROM DUAL) d
                        ON (p.PORTFOLIO_ID = d.PORTFOLIO_ID)
                        WHEN MATCHED THEN
                            UPDATE SET
                                INTERNAL_KEY = :internal_key,
                                USER_ID = :user_id,
                                STYLE_TYPE = :style_type,
                                STYLE_TITLE = :style_title,
                                STYLE_SUBTITLE = :style_subtitle,
                                TOTAL_ORIGINAL_PRICE = :total_original_price,
                                TOTAL_DISCOUNT_PRICE = :total_discount_price,
                                MATCH_SCORE = :match_score,
                                STATUS = :status,
                                UPDATED_AT = SYSDATE
                        WHEN NOT MATCHED THEN
                            INSERT (
                                PORTFOLIO_ID, INTERNAL_KEY, USER_ID, STYLE_TYPE, STYLE_TITLE, STYLE_SUBTITLE,
                                TOTAL_ORIGINAL_PRICE, TOTAL_DISCOUNT_PRICE, MATCH_SCORE, STATUS, CREATED_AT, UPDATED_AT
                            ) VALUES (
                                :portfolio_id, :internal_key, :user_id, :style_type, :style_title, :style_subtitle,
                                :total_original_price, :total_discount_price, :match_score, :status, SYSDATE, SYSDATE
                            )
                    """, {
                        'portfolio_id': portfolio_id_num,
                        'internal_key': portfolio_data.get('internal_key') or portfolio_id_str,
                        'user_id': portfolio_data.get('user_id'),
                        'style_type': portfolio_data.get('style_type', 'modern'),
                        'style_title': portfolio_data.get('style_title') or '',
                        'style_subtitle': portfolio_data.get('style_subtitle') or '',
                        'total_original_price': int(portfolio_data.get('total_original_price', 0)),
                        'total_discount_price': int(portfolio_data.get('total_discount_price', 0)),
                        'match_score': portfolio_data.get('match_score', 0),
                        'status': portfolio_data.get('status', 'draft')
                    })
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'portfolio_id': portfolio_id_num
                    }
                    
        except Exception as e:
            print(f"[save_portfolio_to_oracle] 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def save_portfolio_products_to_oracle(portfolio_id: str, products: list) -> dict:
        """
        PORTFOLIO_PRODUCT 테이블에 포트폴리오 제품 목록 저장
        
        Args:
            portfolio_id: 포트폴리오 ID 문자열 (예: "PF-001")
            products: 제품 리스트
                [
                    {'product_id': 101, 'priority': 1, 'recommend_reason': '추천 이유 1'},
                    {'product_id': 102, 'priority': 2, 'recommend_reason': '추천 이유 2'},
                ]
                
        Returns:
            {
                'success': True/False,
                'saved_count': 저장된 제품 수,
                'error': 에러 메시지 (실패 시)
            }
        """
        from api.db.oracle_client import get_connection
        
        try:
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 기존 제품 삭제 (재추천 시)
                    cur.execute("DELETE FROM PORTFOLIO_PRODUCT WHERE PORTFOLIO_ID = :portfolio_id", {
                        'portfolio_id': portfolio_id_num
                    })
                    
                    saved_count = 0
                    # 제품별로 저장
                    for product in products:
                        product_id = product.get('product_id') or product.get('id')
                        if not product_id:
                            continue
                        
                        # ID 시퀀스 조회 또는 자동 생성
                        cur.execute("""
                            SELECT NVL(MAX(ID), 0) + 1 FROM PORTFOLIO_PRODUCT
                        """)
                        next_id = cur.fetchone()[0]
                        
                        cur.execute("""
                            INSERT INTO PORTFOLIO_PRODUCT (
                                ID, PORTFOLIO_ID, PRODUCT_ID, PRIORITY, RECOMMEND_REASON
                            ) VALUES (
                                :id, :portfolio_id, :product_id, :priority, :recommend_reason
                            )
                        """, {
                            'id': next_id,
                            'portfolio_id': portfolio_id_num,
                            'product_id': int(product_id),
                            'priority': product.get('priority', saved_count + 1),
                            'recommend_reason': product.get('recommend_reason') or product.get('reason') or ''
                        })
                        
                        saved_count += 1
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'saved_count': saved_count
                    }
                    
        except Exception as e:
            print(f"[save_portfolio_products_to_oracle] 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def save_portfolio_session_to_oracle(portfolio_id: str, session_id: str, member_id: str = None) -> dict:
        """
        PORTFOLIO_SESSION 테이블에 포트폴리오-세션 연결 저장
        
        Args:
            portfolio_id: 포트폴리오 ID 문자열 (예: "PF-001")
            session_id: 세션 ID
            member_id: 회원 ID (선택적)
                
        Returns:
            {
                'success': True/False,
                'error': 에러 메시지 (실패 시)
            }
        """
        from api.db.oracle_client import get_connection
        
        try:
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PORTFOLIO_SESSION 테이블 MERGE (UPSERT)
                    cur.execute("""
                        MERGE INTO PORTFOLIO_SESSION ps
                        USING (SELECT :portfolio_id AS PORTFOLIO_ID FROM DUAL) d
                        ON (ps.PORTFOLIO_ID = d.PORTFOLIO_ID)
                        WHEN MATCHED THEN
                            UPDATE SET
                                MEMBER_ID = :member_id,
                                SESSION_ID = :session_id,
                                CREATED_AT = SYSDATE
                        WHEN NOT MATCHED THEN
                            INSERT (PORTFOLIO_ID, MEMBER_ID, SESSION_ID, CREATED_AT)
                            VALUES (:portfolio_id, :member_id, :session_id, SYSDATE)
                    """, {
                        'portfolio_id': portfolio_id_num,
                        'member_id': member_id,
                        'session_id': session_id
                    })
                    
                    conn.commit()
                    
                    return {
                        'success': True
                    }
                    
        except Exception as e:
            print(f"[save_portfolio_session_to_oracle] 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def _save_portfolio_to_oracle(portfolio, session_id: str, member_id: str = None, recommendations: list = None):
        """
        포트폴리오를 Oracle DB에 저장 (통합 함수 - 모든 테이블을 하나의 트랜잭션으로 처리)
        
        Args:
            portfolio: Portfolio Django 모델 인스턴스 또는 포트폴리오 데이터 딕셔너리
            session_id: 온보딩 세션 ID
            member_id: 회원 ID (선택적)
            recommendations: 추천 제품 리스트
            
        Returns:
            {
                'success': True/False,
                'portfolio_id': 숫자 ID,
                'error': 에러 메시지 (실패 시)
            }
        """
        from api.db.oracle_client import get_connection
        
        try:
            # Django 모델 인스턴스인 경우 딕셔너리로 변환
            if hasattr(portfolio, 'portfolio_id'):
                portfolio_data = {
                    'portfolio_id': portfolio.portfolio_id,
                    'internal_key': portfolio.internal_key or portfolio.portfolio_id,
                    'user_id': portfolio.user_id,
                    'style_type': portfolio.style_type,
                    'style_title': portfolio.style_title,
                    'style_subtitle': portfolio.style_subtitle,
                    'total_original_price': portfolio.total_original_price,
                    'total_discount_price': portfolio.total_discount_price,
                    'match_score': portfolio.match_score,
                    'status': portfolio.status
                }
                products = recommendations or portfolio.products or []
            else:
                portfolio_data = portfolio
                products = recommendations or portfolio_data.get('products', [])
            
            portfolio_id_str = portfolio_data.get('portfolio_id') or portfolio_data.get('internal_key')
            if not portfolio_id_str:
                return {
                    'success': False,
                    'error': 'portfolio_id 또는 internal_key가 필요합니다.'
                }
            
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id_str)
            
            # 모든 테이블 저장을 하나의 트랜잭션으로 처리
            with get_connection() as conn:
                try:
                    with conn.cursor() as cur:
                        # 1. PORTFOLIO 테이블 저장
                        cur.execute("""
                            MERGE INTO PORTFOLIO p
                            USING (SELECT :portfolio_id AS PORTFOLIO_ID FROM DUAL) d
                            ON (p.PORTFOLIO_ID = d.PORTFOLIO_ID)
                            WHEN MATCHED THEN
                                UPDATE SET
                                    INTERNAL_KEY = :internal_key,
                                    USER_ID = :user_id,
                                    STYLE_TYPE = :style_type,
                                    STYLE_TITLE = :style_title,
                                    STYLE_SUBTITLE = :style_subtitle,
                                    TOTAL_ORIGINAL_PRICE = :total_original_price,
                                    TOTAL_DISCOUNT_PRICE = :total_discount_price,
                                    MATCH_SCORE = :match_score,
                                    STATUS = :status,
                                    UPDATED_AT = SYSDATE
                            WHEN NOT MATCHED THEN
                                INSERT (
                                    PORTFOLIO_ID, INTERNAL_KEY, USER_ID, STYLE_TYPE, STYLE_TITLE, STYLE_SUBTITLE,
                                    TOTAL_ORIGINAL_PRICE, TOTAL_DISCOUNT_PRICE, MATCH_SCORE, STATUS, CREATED_AT, UPDATED_AT
                                ) VALUES (
                                    :portfolio_id, :internal_key, :user_id, :style_type, :style_title, :style_subtitle,
                                    :total_original_price, :total_discount_price, :match_score, :status, SYSDATE, SYSDATE
                                )
                        """, {
                            'portfolio_id': portfolio_id_num,
                            'internal_key': portfolio_data.get('internal_key') or portfolio_id_str,
                            'user_id': portfolio_data.get('user_id'),
                            'style_type': portfolio_data.get('style_type', 'modern'),
                            'style_title': portfolio_data.get('style_title') or '',
                            'style_subtitle': portfolio_data.get('style_subtitle') or '',
                            'total_original_price': int(portfolio_data.get('total_original_price', 0)),
                            'total_discount_price': int(portfolio_data.get('total_discount_price', 0)),
                            'match_score': portfolio_data.get('match_score', 0),
                            'status': portfolio_data.get('status', 'draft')
                        })
                        
                        # 2. PORTFOLIO_PRODUCT 테이블 저장
                        if products:
                            # 기존 제품 삭제
                            cur.execute("DELETE FROM PORTFOLIO_PRODUCT WHERE PORTFOLIO_ID = :portfolio_id", {
                                'portfolio_id': portfolio_id_num
                            })
                            
                            # 제품별로 저장
                            for idx, product in enumerate(products, start=1):
                                product_id = product.get('product_id') or product.get('id')
                                if not product_id:
                                    continue
                                
                                # ID 시퀀스 조회 또는 자동 생성
                                cur.execute("""
                                    SELECT NVL(MAX(ID), 0) + 1 FROM PORTFOLIO_PRODUCT
                                """)
                                next_id = cur.fetchone()[0]
                                
                                cur.execute("""
                                    INSERT INTO PORTFOLIO_PRODUCT (
                                        ID, PORTFOLIO_ID, PRODUCT_ID, PRIORITY, RECOMMEND_REASON
                                    ) VALUES (
                                        :id, :portfolio_id, :product_id, :priority, :recommend_reason
                                    )
                                """, {
                                    'id': next_id,
                                    'portfolio_id': portfolio_id_num,
                                    'product_id': int(product_id),
                                    'priority': product.get('priority', idx),
                                    'recommend_reason': product.get('recommend_reason') or product.get('reason') or ''
                                })
                        
                        # 3. PORTFOLIO_SESSION 테이블 저장
                        cur.execute("""
                            MERGE INTO PORTFOLIO_SESSION ps
                            USING (SELECT :portfolio_id AS PORTFOLIO_ID FROM DUAL) d
                            ON (ps.PORTFOLIO_ID = d.PORTFOLIO_ID)
                            WHEN MATCHED THEN
                                UPDATE SET
                                    MEMBER_ID = :member_id,
                                    SESSION_ID = :session_id,
                                    CREATED_AT = SYSDATE
                            WHEN NOT MATCHED THEN
                                INSERT (PORTFOLIO_ID, MEMBER_ID, SESSION_ID, CREATED_AT)
                                VALUES (:portfolio_id, :member_id, :session_id, SYSDATE)
                        """, {
                            'portfolio_id': portfolio_id_num,
                            'member_id': member_id,
                            'session_id': session_id
                        })
                    
                    # 모든 작업 성공 시 커밋
                    conn.commit()
                    
                    return {
                        'success': True,
                        'portfolio_id': portfolio_id_num
                    }
                    
                except Exception as e:
                    # 에러 발생 시 롤백
                    conn.rollback()
                    raise e
                    
        except Exception as e:
            print(f"[_save_portfolio_to_oracle] 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


    @staticmethod
    def get_portfolio_from_oracle(portfolio_id: str) -> Optional[dict]:
        """
        Oracle DB에서 포트폴리오 조회
        
        Args:
            portfolio_id: 포트폴리오 ID 문자열 (예: "PF-001")
            
        Returns:
            포트폴리오 데이터 딕셔너리 또는 None
        """
        from api.db.oracle_client import fetch_one, get_connection
        
        try:
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            PORTFOLIO_ID, INTERNAL_KEY, USER_ID, STYLE_TYPE, 
                            STYLE_TITLE, STYLE_SUBTITLE, TOTAL_ORIGINAL_PRICE, 
                            TOTAL_DISCOUNT_PRICE, MATCH_SCORE, STATUS, CREATED_AT, UPDATED_AT
                        FROM PORTFOLIO
                        WHERE PORTFOLIO_ID = :portfolio_id
                    """, {'portfolio_id': portfolio_id_num})
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                    
                    return {
                        'portfolio_id': row[0],
                        'internal_key': row[1],
                        'user_id': row[2],
                        'style_type': row[3],
                        'style_title': row[4],
                        'style_subtitle': row[5],
                        'total_original_price': row[6],
                        'total_discount_price': row[7],
                        'match_score': row[8],
                        'status': row[9],
                        'created_at': row[10],
                        'updated_at': row[11]
                    }
        except Exception as e:
            print(f"[get_portfolio_from_oracle] 오류: {e}")
            return None

    @staticmethod
    def get_portfolio_products_from_oracle(portfolio_id: str) -> List[dict]:
        """
        Oracle DB에서 포트폴리오 제품 목록 조회
        
        Args:
            portfolio_id: 포트폴리오 ID 문자열 (예: "PF-001")
            
        Returns:
            제품 목록 리스트
        """
        from api.db.oracle_client import get_connection
        
        try:
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            ID, PORTFOLIO_ID, PRODUCT_ID, PRIORITY, RECOMMEND_REASON
                        FROM PORTFOLIO_PRODUCT
                        WHERE PORTFOLIO_ID = :portfolio_id
                        ORDER BY PRIORITY
                    """, {'portfolio_id': portfolio_id_num})
                    
                    products = []
                    for row in cur.fetchall():
                        products.append({
                            'id': row[0],
                            'portfolio_id': row[1],
                            'product_id': row[2],
                            'priority': row[3],
                            'recommend_reason': row[4]
                        })
                    
                    return products
        except Exception as e:
            print(f"[get_portfolio_products_from_oracle] 오류: {e}")
            return []

    @staticmethod
    def get_portfolio_session_from_oracle(portfolio_id: str) -> Optional[dict]:
        """
        Oracle DB에서 포트폴리오-세션 연결 조회
        
        Args:
            portfolio_id: 포트폴리오 ID 문자열 (예: "PF-001")
            
        Returns:
            세션 연결 데이터 딕셔너리 또는 None
        """
        from api.db.oracle_client import get_connection
        
        try:
            portfolio_id_num = PortfolioService._convert_portfolio_id_to_num(portfolio_id)
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            PORTFOLIO_ID, SESSION_ID, MEMBER_ID, CREATED_AT
                        FROM PORTFOLIO_SESSION
                        WHERE PORTFOLIO_ID = :portfolio_id
                    """, {'portfolio_id': portfolio_id_num})
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                    
                    return {
                        'portfolio_id': row[0],
                        'session_id': row[1],
                        'member_id': row[2],
                        'created_at': row[3]
                    }
        except Exception as e:
            print(f"[get_portfolio_session_from_oracle] 오류: {e}")
            return None


# Singleton 인스턴스
portfolio_service = PortfolioService()

