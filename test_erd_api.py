"""
ERD 기반 API 테스트 스크립트
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("=" * 50)
    print("ERD 기반 API 테스트 시작")
    print("=" * 50)
    
    # 서버가 시작될 때까지 대기
    print("\n1. 서버 연결 확인...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/api/health/", timeout=5)
        print(f"   ✅ 서버 연결 성공: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  서버 연결 실패: {e}")
        print("   서버가 시작될 때까지 기다리는 중...")
        time.sleep(5)
    
    # 2. 회원 목록 조회
    print("\n2. 회원 목록 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/members/", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 성공: {len(data.get('results', data))}개 회원")
        else:
            print(f"   응답: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️  오류: {e}")
    
    # 3. 온보딩 질문 조회
    print("\n3. 온보딩 질문 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/onboarding-questions/", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 성공: {len(data.get('results', data))}개 질문")
        else:
            print(f"   응답: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️  오류: {e}")
    
    # 4. Taste 설정 조회
    print("\n4. Taste 설정 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/taste-configs/", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 성공: {len(data.get('results', data))}개 Taste 설정")
        else:
            print(f"   응답: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️  오류: {e}")
    
    # 5. 제품 목록 조회 (기존 API)
    print("\n5. 제품 목록 조회 테스트 (기존 API)...")
    try:
        response = requests.get("http://localhost:8000/api/products/", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 성공: 제품 목록 조회됨")
        else:
            print(f"   응답: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️  오류: {e}")
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)
    print("\n📚 API 문서: ERD_BACKEND_API_DOCS.md 참고")
    print("🌐 API Base URL: http://localhost:8000/api/v1/")
    print("📊 Admin: http://localhost:8000/admin/")

if __name__ == "__main__":
    test_api_endpoints()
