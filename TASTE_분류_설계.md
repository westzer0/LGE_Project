# TASTE 분류 설계 문서

## 개요

온보딩 데이터(약 10,000개 조합)를 기반으로 사용자 취향(taste)을 구분하여 MEMBER 테이블에 저장합니다.

## Taste 개수 제안

### 분석
- **온보딩 조합 수**: 약 10,000개
- **제품 수**: 약 15,000개
- **목표**: 적절한 수의 taste로 구분하여 추천 정확도와 관리 효율성 균형

### 제안: **100-150개**

#### 근거
1. **통계적 관점**
   - 10,000개 조합 / 120개 taste = 평균 83개 조합 per taste
   - 15,000개 제품 / 120개 taste = 평균 125개 제품 per taste
   - 각 taste당 충분한 데이터 확보 가능

2. **실무적 관점**
   - 너무 적으면 (10개 이하): 구분이 모호함, 추천 정확도 낮음
   - 너무 많으면 (500개 이상): 관리 복잡, 오버피팅 위험, 유사한 taste가 분산됨
   - 100-150개: 충분한 세분화 + 관리 가능한 수준

3. **추천 시스템 관점**
   - Collaborative Filtering: 각 taste당 최소 50-100명의 사용자 필요
   - Content-Based Filtering: 각 taste당 충분한 제품 다양성 필요
   - 120개 taste면 각 taste당 평균 83명의 사용자, 125개 제품 → 충분함

### 최종 결정: **120개**

## 구현 방법

### 1. 해시 기반 분류

온보딩 데이터의 주요 속성을 조합하여 해시값을 생성하고, 이를 120개로 나눈 나머지 + 1로 taste_id를 계산합니다.

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

**계산 공식:**
```
taste_key = f"{vibe}|{household_range}|{housing_type}|{pyung_range}|{budget_level}|{priority_str}|{main_space_str}|{pet}|{cooking}|{laundry}|{media}"
taste_hash = MD5(taste_key)
taste_id = (taste_hash % 120) + 1
```

### 2. 장점
- **일관성**: 같은 온보딩 데이터는 항상 같은 taste_id 생성
- **균등 분산**: 해시 기반으로 120개 taste에 균등하게 분산
- **빠른 계산**: 실시간 계산 가능
- **확장성**: 나중에 taste 개수 조정 가능

### 3. 단점 및 보완
- **유사한 취향 분리**: 해시 특성상 유사한 취향이 다른 taste로 분류될 수 있음
- **보완**: 나중에 클러스터링 기반으로 개선 가능

## 데이터베이스 구조

### MEMBER 테이블
```sql
ALTER TABLE MEMBER ADD (TASTE NUMBER(10));
```

- **TASTE**: 취향 ID (1 ~ 120)
- NULL 허용 (온보딩 완료 전에는 NULL)

## 사용 시나리오

1. **온보딩 완료 시**
   - 온보딩 데이터 수집
   - taste_id 계산
   - MEMBER 테이블에 저장

2. **추천 요청 시**
   - MEMBER 테이블에서 taste 조회
   - taste_id 기반 추천 로직 적용

3. **taste별 통계 분석**
   - taste_id별 사용자 수
   - taste_id별 선호 제품
   - taste_id별 추천 정확도

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

