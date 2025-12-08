"""
Oracle 직접 연결 클라이언트 사용 예시
"""
from api.db import fetch_all, fetch_one, fetch_all_dict, fetch_one_dict, execute, execute_many


# ============================================================
# 1. SELECT 쿼리 - 모든 결과 가져오기
# ============================================================

def example_fetch_all():
    """모든 사용자 조회"""
    sql = "SELECT * FROM users"
    results = fetch_all(sql)
    for row in results:
        print(row)


def example_fetch_all_with_params():
    """파라미터를 사용한 조회"""
    sql = "SELECT * FROM users WHERE age > :age AND status = :status"
    params = {"age": 18, "status": "active"}
    results = fetch_all(sql, params)
    return results


# ============================================================
# 2. SELECT 쿼리 - 딕셔너리 형태로 결과 받기
# ============================================================

def example_fetch_all_dict():
    """딕셔너리 리스트로 결과 받기"""
    sql = "SELECT id, name, email FROM users"
    users = fetch_all_dict(sql)
    # 결과: [{"id": 1, "name": "홍길동", "email": "hong@example.com"}, ...]
    for user in users:
        print(f"{user['name']} ({user['email']})")


# ============================================================
# 3. SELECT 쿼리 - 단일 행 조회
# ============================================================

def example_fetch_one():
    """단일 사용자 조회"""
    sql = "SELECT * FROM users WHERE id = :id"
    params = {"id": 1}
    user = fetch_one(sql, params)
    if user:
        print(f"사용자: {user}")


def example_fetch_one_dict():
    """단일 사용자를 딕셔너리로 조회"""
    sql = "SELECT * FROM users WHERE email = :email"
    params = {"email": "test@example.com"}
    user = fetch_one_dict(sql, params)
    if user:
        print(f"이름: {user['name']}, 이메일: {user['email']}")


# ============================================================
# 4. INSERT 쿼리
# ============================================================

def example_insert():
    """새 사용자 추가"""
    sql = "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)"
    params = {
        "name": "홍길동",
        "email": "hong@example.com",
        "age": 30
    }
    rows_affected = execute(sql, params)
    print(f"{rows_affected}개 행이 추가되었습니다.")


# ============================================================
# 5. UPDATE 쿼리
# ============================================================

def example_update():
    """사용자 정보 업데이트"""
    sql = "UPDATE users SET name = :name, email = :email WHERE id = :id"
    params = {
        "id": 1,
        "name": "홍길동 (수정)",
        "email": "hong_updated@example.com"
    }
    rows_affected = execute(sql, params)
    print(f"{rows_affected}개 행이 업데이트되었습니다.")


# ============================================================
# 6. DELETE 쿼리
# ============================================================

def example_delete():
    """사용자 삭제"""
    sql = "DELETE FROM users WHERE id = :id"
    params = {"id": 1}
    rows_affected = execute(sql, params)
    print(f"{rows_affected}개 행이 삭제되었습니다.")


# ============================================================
# 7. 배치 처리 (여러 행 한 번에 추가)
# ============================================================

def example_batch_insert():
    """여러 사용자를 한 번에 추가"""
    sql = "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)"
    users = [
        {"name": "홍길동", "email": "hong@example.com", "age": 30},
        {"name": "김철수", "email": "kim@example.com", "age": 25},
        {"name": "이영희", "email": "lee@example.com", "age": 28},
    ]
    rows_affected = execute_many(sql, users)
    print(f"{rows_affected}개 행이 추가되었습니다.")


# ============================================================
# 8. Django View에서 사용 예시
# ============================================================

def django_view_example(request):
    """Django View에서 사용하는 예시"""
    from django.http import JsonResponse
    
    try:
        # Oracle에서 데이터 조회
        sql = "SELECT * FROM products WHERE category = :category"
        params = {"category": "전자제품"}
        products = fetch_all_dict(sql, params)
        
        # JSON 응답 반환
        return JsonResponse({"products": products})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================================================
# 9. 실제 사용 예시 (테이블이 있는 경우)
# ============================================================

def test_connection():
    """연결 테스트"""
    try:
        # 간단한 쿼리로 연결 확인
        result = fetch_one("SELECT USER, SYSDATE FROM DUAL")
        if result:
            print(f"✅ 연결 성공!")
            print(f"사용자: {result[0]}")
            print(f"서버 시간: {result[1]}")
            return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

if __name__ == "__main__":
    # 연결 테스트 실행
    test_connection()

