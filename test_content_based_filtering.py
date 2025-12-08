"""
콘텐츠 기반 필터링 테스트 스크립트

사용법:
    # SQLite 사용 (권장 - Oracle 11g 호환성 문제 해결)
    USE_SQLITE_FOR_TESTING=true python test_content_based_filtering.py
    
    # 또는 Oracle DB 사용 (테이블이 있는 경우)
    python test_content_based_filtering.py
"""
import os
import sys
import django

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# SQLite 사용 여부 확인 (환경 변수로 제어)
use_sqlite = os.environ.get('USE_SQLITE_FOR_TESTING', 'False').lower() == 'true'
if use_sqlite:
    print("[테스트] SQLite 모드로 실행합니다 (Oracle 11g 호환성 문제 해결)")
    os.environ.setdefault('USE_SQLITE_FOR_TESTING', 'True')
else:
    print("[테스트] Oracle DB 모드로 실행합니다 (테이블이 없으면 오류 발생 가능)")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.content_based_filtering import content_based_filtering
from api.models import Product


def test_taste_parsing():
    """TASTE 문자열 파싱 테스트 (정수형 처리 포함)"""
    print("\n=== TASTE 문자열 파싱 테스트 ===")
    
    test_cases = [
        "미니멀,모던,빈티지",
        "럭셔리,프리미엄",
        "내추럴,우드톤,화이트톤",
        "",
        "단일태그",
        123,  # 정수형 테스트
        1.5,  # 실수형 테스트
        None,  # None 테스트
    ]
    
    for taste_value in test_cases:
        tags = content_based_filtering.parse_taste_string(taste_value)
        print(f"  {repr(taste_value)} ({type(taste_value).__name__}) -> {tags}")


def test_product_feature_extraction():
    """제품 피처 추출 테스트"""
    print("\n=== 제품 피처 추출 테스트 ===")
    
    try:
        # Oracle DB 호환: 전체 조회 후 Python에서 슬라이싱
        try:
            all_products = list(Product.objects.filter(is_active=True, spec__isnull=False))
            products = all_products[:3]  # 최대 3개만
        except Exception as db_error:
            # 테이블이 없거나 조회 실패 시 모킹 데이터 사용
            print(f"  DB 조회 실패: {db_error}")
            print("  모킹 데이터로 테스트 진행...")
            
            # 모킹 Product 객체 생성
            from unittest.mock import MagicMock
            mock_product = MagicMock()
            mock_product.name = "LG OLED TV 55인치"
            mock_product.category = "TV"
            mock_product.spec = None
            
            mock_spec = MagicMock()
            mock_spec.spec_json = '{"MAIN_CATEGORY": "TV", "SUB_CATEGORY": "OLED", "COLOR": "블랙", "SIZE": 55}'
            mock_product.spec = mock_spec
            
            products = [mock_product]
        
        if not products:
            print("  제품 데이터가 없습니다. (DB 연결 문제 또는 데이터 없음)")
            return
        
        for product in products:
            print(f"\n제품: {product.name}")
            spec = product.spec if hasattr(product, 'spec') else None
            features = content_based_filtering.extract_product_features(product, spec)
            print(f"  추출된 피처: {features}")
    except Exception as e:
        print(f"  제품 피처 추출 테스트 실패: {e}")
        print("  (Oracle DB 연결 문제일 수 있습니다. SQLite로 전환하거나 DB 연결을 확인하세요.)")
        import traceback
        print(f"  상세 오류:\n{traceback.format_exc()}")


def test_vectorization():
    """벡터화 테스트"""
    print("\n=== 벡터화 테스트 ===")
    
    taste_tags = ["미니멀", "모던", "빈티지"]
    product_features = ["TV", "OLED", "4K", "스마트"]
    
    taste_vector = content_based_filtering.text_to_vector(taste_tags)
    product_vector = content_based_filtering.text_to_vector(product_features)
    
    print(f"  TASTE 태그: {taste_tags}")
    print(f"  TASTE 벡터 (0이 아닌 인덱스): {[i for i, v in enumerate(taste_vector) if v > 0]}")
    print(f"  제품 피처: {product_features}")
    print(f"  제품 벡터 (0이 아닌 인덱스): {[i for i, v in enumerate(product_vector) if v > 0]}")


