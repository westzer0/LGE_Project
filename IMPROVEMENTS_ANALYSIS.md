# 프로젝트 개선사항 분석 보고서 (PRD 기준)

**분석 일시**: 2024년 12월  
**분석 기준**: PRD (가전 추천 포트폴리오, Last Update: 26/11/2025) 및 코드베이스 분석

---

## 📋 개요

이 문서는 **PRD 요구사항을 기준**으로 LG 가전 패키지 추천 시스템의 DB, 백엔드, 프론트엔드, 서버 관련 개선사항을 체계적으로 정리한 것입니다.

### PRD 핵심 요구사항 요약
- **온보딩 6단계**: Vibe Check → Household DNA → Reality Check → Lifestyle Info → Priorities → Budget
- **포트폴리오 추천**: 스타일 분석, 추천 이유, 구매 리뷰 분석, 매칭 퍼센트
- **포트폴리오 관리**: 저장/공유, 다시 추천받기, 다른 추천 후보, 장바구니 담기, 베스트샵 상담 예약, 편집
- **공간 디자인**: 이미지 업로드, 가전/가구 배치 시각화 (★★☆ 우선순위)
- **견적 관리**: 즉시 조회, 저장/공유

---

## 🗄️ 1. 데이터베이스 (DB) 관련 개선사항

### 1.1 보안 이슈

#### 🔴 **긴급**: 하드코딩된 DB 인증 정보
**위치**: `api/db/oracle_client.py:77-81`

```python
ORACLE_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
```

**문제점**:
- 기본값으로 실제 DB 인증 정보가 하드코딩되어 있음
- 코드가 공개 저장소에 올라가면 보안 위험
- 환경 변수가 없을 때 기본값 사용으로 인한 보안 취약점

**개선 방안**:
```python
# 환경 변수가 필수로 설정되어야 함
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_HOST = os.getenv("ORACLE_HOST")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))

if not all([ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST]):
    raise ValueError("Oracle DB 환경 변수가 설정되지 않았습니다.")
```

### 1.2 연결 관리

#### 🟡 **중요**: DB 연결 풀링 부재
**문제점**:
- 매 요청마다 새로운 DB 연결 생성
- 고부하 시 연결 수 제한 초과 가능
- 성능 저하

**개선 방안**:
- Oracle Connection Pool 구현
- 연결 재사용으로 성능 향상
- 최대 연결 수 제한 설정

```python
# 예시: 연결 풀 구현
import oracledb

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=DSN,
            min=2,
            max=10,
            increment=1
        )
    return _pool
```

### 1.3 에러 처리

#### 🟡 **중요**: DB 에러 처리 일관성 부족
**문제점**:
- `DatabaseDisabledError`는 처리되지만, 다른 DB 에러는 일관성 없이 처리됨
- 타임아웃 에러 처리 부재
- 연결 실패 시 사용자 친화적 메시지 부족

**개선 방안**:
- 통일된 에러 핸들링 미들웨어 구현
- DB 에러 타입별 분류 및 처리
- 로깅 강화

### 1.4 트랜잭션 관리

#### 🟡 **중요**: 트랜잭션 관리 개선 필요
**문제점**:
- 명시적 트랜잭션 관리 부재
- 롤백 처리 미흡

**개선 방안**:
- Django ORM 트랜잭션 데코레이터 활용
- 예외 발생 시 자동 롤백 보장

---

## 🔧 2. 백엔드 관련 개선사항

### 2.1 보안 이슈

#### 🔴 **긴급**: 과도한 CSRF 비활성화
**위치**: `api/views.py` (28개 엔드포인트)

**문제점**:
- 28개의 API 엔드포인트에서 `@csrf_exempt` 사용
- CSRF 공격에 취약
- POST/PUT/DELETE 요청 보호 부재

**개선 방안**:
```python
# CSRF 보호 활성화
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token

# 또는 DRF의 인증 클래스 사용
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
```

**우선순위**:
1. 사용자 데이터를 변경하는 API부터 CSRF 보호 적용
2. 읽기 전용 API는 선택적 적용
3. React 앱에서 CSRF 토큰 자동 처리

#### 🔴 **긴급**: SECRET_KEY 기본값
**위치**: `config/settings.py:59`

```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-8zb-1$0d6^f=&c@v8-l2-9b*9ydnp7k3m0-s_y8gljjkvtiyt8')
```

**문제점**:
- 프로덕션에서 기본값 사용 시 보안 위험
- 환경 변수 누락 시 경고만 출력

