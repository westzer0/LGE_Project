"""
빠른 기능 테스트 스크립트

사용법:
    python quick_test.py

이 스크립트는 주요 API 엔드포인트가 정상적으로 동작하는지 확인합니다.
"""

import os
import sys
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json

def test_api_endpoint(client, method, url, data=None, expected_status=200):
    """API 엔드포인트 테스트 헬퍼 함수"""
    try:
        if method == 'GET':
            response = client.get(url)
        elif method == 'POST':
            response = client.post(url, json.dumps(data), content_type='application/json')
        else:
            print(f"❌ 지원하지 않는 HTTP 메서드: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {url} - 성공 (상태 코드: {response.status_code})")
            return True
        else:
            print(f"❌ {method} {url} - 실패 (예상: {expected_status}, 실제: {response.status_code})")
            try:
                print(f"   응답: {response.json()}")
            except:
                print(f"   응답: {response.content[:200]}")
            return False
    except Exception as e:
        print(f"❌ {method} {url} - 오류: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("프론트엔드 기능 테스트 시작")
    print("=" * 60)
    print()
    
    client = Client()
    results = []
    
    # 1. 페이지 로드 테스트
    print("📄 페이지 로드 테스트")
    print("-" * 60)
    results.append(("메인 페이지", test_api_endpoint(client, 'GET', '/')))
    results.append(("온보딩 페이지", test_api_endpoint(client, 'GET', '/onboarding/')))
    results.append(("결과 페이지", test_api_endpoint(client, 'GET', '/result/')))
    print()
    
    # 2. API 엔드포인트 테스트
    print("🔌 API 엔드포인트 테스트")
    print("-" * 60)
    
    # 제품 목록 조회
    results.append(("제품 목록 조회", test_api_endpoint(client, 'GET', '/api/products/')))
    
    # 장바구니 목록 조회 (user_id 필요)
    results.append(("장바구니 목록 조회", test_api_endpoint(
        client, 'GET', '/api/cart/list/?user_id=test_user', expected_status=200
    )))
    
    # 포트폴리오 목록 조회 (user_id 필요)
    results.append(("포트폴리오 목록 조회", test_api_endpoint(
        client, 'GET', '/api/portfolio/list/?user_id=test_user', expected_status=200
    )))
    
    # AI 상태 확인
    results.append(("AI 상태 확인", test_api_endpoint(client, 'GET', '/api/ai/status/')))
    print()
    
    # 3. 결과 요약
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} - {name}")
    
    print()
    print(f"총 {total}개 테스트 중 {passed}개 통과 ({passed*100//total}%)")
    print()
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패. 위의 오류 메시지를 확인하세요.")
    
    print()
    print("=" * 60)
    print("수동 테스트 가이드")
    print("=" * 60)
    print()
    print("1. 서버 실행: python manage.py runserver")
    print("2. 브라우저에서 http://localhost:8000 접속")
    print("3. 온보딩 설문 완료 후 결과 페이지에서 기능 테스트")
    print()
    print("주요 테스트 항목:")
    print("  - 포트폴리오 편집: 결과 페이지의 '편집' 버튼 클릭")
    print("  - 장바구니: 헤더의 장바구니 아이콘 클릭")
    print("  - 포트폴리오 목록: /portfolios/ 접속")
    print()
    print("자세한 내용은 TESTING_GUIDE.md를 참고하세요.")

if __name__ == '__main__':
    main()

