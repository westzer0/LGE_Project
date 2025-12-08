# 백엔드 로직 검증 목표

## 🎯 검증하고 싶은 것

### 1. 카테고리 매칭 정확도
**문제**: TV 카테고리에 냉장고가 추천되는 버그
**검증 내용**:
- TV MAIN_CATEGORY → TV/Audio 제품만 추천되는가?
- 냉장고 MAIN_CATEGORY → KITCHEN 제품만 추천되는가?
- 각 MAIN_CATEGORY가 독립적으로 필터링되는가? (KITCHEN과 LIVING이 묶이지 않는가?)

**검증 방법**:
- 각 MAIN_CATEGORY별로 추천 결과 확인
- MAIN_CATEGORY와 product_type이 일치하는지 확인
- 잘못된 카테고리 추천이 있는지 확인

---

### 2. 저예산 대가족 Fallback 로직
**문제**: 저예산 대가족(4인 이상)에게 추천이 0개
**검증 내용**:
- 예산이 'low'이고 가구수가 4인 이상일 때 예산 범위가 확대되는가?
- 확대 후에도 추천이 나오는가?

**검증 방법**:
- 저예산 대가족 시나리오 테스트
- 예산 확대 전/후 추천 개수 비교

---

### 3. Taste ID null 처리
**문제**: taste_id가 null일 때 실패율이 높음
**검증 내용**:
- taste_id가 null일 때도 정상 작동하는가?
- calculate_product_score (일반 스코어링)이 사용되는가?

**검증 방법**:
- taste_id null 시나리오 테스트
- taste_id 있을 때와 없을 때 성공률 비교

---

### 4. 각 MAIN_CATEGORY 독립 필터링
**문제**: KITCHEN과 LIVING이 묶여서 필터링됨
**검증 내용**:
- 각 MAIN_CATEGORY별로 `_filter_products`가 개별 호출되는가?
- KITCHEN과 LIVING이 서로 영향을 주지 않는가?

**검증 방법**:
- KITCHEN만 선택했을 때 KITCHEN 제품만 나오는지
- LIVING만 선택했을 때 LIVING 제품만 나오는지
- 둘 다 선택했을 때 각각 독립적으로 추천되는지

---

### 5. PRD 시뮬레이션 정확도
**검증 내용**:
- 1000명 가상 고객 데이터로 시뮬레이션이 정상 작동하는가?
- 추천 성공률이 높은가? (목표: 90% 이상)
- 카테고리별로 올바른 추천이 나오는가?

**검증 방법**:
- `simulate_prd_flow.py` 실행
- 리포트에서 성공률, 카테고리 분포 확인

---

## 📊 검증 지표

1. **추천 성공률**: 90% 이상 목표
2. **카테고리 매칭 정확도**: 100% (잘못된 카테고리 추천 0개)
3. **저예산 대가족 추천률**: 0개 추천이 발생하지 않아야 함
4. **Taste ID null 성공률**: 80% 이상
5. **카테고리 독립성**: KITCHEN과 LIVING이 서로 영향을 주지 않음

---

## 🔍 검증 방법

### 자동 검증 스크립트
```bash
# PRD 시뮬레이션 실행
python simulate_prd_flow.py

# 결과 시각화
python visualize_verification_results.py
```

### 수동 검증
1. 각 MAIN_CATEGORY별로 테스트 케이스 실행
2. 로그에서 카테고리 필터링 확인
3. 추천 결과에서 MAIN_CATEGORY와 product_type 일치 확인

---

## ✅ 수정 완료된 항목

1. ✅ 카테고리 필터링 강화 (MAIN_CATEGORY와 product_type 매칭)
2. ✅ 저예산 대가족 fallback 로직 추가
3. ✅ 각 MAIN_CATEGORY 독립 필터링 (KITCHEN과 LIVING 분리)
4. ✅ category_mapping.py 생성 (올바른 카테고리 매핑)

---

## ⚠️ 검증 필요 항목

1. ⚠️ 실제 시뮬레이션 결과 확인 (현재 Django ORM 연결 오류로 추천 실패)
2. ⚠️ 카테고리 매칭 정확도 실제 테스트
3. ⚠️ Taste ID null 처리 실제 테스트