**개선 방안**:
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-...'  # 개발 환경만
    else:
        raise ValueError("DJANGO_SECRET_KEY 환경 변수가 설정되지 않았습니다.")
```

#### 🟡 **중요**: DEBUG 기본값 True
**위치**: `config/settings.py:63`

```python
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
```

**문제점**:
- 프로덕션에서 실수로 DEBUG=True 가능
- 상세 에러 정보 노출 위험

**개선 방안**:
```python
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'
```

### 2.2 API 응답 표준화

#### 🟡 **중요**: 응답 형식 불일치
**문제점**:
- 일부 API는 `{"success": true, "data": ...}` 형식
- 일부는 직접 데이터 반환
- 에러 응답 형식도 불일치

**개선 방안**:
- DRF Response 클래스 활용
- 통일된 응답 포맷 정의
- 커스텀 렌더러 구현

```python
# 예시: 통일된 응답 형식
class StandardResponse:
    @staticmethod
    def success(data=None, message=None):
        return JsonResponse({
            'success': True,
            'data': data,
            'message': message
        }, json_dumps_params={'ensure_ascii': False})
    
    @staticmethod
    def error(message, code=400):
        return JsonResponse({
            'success': False,
            'error': message
        }, status=code, json_dumps_params={'ensure_ascii': False})
