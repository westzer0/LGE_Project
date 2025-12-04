# 제품 데이터 확인 방법

## 방법 1: Django Shell (가장 간단)

```bash
python manage.py shell
```

그 다음 아래 코드를 복사-붙여넣기:

```python
from api.models import Product
from django.db.models import Count

# 전체 제품 수
print(f"전체 제품: {Product.objects.count()}개")

# 카테고리별 통계
print("\n카테고리별 제품 수:")
for category_code, category_label in Product.CATEGORY_CHOICES:
    count = Product.objects.filter(category=category_code).count()
    if count > 0:
        print(f"  {category_label} ({category_code}): {count}개")

# 최신 제품 10개
print("\n최신 제품 10개:")
for product in Product.objects.all()[:10]:
    print(f"  - {product.name} ({product.model_number}) - {product.get_category_display()}")

# 특정 카테고리 제품 보기
print("\nTV 제품 목록:")
for product in Product.objects.filter(category='TV')[:10]:
    print(f"  - {product.name} ({product.model_number}) - {product.price:,}원")
```

## 방법 2: Django Admin 페이지 (웹 UI)

```bash
python manage.py runserver
```

브라우저에서 접속:
```
http://127.0.0.1:8000/admin/
```

- 로그인 후 "제품" 메뉴 클릭
- 검색, 필터링, 정렬 가능
- 제품 클릭하면 상세 정보 및 스펙 확인 가능

## 방법 3: API 엔드포인트

```bash
# 전체 제품 리스트
curl http://127.0.0.1:8000/api/products/

# TV 카테고리만
curl http://127.0.0.1:8000/api/products/?category=TV
```

또는 브라우저에서:
```
http://127.0.0.1:8000/api/products/
http://127.0.0.1:8000/api/products/?category=TV
```

## 방법 4: 커맨드로 확인

```bash
python manage.py check_data
```

이 명령어는 제품 수, 카테고리별 통계, 샘플 데이터를 출력합니다.

