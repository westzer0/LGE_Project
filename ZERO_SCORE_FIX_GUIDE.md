# TASTE_CONFIG 0점 컬럼 문제 해결 가이드

## 문제 요약

Oracle DB의 `TASTE_CONFIG` 테이블에서 일부 SCORE 컬럼이 모든 레코드(taste_id 1-120)에서 0점인 문제가 있었습니다.

## 원인 분석

### 1. 카테고리명 불일치
- Oracle DB의 실제 카테고리명과 점수 계산 로직에서 사용하는 카테고리명이 다름
- 예: Oracle DB `세탁` → 로직 `세탁기`
- 예: Oracle DB `광파오븐전자레인지` → 로직 `전자레인지`

### 2. Oracle DB에 존재하지 않는 카테고리
- `건조기`, `워시타워`, `로봇청소기`, `사운드바` 등은 Oracle DB에 별도 카테고리로 존재하지 않음
- 다른 카테고리로 통합되어 있거나 존재하지 않음

### 3. 브랜드 라인 (OBJET, SIGNATURE)
- `OBJET`, `SIGNATURE`는 MAIN_CATEGORY가 아닌 브랜드 라인
- 실제 제품의 MAIN_CATEGORY는 `TV`, `냉장고` 등

## 해결 방법

### 1. 점수 계산 로직 수정

**파일**: `api/management/commands/populate_taste_config.py`

#### 변경 사항:
1. Oracle DB에 없는 카테고리도 점수 계산하도록 수정
   - `_save_to_oracle` 메서드에서 `TasteCategorySelector._calculate_category_score` 직접 호출
   - Oracle DB에 없는 카테고리(`건조기`, `워시타워`, `로봇청소기`, `사운드바` 등)도 점수 계산

2. OBJET, SIGNATURE 점수 부여
   - 예산 수준에 따라 10-20점 부여
   - `high/premium/luxury`: 20점
   - `medium`: 15점
   - `low`: 10점

3. `all_category_scores`에 추가 카테고리 포함
   - Oracle DB에 없지만 컬럼이 존재하는 카테고리도 점수 계산하여 포함

### 2. 점수 재계산

모든 taste_id (1-120)에 대해 점수를 재계산해야 합니다.

```bash
# 방법 1: populate_taste_config 명령 사용 (권장)
python manage.py populate_taste_config --taste-range 1-120 --force

# 방법 2: fix_zero_score_columns 명령 사용
python manage.py fix_zero_score_columns --recalculate
```

### 3. 해결 불가능한 컬럼 삭제

`OBJET_SCORE`, `SIGNATURE_SCORE`는 브랜드 라인이므로 삭제할 수 있습니다.

```bash
python manage.py fix_zero_score_columns --delete
```

또는 수동으로 SQL 실행:
```sql
ALTER TABLE TASTE_CONFIG DROP COLUMN OBJET_SCORE;
ALTER TABLE TASTE_CONFIG DROP COLUMN SIGNATURE_SCORE;
```

## 사용 가능한 명령어

### 1. analyze_and_fix_zero_scores
0점 컬럼을 분석하고 원인을 파악합니다.

```bash
python manage.py analyze_and_fix_zero_scores --analyze-only
```

### 2. fix_zero_score_columns
점수 재계산 및 컬럼 삭제를 수행합니다.

```bash
# 점수 재계산만
python manage.py fix_zero_score_columns --recalculate

# 컬럼 삭제만
python manage.py fix_zero_score_columns --delete

# 모두 실행
python manage.py fix_zero_score_columns --all
```

### 3. populate_taste_config
모든 taste에 대해 점수를 재계산합니다.

```bash
# 모든 taste (1-120) 강제 재계산
python manage.py populate_taste_config --taste-range 1-120 --force
```

## 예상 결과

### 해결 가능한 컬럼 (점수 재계산 후 점수 부여)
- `세탁기_SCORE`: Oracle DB `세탁` → 로직 `세탁기` 매핑으로 점수 부여
- `전자레인지_SCORE`: Oracle DB `광파오븐전자레인지` → 로직 `전자레인지` 매핑으로 점수 부여
- `오븐_SCORE`: Oracle DB `광파오븐` → 로직 `오븐` 매핑으로 점수 부여
- `건조기_SCORE`: Oracle DB에 없지만 점수 계산 로직으로 점수 부여
- `워시타워_SCORE`: Oracle DB에 없지만 점수 계산 로직으로 점수 부여
- `로봇청소기_SCORE`: `청소기_SCORE`와 통합되어 점수 부여
- `사운드바_SCORE`: Oracle DB `오디오` → `사운드바_SCORE` 매핑으로 점수 부여
- `의류관리기_SCORE`: 점수 계산 로직 보정으로 점수 부여

### 해결 불가능한 컬럼 (삭제 권장)
- `OBJET_SCORE`: 브랜드 라인 (삭제 또는 별도 처리 필요)
- `SIGNATURE_SCORE`: 브랜드 라인 (삭제 또는 별도 처리 필요)

## 주의사항

1. **데이터 백업**: 점수 재계산 전에 Oracle DB 백업 권장
2. **실행 시간**: 모든 taste_id (1-120) 재계산은 시간이 걸릴 수 있음
3. **컬럼 삭제**: `OBJET_SCORE`, `SIGNATURE_SCORE` 삭제는 되돌릴 수 없으므로 신중히 결정

## 검증

점수 재계산 후 다음 쿼리로 확인:

```sql
-- 각 SCORE 컬럼별로 0점이 아닌 레코드 수 확인
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN TV_SCORE > 0 THEN 1 ELSE 0 END) as tv_score_count,
    SUM(CASE WHEN "세탁기_SCORE" > 0 THEN 1 ELSE 0 END) as 세탁기_score_count,
    SUM(CASE WHEN "전자레인지_SCORE" > 0 THEN 1 ELSE 0 END) as 전자레인지_score_count,
    SUM(CASE WHEN "건조기_SCORE" > 0 THEN 1 ELSE 0 END) as 건조기_score_count,
    SUM(CASE WHEN "워시타워_SCORE" > 0 THEN 1 ELSE 0 END) as 워시타워_score_count,
    SUM(CASE WHEN "의류관리기_SCORE" > 0 THEN 1 ELSE 0 END) as 의류관리기_score_count
FROM TASTE_CONFIG;
```

## 참고 파일

- `ZERO_SCORE_ANALYSIS_REPORT.md`: 상세 분석 보고서
- `api/management/commands/analyze_and_fix_zero_scores.py`: 분석 스크립트
- `api/management/commands/fix_zero_score_columns.py`: 해결 스크립트
- `api/management/commands/populate_taste_config.py`: 점수 재계산 스크립트