```

### 2.3 에러 처리

#### 🟡 **중요**: 예외 처리 일관성 부족
**문제점**:
- 일부 뷰는 try-except로 처리
- 일부는 Django 기본 에러 처리에 의존
- 에러 로깅 부족

**개선 방안**:
- 커스텀 예외 클래스 정의
- 미들웨어에서 전역 예외 처리
- 에러 로깅 강화

```python
# 예시: 커스텀 예외
class APIException(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

# 예시: 전역 예외 처리 미들웨어
class APIExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
        except APIException as e:
            return JsonResponse({
                'success': False,
                'error': e.message
            }, status=e.status_code)
        return response
```

### 2.4 입력 검증

#### 🟡 **중요**: 입력 검증 부족
**문제점**:
- 일부 API에서 입력 검증 없이 처리
- SQL Injection 위험 (ORM 사용 시 낮지만)
- XSS 위험

**개선 방안**:
- DRF Serializer 활용
- 입력 값 타입 및 범위 검증
- Sanitization 적용

### 2.5 로깅

#### 🟢 **권장**: 로깅 개선
**문제점**:
- 로깅 설정은 있으나 활용도 낮음
- API 요청/응답 로깅 부족
- 에러 로깅 상세도 부족

**개선 방안**:
- 요청/응답 로깅 미들웨어
- 에러 스택 트레이스 로깅
- 로그 레벨별 분리

---

## 🎨 3. 프론트엔드 관련 개선사항

### 3.1 에러 처리

#### 🟡 **중요**: 에러 처리 개선 필요
**위치**: `src/utils/api.js`, `src/pages/Onboarding.jsx`

**문제점**:
- 네트워크 에러는 처리되지만, 비즈니스 로직 에러 처리 부족
- 사용자 친화적 에러 메시지 부족
- 에러 상태 UI 부재

**개선 방안**:
```javascript
// 에러 타입별 처리
const handleAPIError = (error) => {
  if (error.message.includes('네트워크')) {
    return '서버에 연결할 수 없습니다. 네트워크를 확인해주세요.';
  }
  if (error.message.includes('404')) {
    return '요청한 리소스를 찾을 수 없습니다.';
  }
  if (error.message.includes('500')) {
    return '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
  }
  return error.message || '알 수 없는 오류가 발생했습니다.';
};
```

### 3.2 로딩 상태 관리

#### 🟡 **중요**: 로딩 상태 UI 개선
**문제점**:
- 로딩 상태는 있으나 사용자 경험 개선 여지
- 스켈레톤 UI 부재
- 진행률 표시 부재

**개선 방안**:
- 스켈레톤 UI 컴포넌트 추가
- 진행률 표시 (온보딩 단계별)
- 로딩 애니메이션 개선

### 3.3 상태 관리

#### 🟢 **권장**: 상태 관리 라이브러리 도입
**문제점**:
- React 기본 상태 관리만 사용
- 복잡한 상태 관리 시 prop drilling 가능성
- 전역 상태 관리 부재

**개선 방안**:
- Context API 활용
- 또는 Zustand/Redux 도입 검토

### 3.4 성능 최적화

#### 🟢 **권장**: 성능 최적화
**문제점**:
- 컴포넌트 리렌더링 최적화 부족
- 이미지 최적화 부재
- 코드 스플리팅 부재

**개선 방안**:
- React.memo, useMemo, useCallback 활용
- 이미지 lazy loading
- React.lazy로 코드 스플리팅

---

## 🖥️ 4. 서버 설정 관련 개선사항

### 4.1 보안 설정

#### 🔴 **긴급**: 하드코딩된 ngrok 도메인
**위치**: `config/settings.py:68`

```python
default_hosts = 'localhost,127.0.0.1,testserver,braeden-unaromatic-zola.ngrok-free.dev'
```

**문제점**:
- ngrok 도메인이 하드코딩되어 있음
- ngrok 도메인은 변경될 수 있음
- 환경 변수로 관리해야 함

**개선 방안**:
```python
default_hosts = 'localhost,127.0.0.1,testserver'
ngrok_host = os.environ.get('NGROK_HOST')
if ngrok_host:
    default_hosts += f',{ngrok_host}'
```

#### 🟡 **중요**: 프로덕션 보안 설정 강화
**문제점**:
- 일부 보안 설정이 프로덕션에서만 적용
- SECURE_HSTS_SECONDS 미설정
- SECURE_REFERRER_POLICY 미설정

**개선 방안**:
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1년
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

### 4.2 환경 변수 관리

#### 🟡 **중요**: 환경 변수 검증 강화
**문제점**:
- 필수 환경 변수 누락 시 경고만 출력
- 프로덕션에서 필수 변수 누락 가능

**개선 방안**:
- 시작 시 필수 환경 변수 검증
- 누락 시 서버 시작 실패

```python
# 필수 환경 변수 목록
REQUIRED_ENV_VARS = [
    'DJANGO_SECRET_KEY',
] if not DEBUG else []

# 선택적 필수 (프로덕션에서만)
if not DEBUG:
    REQUIRED_ENV_VARS.extend([
        'ALLOWED_HOSTS',
    ])

# 검증
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
```

### 4.3 로깅 설정

#### 🟢 **권장**: 로깅 설정 개선
**문제점**:
- 로깅 설정은 있으나 파일 로그 디렉토리 생성 확인 필요
- 로그 로테이션 설정 부재
- 프로덕션 로그 레벨 관리 부재

**개선 방안**:
- 로그 로테이션 설정 (RotatingFileHandler)
- 환경별 로그 레벨 설정
- 에러 로그 별도 파일 관리

---

## 📊 5. PRD 요구사항 대비 구현 상태

### ✅ 구현 완료된 기능
1. **온보딩 6단계** - 기본 구현 완료
2. **포트폴리오 추천** - 기본 구현 완료
3. **포트폴리오 다시 추천받기** - `portfolio_refresh_view` 구현됨
4. **다른 추천 후보 확인** - `portfolio_alternatives_view` 구현됨
5. **장바구니 담기** - `portfolio_add_to_cart_view` 구현됨
6. **베스트샵 상담 예약** - `bestshop_consultation_view` 구현됨
7. **포트폴리오 편집** - `portfolio_edit_view` 구현됨
8. **스타일 분석** - `style_analysis_service` 구현됨

### ⚠️ PRD 요구사항 미충족 또는 개선 필요

#### 🔴 **긴급**: PRD 요구사항 누락
1. **공간 디자인 기능 미구현** (PRD: ★★☆ 우선순위)
   - 이미지 업로드 기능 없음
   - 가전/가구 배치 시각화 기능 없음
   - 자연어를 통한 짐/가구 제거 기능 없음
   - 드래그 앤 드롭 배치 기능 없음

2. **스타일 메시지 PRD 패턴 미적용**
   - PRD에 상세한 스타일 메시지 패턴 제공됨
   - 현재는 기본 메시지만 생성
   - PRD 예시 패턴 적용 필요:
     - 디자인 취향 기반 타이틀 패턴
     - 종합형 타이틀 (디자인 + 라이프스타일)
     - 고객 타입 기반 타이틀
     - 상세한 서브 메시지 패턴

3. **온보딩 이탈 시 임시저장 미구현** (PRD: P1 / ★★☆)
   - PRD: "사용자 ID + 내부키로 임시저장"
   - 현재: alert만 표시, 저장 기능 없음

4. **구매 리뷰 분석 표시 미흡** (PRD 요구사항)
   - PRD: "구매 리뷰는 모델별로 최대 3개까지 표시"
   - 현재: 리뷰 조회 API는 있으나 포트폴리오 결과 화면에 표시 여부 확인 필요

5. **도면 기반 설치 유의사항 자동 출력 미구현**
   - PRD: "제품 치수 + 유저가 입력한 공간 데이터 기반 설치 유의사항 자동 출력"
   - 현재: 관련 로직 확인 필요

#### 🟡 **중요**: PRD 요구사항 부분 구현 또는 개선 필요
1. **온보딩 Step 3 분기 처리 미완성**
   - PRD: 원룸 선택 시 Q3-2 건너뛰기 → 바로 Q3-3로 이동
   - PRD: 주방 선택 시 Step 4에서 요리 빈도만 활성화
   - PRD: 드레스룸 선택 시 Step 4에서 세탁 패턴만 활성화
   - 현재: 분기 로직 확인 필요

2. **포트폴리오 결과 화면 구성 미흡**
   - PRD: "매거진 느낌으로 구성"
   - PRD: "가전별 대표 이미지, 각 가전 이미지&종류 클릭 시 해당 위치로 자동 스크롤"
   - 현재: 기본 구성만 있음

3. **추천 이유 생성 로직 개선 필요**
   - PRD: "온보딩 값 + 제품 스펙 기반으로 생성"
   - PRD 예시: "가족 수에 맞는 용량", "주방 폭에 맞는 600mm 이하 모델"
   - 현재: 기본 추천 이유만 생성

4. **베스트샵 상담 예약 연동 미완성**
   - PRD: "상담 일자, 시간 선택 → 약관 동의 → 예약 신청하기 클릭 시 해당 베스트샵 상담 매니저에게 유저의 가전 포트폴리오 목록 자동 전송"
   - 현재: URL 생성만 하고 실제 전송 로직 확인 필요

---

## 📊 6. 종합 개선 우선순위

### 🔴 긴급 (즉시 수정 필요)
1. **DB 인증 정보 하드코딩 제거** - 보안 위험
2. **CSRF 보호 활성화** - 보안 위험
3. **SECRET_KEY 기본값 제거** - 보안 위험
4. **ngrok 도메인 하드코딩 제거** - 운영 안정성

### 🟡 중요 (단기 개선 - PRD 요구사항)
1. **스타일 메시지 PRD 패턴 적용** - PRD 요구사항
2. **온보딩 Step 3 분기 처리 완성** - PRD 요구사항
3. **포트폴리오 결과 화면 매거진 스타일 구성** - PRD 요구사항
4. **구매 리뷰 분석 표시 강화** - PRD 요구사항
5. **도면 기반 설치 유의사항 자동 출력** - PRD 요구사항

### 🟢 권장 (중장기 개선)
1. **공간 디자인 기능 구현** - PRD: ★★☆ 우선순위
2. **온보딩 이탈 시 임시저장** - PRD: P1 / ★★☆
3. **DB 연결 풀링 구현** - 성능
4. **API 응답 표준화** - 유지보수성
5. **에러 처리 일관성** - 안정성
6. **로깅 강화** - 모니터링
7. **프론트엔드 성능 최적화** - 사용자 경험

---

## 📝 구현 체크리스트 (PRD 기준)

### Phase 1: 보안 개선 (1주)
- [ ] DB 인증 정보 하드코딩 제거
- [ ] SECRET_KEY 기본값 제거
- [ ] CSRF 보호 활성화 (우선순위 높은 API부터)
- [ ] ngrok 도메인 환경 변수화
- [ ] DEBUG 기본값 False로 변경

### Phase 2: PRD 핵심 요구사항 구현 (2주)
- [ ] 스타일 메시지 PRD 패턴 적용
  - [ ] 디자인 취향 기반 타이틀 패턴
  - [ ] 종합형 타이틀 (디자인 + 라이프스타일)
  - [ ] 고객 타입 기반 타이틀
  - [ ] 상세한 서브 메시지 패턴
- [ ] 온보딩 Step 3 분기 처리 완성
  - [ ] 원룸 선택 시 Q3-2 건너뛰기
  - [ ] 주방 선택 시 Step 4 요리 빈도만 활성화
  - [ ] 드레스룸 선택 시 Step 4 세탁 패턴만 활성화
- [ ] 포트폴리오 결과 화면 매거진 스타일 구성
  - [ ] 가전별 대표 이미지
  - [ ] 각 가전 이미지&종류 클릭 시 자동 스크롤
- [ ] 구매 리뷰 분석 표시 강화 (모델별 최대 3개)
- [ ] 도면 기반 설치 유의사항 자동 출력

### Phase 3: PRD 선택 기능 구현 (2주)
- [ ] 공간 디자인 기능 구현 (PRD: ★★☆)
  - [ ] 이미지 업로드 기능
  - [ ] 가전/가구 배치 시각화
  - [ ] 자연어를 통한 짐/가구 제거
  - [ ] 드래그 앤 드롭 배치
- [ ] 온보딩 이탈 시 임시저장 (PRD: P1 / ★★☆)
- [ ] 베스트샵 상담 예약 포트폴리오 자동 전송

### Phase 4: 안정성 및 성능 개선 (2주)
- [ ] DB 연결 풀링 구현
- [ ] API 응답 표준화
- [ ] 에러 처리 미들웨어 구현
- [ ] 입력 검증 강화
- [ ] 환경 변수 검증 로직 추가
- [ ] 프론트엔드 에러 처리 개선
- [ ] 로딩 상태 UI 개선

### Phase 5: 모니터링 및 품질 (1주)
- [ ] 로깅 강화
- [ ] 로그 로테이션 설정
- [ ] 테스트 코드 작성
- [ ] API 문서 업데이트

---

## 🔗 참고 문서

- [Django Security Best Practices](https://docs.djangoproject.com/en/5.2/topics/security/)
- [Django REST Framework Security](https://www.django-rest-framework.org/topics/security/)
- [Oracle Connection Pooling](https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html#connection-pooling)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)

---

## 📌 PRD 요구사항 상세 체크리스트

### 온보딩 (6단계)
- [x] Step 1: Vibe Check (감성 & 취향) - 구현됨
- [x] Step 2: Household DNA (구성원 & 펫) - 구현됨
- [ ] Step 3: Reality Check (공간 제약 & 카테고리별 상세) - **분기 처리 미완성**
  - [ ] 원룸 선택 시 Q3-2 건너뛰기
  - [ ] 주방/드레스룸 선택 시 Step 4 질문 분기
- [x] Step 4: Lifestyle Info (라이프스타일 정보) - 구현됨
- [x] Step 5: Priorities (가치관) - 구현됨
- [x] Step 6: Budget (예산 범위) - 구현됨
- [ ] 온보딩 이탈 시 임시저장 - **미구현**

### 포트폴리오 추천
- [x] 온보딩 기반 추천 - 구현됨
- [x] 스타일 분석 결과 - 구현됨 (PRD 패턴 미적용)
- [x] 추천 이유 제공 - 구현됨 (PRD 예시 패턴 적용 필요)
- [ ] 구매 리뷰 분석 표시 - **포트폴리오 결과 화면에 표시 확인 필요**
- [ ] 매칭 퍼센트 표시 - **구현 여부 확인 필요**
- [ ] 도면 기반 설치 유의사항 - **자동 출력 미구현**

### 포트폴리오 관리
- [x] 포트폴리오 저장 - 구현됨
- [x] 포트폴리오 공유 (카카오톡, 링크) - 구현됨
- [x] 다시 추천받기 (리프레시) - 구현됨
- [x] 다른 추천 후보 확인 - 구현됨
- [x] 장바구니 모두 담기 - 구현됨
- [x] 베스트샵 상담 예약 - 구현됨 (포트폴리오 자동 전송 확인 필요)
- [x] 포트폴리오 편집 (추가/삭제/업그레이드/다운그레이드) - 구현됨

### 공간 디자인 (PRD: ★★☆ 우선순위)
- [ ] 이미지 업로드 - **미구현**
- [ ] 공간 구조와 색감/스타일 분석 - **미구현**
- [ ] 추천 제품 직접 배치 - **미구현**
- [ ] 다양한 가전 색상, 모델 옵션 시각적 비교 - **미구현**
- [ ] 자연어를 통한 짐/가구 제거 - **미구현**
- [ ] 드래그 앤 드롭 배치 - **미구현**
- [ ] 공간 디자인 결과 외부 공유 - **미구현**

### 견적 관리
- [x] 즉시 견적 조회 - 구현됨
- [x] 견적 저장/공유 - 구현됨

---

**작성자**: AI Assistant  
**최종 업데이트**: 2024년 12월  
**PRD 기준**: 가전 추천 포트폴리오 (Last Update: 26/11/2025)
