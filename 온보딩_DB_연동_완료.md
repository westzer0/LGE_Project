# 온보딩 Oracle DB 연동 완료

## 작업 개요

온보딩 질문, 선택지, 사용자 응답, 세션 정보를 Oracle DB에 저장하도록 구현 완료.

## 구현 내용

### 1. Oracle DB 테이블 구조 설계 및 DDL 작성

**파일**: `api/db/onboarding_tables_ddl.sql`

#### 테이블 구조

1. **ONBOARDING_QUESTION** (온보딩 질문 항목)
   - 질문 ID, 단계 번호, 질문 유형, 질문 텍스트
   - 조건부 질문 지원 (CONDITION_TYPE, CONDITION_VALUE)
   - 초기 데이터 포함 (6단계 모든 질문)

2. **ONBOARDING_ANSWER** (온보딩 선택지 항목)
   - 답변 ID, 질문 ID (FK), 답변 값, 답변 텍스트
   - 이미지 URL 지원
   - 초기 데이터 포함 (모든 선택지)

3. **ONBOARDING_SESSION** (온보딩 세션 별 선택지 결과 항목)
   - 세션 ID (PK), 사용자 ID
   - 현재 단계, 상태 (IN_PROGRESS, COMPLETED, ABANDONED)
   - Step 1~6 데이터 필드 (vibe, household_size, housing_type, pyung, priority, budget_level)
   - JSON 필드 (SELECTED_CATEGORIES, RECOMMENDED_PRODUCTS, RECOMMENDATION_RESULT)
   - 타임스탬프 (CREATED_AT, UPDATED_AT, COMPLETED_AT)

4. **ONBOARDING_USER_RESPONSE** (온보딩 사용자 선택지 결과 항목)
   - 응답 ID (PK), 세션 ID (FK), 질문 ID (FK), 답변 ID (FK)
   - 답변 값, 텍스트 입력 값 (평수 등)
   - 단계 번호

#### 초기 데이터

- Step 1: 분위기 질문 및 4개 선택지
- Step 2: 메이트 질문 및 4개 선택지, 반려동물 질문 및 2개 선택지
- Step 3: 주거 형태 질문 및 4개 선택지, 주요 공간 질문 및 6개 선택지, 평수 입력
- Step 4: 요리 질문 및 3개 선택지, 세탁 질문 및 3개 선택지, 미디어 질문 및 4개 선택지
- Step 5: 우선순위 질문 및 4개 선택지
- Step 6: 예산 질문 및 3개 선택지

### 2. 온보딩 DB 서비스 구현

**파일**: `api/services/onboarding_db_service.py`

#### 주요 메서드

- `create_or_update_session()`: 세션 생성 또는 업데이트
- `save_user_response()`: 단일 선택 응답 저장
- `save_multiple_responses()`: 다중 선택 응답 저장 (main_space, priority 등)
- `get_session()`: 세션 정보 조회
- `get_user_responses()`: 사용자 응답 조회

### 3. views.py 수정

**파일**: `api/views.py`

#### 변경 사항

- `onboarding_step_view` 함수에 Oracle DB 저장 로직 추가
- Django DB (SQLite) 저장과 병행하여 Oracle DB에도 저장
- Oracle DB 저장 실패 시에도 Django DB 저장은 유지 (에러 처리)

#### 저장 로직

각 단계별로:
- **Step 1**: vibe 저장
- **Step 2**: mate, pet 저장
- **Step 3**: housing_type, main_space (다중 선택), pyung (텍스트 입력) 저장
- **Step 4**: cooking, laundry, media 저장
- **Step 5**: priority (다중 선택) 저장
- **Step 6**: budget 저장

## 사용 방법

### 1. Oracle DB 테이블 생성

```sql
-- DDL 스크립트 실행
@api/db/onboarding_tables_ddl.sql
```

또는 SQL Developer에서 스크립트 실행

### 2. 온보딩 진행 시 자동 저장

온보딩 단계별로 `/api/onboarding/step/` API 호출 시:
- Django DB (SQLite)에 저장
- Oracle DB에도 자동 저장

### 3. 데이터 조회

```python
from api.services.onboarding_db_service import onboarding_db_service

# 세션 정보 조회
session = onboarding_db_service.get_session('session_12345')

# 사용자 응답 조회
responses = onboarding_db_service.get_user_responses('session_12345', step_number=1)
```

## 테이블 관계도

```
ONBOARDING_QUESTION (1) ──< (N) ONBOARDING_ANSWER
    │
    │ (1)
    │
    └──< (N) ONBOARDING_USER_RESPONSE
            │
            │ (N)
            │
            └──> (1) ONBOARDING_SESSION
```

## 주의사항

1. **Oracle DB 연결 설정**: `.env` 파일에 Oracle DB 연결 정보가 설정되어 있어야 함
   - `ORACLE_USER`
   - `ORACLE_PASSWORD`
   - `ORACLE_HOST`
   - `ORACLE_PORT`

2. **에러 처리**: Oracle DB 저장 실패 시에도 Django DB 저장은 유지되므로 서비스는 계속 동작

3. **다중 선택 처리**: 
   - `main_space`, `priority`는 다중 선택 가능
   - `save_multiple_responses()` 메서드 사용

4. **텍스트 입력 처리**:
   - `pyung` (평수)는 텍스트 입력
   - `answer_value`와 `answer_text` 모두 저장

## 다음 단계 (선택사항)

1. 온보딩 데이터 분석 대시보드
2. 사용자 응답 통계 조회 API
3. 온보딩 완료율 분석
4. 추천 결과와 온보딩 데이터 연계 분석

