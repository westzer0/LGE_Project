# 데이터 준비 진단 및 자동 입력 가이드

## 1. 현재 상태 진단

### Django Shell 진단 코드

터미널에서 다음 명령어를 실행하세요:

```bash
python manage.py shell
```

그 다음 아래 코드를 복사-붙여넣기:

```python
from api.models import Product, ProductSpec, UserSample
import json

# 1. Product 테이블 행 수 확인
product_count = Product.objects.count()
print(f"📦 Product 테이블: {product_count}개")

if product_count > 0:
    # 카테고리별 통계
    print("\n카테고리별 제품 수:")
    for category_code, category_name in Product.CATEGORY_CHOICES:
        count = Product.objects.filter(category=category_code).count()
        if count > 0:
            print(f"  - {category_name} ({category_code}): {count}개")
    
    # 샘플 제품 출력
    print("\n샘플 제품 (최신 5개):")
    for product in Product.objects.all()[:5]:
        print(f"  - {product.name} ({product.model_number}) - {product.get_category_display()}")
else:
    print("  ⚠️  제품 데이터가 없습니다.")

# 2. ProductSpec 데이터 샘플 3개 출력
spec_count = ProductSpec.objects.count()
print(f"\n📋 ProductSpec 테이블: {spec_count}개")

if spec_count > 0:
    print("\n샘플 ProductSpec (3개):")
    for spec in ProductSpec.objects.all()[:3]:
        try:
            spec_data = json.loads(spec.spec_json)
            print(f"  - Product ID: {spec.product_id}")
            print(f"    Source: {spec.source}")
            print(f"    Keys in spec_json: {len(spec_data)}개")
            print(f"    Sample keys: {list(spec_data.keys())[:5]}")
        except Exception as e:
            print(f"  - Product ID: {spec.product_id} (JSON 파싱 오류: {e})")
else:
    print("  ⚠️  스펙 데이터가 없습니다.")

# 3. UserSample 테이블 행 수 확인
user_count = UserSample.objects.count()
print(f"\n👥 UserSample 테이블: {user_count}개")

if user_count > 0:
    print("\n샘플 UserSample (3개):")
    for user in UserSample.objects.all()[:3]:
        print(f"  - User ID: {user.user_id}")
        print(f"    Household: {user.household_size}, Budget: {user.budget_range}")
else:
    print("  ⚠️  사용자 샘플 데이터가 없습니다.")

# 요약
print("\n=== 요약 ===")
print(f"총 제품: {product_count}개")
print(f"총 스펙: {spec_count}개")
print(f"총 사용자 샘플: {user_count}개")
```

또는 간단하게 커맨드로 실행:

```bash
python manage.py check_data
```

## 2. 마이그레이션 상태 확인

```bash
python manage.py showmigrations api
```

**예상 결과:**
```
api
 [X] 0001_initial
 [X] 0002_usersample_productspec
```

`[ ]` 표시가 있으면 미적용 마이그레이션이 있습니다.

**마이그레이션 적용:**
```bash
python manage.py migrate api
```

또는 전체 적용:
```bash
python manage.py migrate
```

## 3. CSV Import 자동화

### 방법 1: 개별 파일 Import

```bash
# 제품 스펙 CSV import
python manage.py import_specs --csv "data/TV_제품스펙.csv" --category TV
python manage.py import_specs --csv "data/오디오_제품스펙.csv" --category LIVING
python manage.py import_specs --csv "data/홈오디오_제품스펙.csv" --category LIVING
python manage.py import_specs --csv "data/스탠바이미_제품스펙.csv" --category TV
python manage.py import_specs --csv "data/프로젝터_제품스펙.csv" --category TV
python manage.py import_specs --csv "data/상업용 디스플레이_제품스펙.csv" --category TV

# 사용자 샘플 CSV import
python manage.py import_user_samples --csv "data/recommendation_dummy_data.csv"
```

### 방법 2: 자동화 스크립트 (권장)

```bash
# 모든 CSV 파일 자동 import
python manage.py import_all_data
```

**Dry-run 모드 (실제 저장 없이 테스트):**
```bash
python manage.py import_all_data --dry-run
```

**제한된 행 수로 테스트:**
```bash
python manage.py import_all_data --limit 10
```

## 4. 결과 검증 쿼리

Django shell에서 실행:

```python
from api.models import Product, ProductSpec

# 전체 제품 수
print(f"전체 제품: {Product.objects.count()}개")

# 카테고리별 제품 수
print(f"TV 제품: {Product.objects.filter(category='TV').count()}개")
print(f"주방가전: {Product.objects.filter(category='KITCHEN').count()}개")
print(f"생활가전: {Product.objects.filter(category='LIVING').count()}개")

# ProductSpec JSON 구조 확인
spec = ProductSpec.objects.first()
if spec:
    import json
    spec_data = json.loads(spec.spec_json)
    print(f"\n첫 번째 스펙의 키 개수: {len(spec_data)}개")
    print(f"샘플 키: {list(spec_data.keys())[:10]}")
```

**예상 결과:**
- 전체 제품: 100+ 개
- TV 제품: 20+ 개
- ProductSpec JSON 구조 정상

## 5. 전체 프로세스 (한 번에 실행)

```bash
# 1. 마이그레이션 확인 및 적용
python manage.py migrate

# 2. 데이터 상태 확인
python manage.py check_data

# 3. 모든 CSV 자동 import
python manage.py import_all_data

# 4. 다시 확인
python manage.py check_data
```

## 6. 문제 해결

### 문제: CSV 파일을 찾을 수 없음
- `data/` 폴더가 프로젝트 루트에 있는지 확인
- 경로를 절대 경로로 지정: `--csv "C:\Users\134\Desktop\DX Project\data\TV_제품스펙.csv"`

### 문제: 카테고리 오류
- `Product.CATEGORY_CHOICES`에 정의된 카테고리만 사용 가능
- 사용 가능한 카테고리: TV, KITCHEN, LIVING, AIR, AI, OBJET, SIGNATURE

### 문제: JSON 파싱 오류
- `ProductSpec.spec_json` 필드가 올바른 JSON 형식인지 확인
- CSV import 시 에러 메시지 확인

