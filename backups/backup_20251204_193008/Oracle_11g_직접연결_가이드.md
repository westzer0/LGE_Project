# Oracle 11g 직접 연결 가이드

## 🔍 문제 상황

- ✅ `test_oracle_thick.py`: Thick 모드로 Oracle 11g 연결 성공
- ❌ Django ORM: Oracle 11g를 지원하지 않음 (Oracle 19 이상만 지원)

**결론**: Django ORM을 사용하지 않고 `oracledb`를 직접 사용해야 합니다.

---

## ✅ 해결 방법

### Oracle 직접 연결 모듈 사용

`api/db/oracle_client.py` 모듈을 사용하여 Oracle에 직접 연결합니다.

---

## 📝 사용 방법

### 1. 기본 사용법

```python
from api.db import fetch_all, fetch_one, execute

# 모든 결과 조회
users = fetch_all("SELECT * FROM users")

# 단일 결과 조회
user = fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})

# INSERT/UPDATE/DELETE
execute("INSERT INTO users (name, email) VALUES (:name, :email)", 
        {"name": "홍길동", "email": "test@example.com"})
```

### 2. 딕셔너리 형태로 결과 받기

```python
from api.db import fetch_all_dict, fetch_one_dict

# 딕셔너리 리스트로 결과 받기
users = fetch_all_dict("SELECT * FROM users")
# [{"id": 1, "name": "홍길동", ...}, {"id": 2, "name": "김철수", ...}]

# 단일 딕셔너리로 결과 받기
user = fetch_one_dict("SELECT * FROM users WHERE id = :id", {"id": 1})
# {"id": 1, "name": "홍길동", "email": "hong@example.com"}
```

### 3. Django View에서 사용

```python
from django.http import JsonResponse
from api.db import fetch_all_dict

def get_products(request):
    """제품 목록 조회"""
    try:
        sql = "SELECT * FROM products WHERE category = :category"
        params = {"category": "전자제품"}
        products = fetch_all_dict(sql, params)
        return JsonResponse({"products": products})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
```

---

## 🔧 Django 설정 변경

### Oracle 설정 제거

`config/settings.py`에서 Oracle 설정을 제거하고 SQLite를 기본으로 사용:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**이미 변경 완료되었습니다!**

---

## 🧪 테스트

### 1. 연결 테스트

```powershell
python -c "from api.db import fetch_one; result = fetch_one('SELECT USER, SYSDATE FROM DUAL'); print('✅ 연결 성공!' if result else '❌ 연결 실패')"
```

### 2. 사용 예시 실행

```powershell
python api/db/사용_예시.py
```

---

## 📋 주요 함수

| 함수 | 설명 | 반환값 |
|------|------|--------|
| `fetch_all(sql, params)` | 모든 결과 조회 | 튜플 리스트 |
| `fetch_one(sql, params)` | 단일 결과 조회 | 튜플 또는 None |
| `fetch_all_dict(sql, params)` | 모든 결과를 딕셔너리로 | 딕셔너리 리스트 |
| `fetch_one_dict(sql, params)` | 단일 결과를 딕셔너리로 | 딕셔너리 또는 None |
| `execute(sql, params)` | INSERT/UPDATE/DELETE | 영향받은 행 수 |
| `execute_many(sql, params_list)` | 배치 처리 | 영향받은 총 행 수 |
| `get_connection()` | 연결 컨텍스트 매니저 | Connection 객체 |

---

## ⚠️ 주의사항

1. **Django ORM 사용 불가**: Oracle 11g는 Django ORM에서 사용할 수 없습니다
   - `from django.db import models` 사용 불가
   - Django 마이그레이션 사용 불가

2. **SQL 직접 작성**: 모든 쿼리를 SQL로 직접 작성해야 합니다

3. **트랜잭션 관리**: `execute()` 함수는 자동으로 커밋합니다
   - 수동 트랜잭션 관리가 필요하면 `get_connection()` 사용

---

## 💡 장점

- ✅ Oracle 11g 지원
- ✅ 추가 설정 불필요
- ✅ 빠른 개발 가능
- ✅ 완전한 SQL 제어

---

## 💡 단점

- ❌ Django ORM 사용 불가
- ❌ Django 마이그레이션 사용 불가
- ❌ SQL을 직접 작성해야 함

---

## 🔗 관련 파일

- `api/db/oracle_client.py` - Oracle 연결 클라이언트
- `api/db/사용_예시.py` - 사용 예시 코드
- `test_oracle_thick.py` - 연결 테스트 스크립트

