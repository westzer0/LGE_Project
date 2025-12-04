# 추천 엔진 리팩토링 계획

## 목표
기존 제품 타입별 추천 로직을 MAIN CATEGORY별 추천 로직으로 완전히 교체

## 현재 문제점

1. **중복된 로직**
   - `recommendation_engine.py`: 제품 타입별 그룹화 (세탁기, 냉장고 등)
   - `taste_based_recommendation_engine.py`: MAIN CATEGORY별 그룹화 (TV, KITCHEN, LIVING 등)
   - 둘 다 "그룹화해서 3개씩 선택"하는 동일한 패턴

2. **사용되지 않는 코드**
   - `recommendation_engine.py`의 제품 타입별 로직
   - `_score_products_by_type()` 메서드
   - `_get_product_type_multiplier()` 메서드

3. **혼란스러운 구조**
   - views.py에서 `recommendation_engine` 사용 중
   - 새로운 `taste_based_recommendation_engine`은 사용 안 함

## 리팩토링 계획

### 1단계: recommendation_engine.py 단순화
- 제품 타입별 그룹화 로직 제거
- MAIN CATEGORY별 추천으로 변경
- `taste_based_recommendation_engine`의 로직을 `recommendation_engine`에 통합

### 2단계: views.py 수정
- `taste_based_recommendation_engine` 사용하도록 변경
- 또는 `recommendation_engine`이 이미 MAIN CATEGORY 방식이면 그대로 사용

### 3단계: 사용되지 않는 코드 삭제
- `_score_products_by_type()` 삭제
- `_get_product_type_multiplier()` 삭제
- `get_recommendations()`의 제품 타입별 그룹화 부분 제거

### 4단계: taste_based_recommendation_engine.py 처리
- `recommendation_engine.py`에 통합했으면 삭제
- 또는 별도 엔진으로 유지 (선택적)

## 주의사항

- `product_type_classifier.py`는 다른 엔진에서도 사용 중이므로 삭제하지 않음
- `playbook_recommendation_engine.py`, `column_based_recommendation_engine.py`는 유지

