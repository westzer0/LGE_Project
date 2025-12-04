# TASTE 분류 시스템 구현 완료

## 구현 내용

### 1. MEMBER 테이블에 TASTE 칼럼 추가
- **칼럼명**: `TASTE`
- **타입**: `NUMBER(10)`
- **NULL 허용**: 예 (온보딩 완료 전에는 NULL)

### 2. Taste 분류 로직 구현

#### 파일 위치
- `api/utils/taste_classifier.py`: Taste 계산 로직
- `api/services/taste_calculation_service.py`: Taste 계산 및 저장 서비스

#### Taste 개수
- **120개**로 설정
- 근거:
  - 온보딩 조합 10,000개 / 120개 taste = 평균 83개 조합 per taste
  - 제품 15,000개 / 120개 taste = 평균 125개 제품 per taste
  - 충분한 데이터 확보 가능

#### 계산 방법
온보딩 데이터의 주요 속성을 조합하여 해시값을 생성하고, 이를 120으로 나눈 나머지 + 1로 taste_id를 계산합니다.

**주요 속성:**
- vibe (4가지)
- household_size 범위 (4가지: 1인, 2인, 3-4인, 5인 이상)
- housing_type (4가지)
- pyung 범위 (7가지: 10이하, 11-15, 16-20, 21-30, 31-40, 41-50, 51이상)
- budget_level (3가지)
- priority 조합 (문자열)
- main_space 조합 (문자열)
- has_pet (2가지)
- cooking (3가지)
- laundry (3가지)
- media (4가지)

**특징:**
- ✅ 일관성: 같은 온보딩 데이터는 항상 같은 taste_id 생성
- ✅ 균등 분산: 해시 기반으로 120개 taste에 균등하게 분산
- ✅ 빠른 계산: 실시간 계산 가능

### 3. 온보딩 완료 시 자동 저장

`api/views.py`의 `onboarding_complete_view`에서:
1. 온보딩 데이터 수집
2. `taste_calculation_service.calculate_and_save_taste()` 호출
3. MEMBER 테이블에 taste_id 저장
4. 응답에 taste_id 포함

### 4. 사용 방법

#### 온보딩 완료 시 (자동)
```python
# api/views.py에서 자동으로 처리됨
# member_id가 있으면 자동으로 taste 계산 및 저장
```

#### 수동으로 taste 계산
```python
from api.services.taste_calculation_service import taste_calculation_service

# 온보딩 데이터로부터 taste 계산 및 저장
taste_id = taste_calculation_service.calculate_and_save_taste(
    member_id='user123',
    onboarding_data={
        'vibe': 'modern',
        'household_size': 2,
        'housing_type': 'apartment',
        'pyung': 30,
        'budget_level': 'medium',
        'priority': ['design', 'value'],
        'has_pet': False,
        'main_space': ['living'],
        'cooking': 'sometimes',
        'laundry': 'weekly',
        'media': 'balanced',
    }
)
```

#### 회원의 taste 조회
```python
from api.services.taste_calculation_service import taste_calculation_service

taste_id = taste_calculation_service.get_taste_for_member('user123')
```

## 테스트

`test_taste_calculation.py`로 테스트 가능:
```bash
python test_taste_calculation.py
```

## 향후 개선 방안

1. **클러스터링 기반 분류**
   - K-means 등으로 유사한 취향 그룹화
   - 더 정확한 taste 분류

2. **동적 taste 개수 조정**
   - 사용자 데이터 축적 후 최적 taste 개수 재계산
   - 현재는 120개로 고정, 나중에 조정 가능

3. **taste별 메타데이터**
   - 각 taste의 대표 속성 저장
   - taste별 설명/태그 추가

## 관련 파일

- `api/utils/taste_classifier.py`: Taste 계산 로직
- `api/services/taste_calculation_service.py`: Taste 계산 및 저장 서비스
- `api/views.py`: 온보딩 완료 시 taste 저장 로직
- `add_taste_column_to_member.py`: MEMBER 테이블에 TASTE 칼럼 추가 스크립트
- `test_taste_calculation.py`: 테스트 스크립트
- `TASTE_분류_설계.md`: 설계 문서

