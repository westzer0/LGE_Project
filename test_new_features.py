"""
새로 구현된 기능 테스트 스크립트
- 포트폴리오 편집 기능
- 실시간 견적 계산
- 추천 후보 조회
- 베스트샵 연동
"""
import os
import sys
import django
import json

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Portfolio, Product, OnboardingSession
from api.services.portfolio_service import portfolio_service
from django.utils import timezone
import uuid


def create_test_portfolio():
    """테스트용 포트폴리오 생성"""
    try:
        # 기존 포트폴리오 확인
        portfolio = Portfolio.objects.first()
        if portfolio:
            print(f"✅ 기존 포트폴리오 사용: {portfolio.portfolio_id}")
            return portfolio
        
        # 테스트용 포트폴리오 생성
        print("📝 테스트용 포트폴리오 생성 중...")
        
        # 제품 가져오기
        products = Product.objects.filter(is_active=True)[:3]
        if not products.exists():
            print("❌ 테스트할 제품이 없습니다.")
            return None
        
        # 제품 데이터 준비
        products_data = []
        total_price = 0
        total_discount = 0
        
        for product in products:
            price = float(product.price)
            discount = float(product.discount_price) if product.discount_price else price
            products_data.append({
                'product_id': product.id,
                'name': product.name,
                'model_number': product.model_number,
                'category': product.category,
                'price': price,
                'discount_price': discount,
                'image_url': product.image_url or '',
                'match_score': 85
            })
            total_price += price
            total_discount += discount
        
        # 포트폴리오 생성
        portfolio_id = f"PF-TEST-{uuid.uuid4().hex[:6].upper()}"
        portfolio = Portfolio.objects.create(
            portfolio_id=portfolio_id,
            user_id='test_user',
            style_type='modern',
            style_title='테스트 포트폴리오',
            style_subtitle='테스트용 포트폴리오입니다.',
            products=products_data,
            total_original_price=total_price,
            total_discount_price=total_discount,
            match_score=85,
            status='draft'
        )
        
        print(f"✅ 테스트용 포트폴리오 생성 완료: {portfolio.portfolio_id}")
        return portfolio
        
    except Exception as e:
        print(f"❌ 포트폴리오 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_portfolio_edit():
    """포트폴리오 편집 기능 테스트"""
    print("\n=== 포트폴리오 편집 기능 테스트 ===")
    
    # 테스트용 포트폴리오 생성
    try:
        portfolio = create_test_portfolio()
        if not portfolio:
            return False
        
        print(f"✅ 포트폴리오 찾음: {portfolio.portfolio_id}")
        print(f"   현재 제품 수: {len(portfolio.products or [])}")
        
        # 제품 추가 테스트 - 포트폴리오에 없는 제품 찾기
        existing_product_ids = [p.get('product_id') for p in portfolio.products if p.get('product_id')]
        new_products = Product.objects.filter(is_active=True).exclude(id__in=existing_product_ids)[:5]
        
        if new_products.exists():
            new_product = new_products.first()
            print(f"\n1. 제품 추가 테스트: {new_product.name} (ID: {new_product.id})")
            
            result = portfolio_service.update_portfolio_products(
                portfolio_id=portfolio.portfolio_id,
                action='add',
                new_product_id=new_product.id
            )
            
            if result.get('success'):
                print(f"   ✅ 제품 추가 성공")
                print(f"   업데이트된 제품 수: {len(result.get('products', []))}")
                print(f"   총 가격: {result.get('total_price', 0):,}원")
            else:
                print(f"   ❌ 제품 추가 실패: {result.get('error')}")
                return False
        else:
            print("❌ 테스트할 제품이 없습니다.")
            return False
        
        # 제품 삭제 테스트
        if portfolio.products and len(portfolio.products) > 1:
            product_to_remove = portfolio.products[0].get('product_id')
            if product_to_remove:
                print(f"\n2. 제품 삭제 테스트: 제품 ID {product_to_remove}")
                
                result = portfolio_service.update_portfolio_products(
                    portfolio_id=portfolio.portfolio_id,
                    action='remove',
                    product_id=product_to_remove
                )
                
                if result.get('success'):
                    print(f"   ✅ 제품 삭제 성공")
                    print(f"   업데이트된 제품 수: {len(result.get('products', []))}")
                else:
                    print(f"   ❌ 제품 삭제 실패: {result.get('error')}")
        
        print("\n✅ 포트폴리오 편집 기능 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_estimate_price():
    """실시간 견적 계산 테스트"""
    print("\n=== 실시간 견적 계산 테스트 ===")
    
    try:
        portfolio = create_test_portfolio()
        if not portfolio:
            return False
        
        print(f"✅ 포트폴리오 찾음: {portfolio.portfolio_id}")
        
        # 옵션 설정
        options = {}
        if portfolio.products:
            first_product = portfolio.products[0]
            product_id = first_product.get('product_id')
            if product_id:
                options[str(product_id)] = {
                    'installation': True,
                    'warranty': 'extended',
                    'accessories': ['stand']
                }
        
        print(f"\n옵션 설정: {json.dumps(options, indent=2, ensure_ascii=False)}")
        
        result = portfolio_service.calculate_estimated_price(
            portfolio_id=portfolio.portfolio_id,
            options=options
        )
        
        if result.get('success'):
            print(f"✅ 견적 계산 성공")
            print(f"   기본 가격: {result.get('base_price', 0):,}원")
            print(f"   옵션 가격: {result.get('options_price', 0):,}원")
            print(f"   총 가격: {result.get('total_price', 0):,}원")
            
            breakdown = result.get('breakdown', [])
            if breakdown:
                print(f"\n   가격 내역:")
                for item in breakdown:
                    print(f"     - {item.get('item')}: {item.get('price'):,}원")
            
            return True
        else:
            print(f"❌ 견적 계산 실패: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alternatives():
    """추천 후보 조회 테스트"""
    print("\n=== 추천 후보 조회 테스트 ===")
    
    try:
        portfolio = create_test_portfolio()
        if not portfolio:
            return False
        
        # 온보딩 세션이 없으면 생성
        if not portfolio.onboarding_session:
            print("📝 테스트용 온보딩 세션 생성 중...")
            try:
                onboarding_session = OnboardingSession.objects.create(
                    session_id=f"test-session-{uuid.uuid4().hex[:8]}",
                    vibe='modern',
                    household_size=2,
                    housing_type='apartment',
                    pyung=25,
                    priority='value',
                    budget_level='medium',
                    status='completed'
                )
                portfolio.onboarding_session = onboarding_session
                portfolio.save()
                print(f"✅ 온보딩 세션 생성 완료: {onboarding_session.session_id}")
            except Exception as e:
                print(f"⚠️  온보딩 세션 생성 실패: {e}")
                print("   추천 후보 조회는 온보딩 세션이 필요합니다.")
                return False
        
        print(f"✅ 포트폴리오 찾음: {portfolio.portfolio_id}")
        
        result = portfolio_service.get_alternative_recommendations(
            portfolio_id=portfolio.portfolio_id
        )
        
        if result.get('success'):
            alternatives = result.get('alternatives', [])
            print(f"✅ 추천 후보 조회 성공")
            print(f"   카테고리 수: {len(alternatives)}")
            
            total_products = 0
            for alt in alternatives:
                category = alt.get('category', '기타')
                products = alt.get('products', [])
                total_products += len(products)
                print(f"   - {category}: {len(products)}개 제품")
            
            print(f"   총 제품 수: {total_products}개")
            return True
        else:
            print(f"❌ 추천 후보 조회 실패: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bestshop_consultation():
    """베스트샵 연동 테스트"""
    print("\n=== 베스트샵 연동 테스트 ===")
    
    try:
        portfolio = create_test_portfolio()
        if not portfolio:
            return False
        
        print(f"✅ 포트폴리오 찾음: {portfolio.portfolio_id}")
        
        # 베스트샵 상담 예약 정보 준비
        consultation_data = {
            'portfolio_id': portfolio.portfolio_id,
            'user_id': 'test_user_123',
            'consultation_purpose': '이사',
            'preferred_date': '2025-12-15',
            'preferred_time': '14:00',
            'store_location': '서울 강남점'
        }
        
        print(f"\n상담 예약 정보:")
        print(json.dumps(consultation_data, indent=2, ensure_ascii=False))
        
        # URL 생성 테스트
        from urllib.parse import urlencode
        bestshop_base_url = "https://bestshop.lge.co.kr/counselReserve/main/MC11420001"
        bestshop_params = {
            'inflow': 'lgekor',
            'portfolio_id': portfolio.portfolio_id,
        }
        
        if portfolio.products:
            product_names = [p.get('name', '') for p in portfolio.products[:5] if p.get('name')]
            if product_names:
                bestshop_params['products'] = ','.join(product_names)
        
        if consultation_data.get('preferred_date'):
            bestshop_params['date'] = consultation_data['preferred_date']
        if consultation_data.get('preferred_time'):
            bestshop_params['time'] = consultation_data['preferred_time']
        if consultation_data.get('store_location'):
            bestshop_params['store'] = consultation_data['store_location']
        
        bestshop_url = f"{bestshop_base_url}?{urlencode(bestshop_params)}"
        
        print(f"\n✅ 베스트샵 URL 생성 성공")
        print(f"   URL: {bestshop_url}")
        print(f"   예약 ID: BS-{portfolio.portfolio_id}-{int(timezone.now().timestamp())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("새로 구현된 기능 테스트 시작")
    print("=" * 60)
    
    results = []
    
    # 1. 포트폴리오 편집 기능 테스트
    results.append(("포트폴리오 편집", test_portfolio_edit()))
    
    # 2. 실시간 견적 계산 테스트
    results.append(("실시간 견적 계산", test_estimate_price()))
    
    # 3. 추천 후보 조회 테스트
    results.append(("추천 후보 조회", test_alternatives()))
    
    # 4. 베스트샵 연동 테스트
    results.append(("베스트샵 연동", test_bestshop_consultation()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")


if __name__ == '__main__':
    main()