def test_cosine_similarity():
    """코사인 유사도 테스트"""
    print("\n=== 코사인 유사도 테스트 ===")
    
    # 테스트 케이스 1: 완전히 일치
    vec1 = content_based_filtering.text_to_vector(["미니멀", "모던"])
    vec2 = content_based_filtering.text_to_vector(["미니멀", "모던"])
    similarity1 = content_based_filtering.cosine_similarity(vec1, vec2)
    print(f"  완전 일치: {similarity1:.3f} (예상: 1.000)")
    
    # 테스트 케이스 2: 부분 일치
    vec3 = content_based_filtering.text_to_vector(["미니멀", "모던", "빈티지"])
    vec4 = content_based_filtering.text_to_vector(["미니멀", "모던", "럭셔리"])
    similarity2 = content_based_filtering.cosine_similarity(vec3, vec4)
    print(f"  부분 일치: {similarity2:.3f} (예상: 0.667)")
    
    # 테스트 케이스 3: 불일치
    vec5 = content_based_filtering.text_to_vector(["미니멀", "모던"])
    vec6 = content_based_filtering.text_to_vector(["럭셔리", "프리미엄"])
    similarity3 = content_based_filtering.cosine_similarity(vec5, vec6)
    print(f"  불일치: {similarity3:.3f} (예상: 0.000)")


def test_score_labeling():
    """점수 등급 부여 테스트"""
    print("\n=== 점수 등급 부여 테스트 ===")
    
    test_scores = [0.95, 0.75, 0.55, 0.35, 0.15]
    
    for score in test_scores:
        label = content_based_filtering.get_score_label(score)
        print(f"  점수 {score:.2f} -> 등급 {label}")


def test_recommendations_by_taste_string():
    """TASTE 문자열 기반 추천 테스트"""
    print("\n=== TASTE 문자열 기반 추천 테스트 ===")
    
    try:
        taste_str = "미니멀,모던,화이트톤"
        print(f"  TASTE: {taste_str}")
        
        result = content_based_filtering.get_recommendations_by_taste_string(
            taste_str=taste_str,
            limit=5,
            min_score=0.1  # 최소 점수 낮춤
        )
        
        if result['success']:
            print(f"  추천 개수: {result['count']}")
            print(f"  점수 분포: {result['score_distribution']}")
            if result['recommendations']:
                print("\n  추천 제품:")
                for i, rec in enumerate(result['recommendations'][:5], 1):
                    print(f"    {i}. {rec['name']} (점수: {rec['score']:.3f}, 등급: {rec['label']})")
            else:
                print("  추천 제품이 없습니다. (제품 데이터가 없거나 매칭되는 제품이 없음)")
        else:
            print(f"  오류: {result.get('message', '알 수 없는 오류')}")
    except Exception as e:
        print(f"  추천 테스트 실패: {e}")
        print("  (DB 연결 문제일 수 있습니다.)")


def test_recommendations_by_member_id():
    """MEMBER_ID 기반 추천 테스트"""
    print("\n=== MEMBER_ID 기반 추천 테스트 ===")
    
    # Oracle DB에서 첫 번째 MEMBER 가져오기
    from api.db.oracle_client import fetch_all_dict
    
    try:
        members = fetch_all_dict("SELECT MEMBER_ID, TASTE FROM MEMBER WHERE ROWNUM <= 1")
        
        if members:
            member_id = members[0]['MEMBER_ID']
            taste = members[0].get('TASTE', '')
            print(f"  MEMBER_ID: {member_id}")
            print(f"  TASTE: {taste} (타입: {type(taste).__name__})")
            
            result = content_based_filtering.get_recommendations_by_taste(
                member_id=member_id,
                limit=5,
                min_score=0.1  # 최소 점수 낮춤
            )
            
            if result['success']:
                print(f"  추천 개수: {result['count']}")
                print(f"  점수 분포: {result['score_distribution']}")
                if result['recommendations']:
                    print("\n  추천 제품:")
                    for i, rec in enumerate(result['recommendations'][:5], 1):
                        print(f"    {i}. {rec['name']} (점수: {rec['score']:.3f}, 등급: {rec['label']})")
                else:
                    print("  추천 제품이 없습니다. (제품 데이터가 없거나 매칭되는 제품이 없음)")
            else:
                print(f"  오류: {result.get('message', '알 수 없는 오류')}")
        else:
            print("  MEMBER 테이블에 데이터가 없습니다.")
    except Exception as e:
        print(f"  Oracle DB 연결 실패: {e}")
        print("  (Oracle DB가 설정되지 않았거나 연결 문제가 있을 수 있습니다)")
        import traceback
        print(f"  상세 오류:\n{traceback.format_exc()}")


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("콘텐츠 기반 필터링 테스트")
    print("=" * 60)
    
    # 기본 테스트
    test_taste_parsing()
    test_product_feature_extraction()
    test_vectorization()
    test_cosine_similarity()
    test_score_labeling()
    
    # 추천 테스트
    test_recommendations_by_taste_string()
    test_recommendations_by_member_id()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == '__main__':
    main()

