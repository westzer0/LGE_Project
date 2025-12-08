# Oracle DB 문제 해결 가이드

## 현재 발생하는 문제

### 1. `ORA-00942: table or view does not exist`
**원인**: Django 모델의 테이블이 Oracle DB에 존재하지 않음

**Django 모델 테이블 이름 규칙**:
- `Product` 모델 → `API_PRODUCT` 테이블 (대문자, 앱 이름 접두사)
- `ProductSpec` 모델 → `API_PRODUCTSPEC` 테이블

**Oracle DB에 실제로 존재하는 테이블**:
- `PRODUCT` (대문자, 앱 이름 없음)
- `PRODUCT_SPEC` (언더스코어 구분)

### 2. 해결 방법

#### 방법 1: Django 모델에 테이블 이름 명시 (권장)

```python
class Product(models.Model):
    # ... 필드 정의 ...
    
    class Meta:
        db_table = 'PRODUCT'  # Oracle DB 테이블 이름 명시
        verbose_name = '제품'
        verbose_name_plural = '제품'
```

#### 방법 2: Oracle DB에 Django 테이블 생성

```bash
# 마이그레이션 실행
python manage.py makemigrations
python manage.py migrate
```

#### 방법 3: 테스트에서 모킹 데이터 사용 (현재 구현됨)

테스트 스크립트에서 DB 조회 실패 시 모킹 데이터로 테스트 진행

## 테이블 이름 확인 방법

### Oracle DB에서 테이블 목록 확인

```sql
-- 현재 사용자의 모든 테이블 확인
SELECT table_name FROM user_tables ORDER BY table_name;

-- 특정 테이블 확인
SELECT table_name FROM user_tables WHERE table_name LIKE '%PRODUCT%';
```

### Django에서 테이블 이름 확인

```python
from api.models import Product
print(Product._meta.db_table)  # 'API_PRODUCT' 또는 설정된 이름
```

## 현재 상태

### 성공한 테스트
- ✅ TASTE 문자열 파싱 (정수형 처리 포함)
- ✅ 벡터화
- ✅ 코사인 유사도 계산
- ✅ 점수 등급 부여

### 실패한 테스트 (DB 의존)
- ⚠️ 제품 피처 추출 (모킹 데이터로 대체 가능)
- ⚠️ TASTE 문자열 기반 추천 (테이블 없음)
- ⚠️ MEMBER_ID 기반 추천 (테이블 없음)

## 권장 조치

1. **Django 마이그레이션 실행**: Oracle DB에 테이블 생성
2. **테이블 이름 확인**: Oracle DB의 실제 테이블 이름 확인
3. **모델 수정**: `db_table` 옵션으로 테이블 이름 명시
4. **테스트 개선**: 모킹 데이터로 핵심 로직 테스트

## 테스트 실행 옵션

### 옵션 1: SQLite로 전환 (테스트용)

`config/settings.py`에서 임시로 SQLite 사용:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### 옵션 2: 모킹 데이터 사용 (현재 구현)

테스트 스크립트가 자동으로 모킹 데이터 사용

### 옵션 3: Oracle DB 테이블 생성

```bash
python manage.py migrate
```

## 참고

- Django 모델은 기본적으로 `앱이름_모델이름` 형식으로 테이블 생성
- Oracle DB는 대문자로 테이블 이름 저장
- `db_table` 옵션으로 커스텀 테이블 이름 지정 가능

