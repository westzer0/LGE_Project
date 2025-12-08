# 테스트 문제 해결 가이드

## Oracle DB 연결 오류

### 문제: `TypeError: connect() got an unexpected keyword argument 'threaded'`

**원인**: oracledb 라이브러리 최신 버전에서는 `threaded` 파라미터가 제거되었습니다.

**해결 방법**:

1. **settings.py 수정** (이미 수정됨)
   ```python
   # "OPTIONS": {
   #     "threaded": True,  # 제거 또는 주석 처리
   # },
   ```

2. **테스트 스크립트 예외 처리** (이미 수정됨)
   - DB 연결 오류 시 테스트를 계속 진행하도록 예외 처리 추가
   - 제품 데이터가 없을 때 메시지 출력

## 테스트 실행 방법

### 기본 테스트
```bash
python test_content_based_filtering.py
```

### 특정 테스트만 실행
테스트 스크립트의 `main()` 함수를 수정하여 원하는 테스트만 실행:

```python
def main():
    test_taste_parsing()  # 이 테스트만 실행
    # test_product_feature_extraction()  # 주석 처리
```

## DB 연결 없이 테스트하는 방법

### 방법 1: SQLite 사용 (임시)
settings.py에서 SQLite로 전환:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### 방법 2: 모킹 사용
테스트에서 실제 DB 조회를 스킵하고 모킹 데이터 사용:

```python
from unittest.mock import patch, MagicMock

@patch('api.models.Product.objects')
def test_product_feature_extraction(mock_products):
    # 모킹 데이터
    mock_product = MagicMock()
    mock_product.name = "LG OLED TV"
    mock_product.category = "TV"
    mock_product.spec = None
    mock_products.filter.return_value = [mock_product]
    
    # 테스트 실행
    ...
```

## 일반적인 오류 해결

### 1. TASTE 정수형 오류
- ✅ 이미 수정됨: `parse_taste_string()` 함수에서 정수형 처리

### 2. 추천 결과 0개
- `min_score` 파라미터를 낮춤 (예: 0.1)
- 제품 피처 추출 로직 강화 (이미 완료)

### 3. 제품 데이터 없음
- Django DB에 제품 데이터가 있는지 확인
- Oracle DB 연결이 정상인지 확인

## 테스트 결과 해석

### 성공적인 테스트 출력 예시:
```
=== TASTE 문자열 파싱 테스트 ===
  '미니멀,모던,빈티지' (str) -> ['미니멀', '모던', '빈티지']
  ✅ 정상

=== 제품 피처 추출 테스트 ===
제품: LG OLED TV
  추출된 피처: ['TV', 'OLED', '4K', '스마트']
  ✅ 정상
```

### 오류 발생 시:
```
=== 제품 피처 추출 테스트 ===
  제품 피처 추출 테스트 실패: ...
  (Oracle DB 연결 문제일 수 있습니다. SQLite로 전환하거나 DB 연결을 확인하세요.)
  ⚠️ DB 연결 문제 - 테스트는 계속 진행됨
```

## 다음 단계

1. Oracle DB 연결 문제 해결
2. 제품 데이터 확인 및 추가
3. TASTE 데이터 형식 확인 (문자열 권장)
4. 추천 결과 검증

