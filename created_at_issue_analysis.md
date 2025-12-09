# created_at 칼럼 쓰레기값 원인 분석 결과

## 분석 결과 요약

### 1. 데이터베이스 상태 확인
- ✅ **CREATED_AT 컬럼은 DATE 타입으로 올바르게 정의되어 있음**
- ✅ **데이터는 "2025-12-09 18:03:55" 형식으로 올바르게 저장되어 있음**
- ✅ **DUMP 결과: Typ=12 Len=7 (Oracle DATE 타입 정상)**

### 2. 문제의 원인

사용자가 본 **"25/12/09 18:03:55"** 형식은:
- **데이터 자체의 문제가 아님**
- **데이터를 조회할 때 `TO_CHAR(CREATED_AT, 'YY/MM/DD HH24:MI:SS')` 형식으로 변환했을 때 나타나는 형식**
- 실제 데이터는 **"2025-12-09 18:03:55"**로 올바르게 저장되어 있음

### 3. 실제 문제점

#### 3.1 타임스탬프 기반 SESSION_ID
```
1765271034356  ← 타임스탬프 기반 (밀리초)
1765270584060  ← 타임스탬프 기반 (밀리초)
1765270756659  ← 타임스탬프 기반 (밀리초)
```

**원인:**
- 프론트엔드나 다른 경로에서 `Date.now()` 또는 `new Date().getTime()`을 사용하여 SESSION_ID를 생성
- `views.py`의 853-863번째 줄에 타임스탬프 기반 SESSION_ID를 UUID로 변환하는 로직이 있지만, **이미 저장된 데이터는 변환되지 않음**

**위치:**
- `api/views.py` 853-863번째 줄:
```python
# session_id가 숫자 문자열이면 UUID로 변환 (타임스탬프 기반 ID 방지)
try:
    # 숫자로 변환 가능한지 확인 (타임스탬프 기반 ID)
    int(session_id)
    # 숫자 문자열이면 UUID로 재생성
    import uuid
    session_id = str(uuid.uuid4())
    print(f"[Onboarding Step] 타임스탬프 기반 session_id 감지, UUID로 변환: {session_id}", flush=True)
except (ValueError, TypeError):
    # 이미 UUID 형식이거나 다른 형식이면 그대로 사용
    pass
```

#### 3.2 데이터 조회 시 날짜 형식
- Oracle의 DATE 타입은 내부적으로 저장되지만, 조회 시 `TO_CHAR`를 사용하지 않으면 클라이언트의 NLS_DATE_FORMAT 설정에 따라 표시됨
- 일부 클라이언트 도구나 쿼리에서 `TO_CHAR(CREATED_AT, 'YY/MM/DD HH24:MI:SS')` 형식을 사용하면 "25/12/09 18:03:55" 형식으로 표시됨

### 4. 해결 방안

#### 4.1 타임스탬프 기반 SESSION_ID 문제 해결
1. **프론트엔드 수정**: 타임스탬프 기반 SESSION_ID 생성 방지
   - `src/pages/Onboarding.jsx`의 `generateSessionId()` 함수는 이미 UUID를 사용하고 있음 ✅
   - 다른 경로에서 타임스탬프 기반 ID를 생성하는지 확인 필요

2. **기존 데이터 마이그레이션**: 타임스탬프 기반 SESSION_ID를 UUID로 변환
   ```sql
   -- 타임스탬프 기반 SESSION_ID를 UUID로 변환하는 마이그레이션 스크립트 필요
   ```

#### 4.2 날짜 형식 표시 문제 해결
1. **조회 쿼리 수정**: 항상 `TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')` 형식 사용
2. **NLS_DATE_FORMAT 설정**: Oracle 세션 레벨에서 날짜 형식 설정
   ```sql
   ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS';
   ```

### 5. 확인된 정상 데이터 예시

```
SESSION_ID: 1765271034356
MEMBER_ID: GUEST
CREATED_AT (YYYY-MM-DD): 2025-12-09 18:03:55  ← 올바른 형식
CREATED_AT (YY/MM/DD): 25/12/09 18:03:55      ← 조회 시 형식 변환된 것
CURRENT_STEP: 1
STATUS: IN_PROGRESS
VIBE: pop  ← 정상적인 값
PRIORITY: value  ← 정상적인 값
BUDGET_LEVEL: medium  ← 정상적인 값
```

### 6. 결론

**"25/12/09 18:03:55" 형식은 쓰레기값이 아니라, 날짜 형식 변환 결과입니다.**

실제 문제는:
1. ✅ **CREATED_AT 데이터는 정상적으로 저장되어 있음**
2. ⚠️ **타임스탬프 기반 SESSION_ID가 일부 존재함** (UUID로 변환 필요)
3. ⚠️ **데이터 조회 시 날짜 형식이 일관되지 않음** (TO_CHAR 형식 통일 필요)

### 7. 권장 조치사항

1. **즉시 조치**: 데이터 조회 시 항상 `TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')` 형식 사용
2. **중기 조치**: 타임스탬프 기반 SESSION_ID를 UUID로 마이그레이션
3. **장기 조치**: 프론트엔드에서 타임스탬프 기반 SESSION_ID 생성 경로 차단

