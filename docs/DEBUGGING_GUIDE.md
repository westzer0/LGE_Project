# 디버깅 가이드

프로젝트에서 발생할 수 있는 문제와 해결 방법을 정리한 가이드입니다.

## 프론트엔드-백엔드 통신 문제

### 1. API 호출이 실패하는 경우

**증상**: 브라우저 콘솔에 네트워크 오류 또는 CORS 오류

**해결 방법**:
1. Django 서버가 실행 중인지 확인
   ```bash
   python manage.py runserver 8000
   ```

2. React 개발 서버가 실행 중인지 확인
   ```bash
   npm run dev
   ```

3. CORS 설정 확인 (`config/settings.py`)
   ```python
   CSRF_TRUSTED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
   ]
   ```

4. 브라우저 개발자 도구에서 네트워크 탭 확인
   - 요청 URL이 올바른지 확인
   - 응답 상태 코드 확인
   - 응답 본문 확인

### 2. CSRF 토큰 오류

**증상**: `403 Forbidden` 또는 `CSRF token missing` 오류

**해결 방법**:
1. `src/utils/api.js`의 `initCSRFToken` 함수가 정상 작동하는지 확인
2. Django 서버에서 CSRF 토큰이 정상적으로 설정되는지 확인
3. 브라우저 쿠키에 `csrftoken`이 있는지 확인

### 3. API 응답이 비어있는 경우

**증상**: API 호출은 성공하지만 데이터가 없음

**해결 방법**:
1. 백엔드 로그 확인 (Django 콘솔 출력)
2. 데이터베이스에 제품 데이터가 있는지 확인
   ```bash
   python manage.py shell
   >>> from api.models import Product
   >>> Product.objects.count()
   ```

3. 추천 엔진이 정상 작동하는지 확인
   - `api/services/recommendation_engine.py`의 로그 확인

## 온보딩 플로우 문제

### 1. 온보딩 제출이 실패하는 경우

**증상**: "완료" 버튼을 눌러도 아무 반응이 없음

**해결 방법**:
1. 브라우저 콘솔 확인 (F12)
2. 네트워크 탭에서 `/api/onboarding/complete/` 요청 확인
3. 요청 본문이 올바른 형식인지 확인
4. 백엔드 로그에서 에러 메시지 확인

**확인 사항**:
- `session_id`가 생성되는지
- 모든 필수 필드가 채워져 있는지
- `household_size`가 정수로 변환되는지

### 2. 추천 결과가 표시되지 않는 경우

**증상**: 온보딩 완료 후 결과 페이지가 비어있음

**해결 방법**:
1. `PortfolioResult.jsx`의 `useEffect` 확인
2. `location.state`에 `recommendations`가 있는지 확인
3. URL 파라미터에 `portfolio_id`가 있는지 확인
4. API 응답 형식이 예상과 일치하는지 확인

## 데이터베이스 문제

### 1. 제품 데이터가 없는 경우

**해결 방법**:
```bash
# 제품 데이터 로드 (커스텀 명령어가 있는 경우)
python manage.py load_products

# 또는 직접 확인
python manage.py shell
>>> from api.models import Product
>>> Product.objects.all()
```

### 2. 포트폴리오가 생성되지 않는 경우

**해결 방법**:
1. `api/services/portfolio_service.py` 확인
2. `OnboardingSession`이 정상적으로 저장되었는지 확인
3. 추천 결과가 있는지 확인

## 로깅 및 디버깅

### 프론트엔드 로깅

브라우저 콘솔에서 확인:
- `[API]` 접두사가 붙은 로그
- `[Onboarding]` 접두사가 붙은 로그
- `[PortfolioResult]` 접두사가 붙은 로그

### 백엔드 로깅

Django 콘솔에서 확인:
- `[Onboarding Complete]` 접두사가 붙은 로그
- `[Portfolio Detail]` 접두사가 붙은 로그
- `[Recommendation]` 접두사가 붙은 로그

### 로그 레벨 설정

`config/settings.py`에서 로깅 설정:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

## 일반적인 문제 해결

### 1. 서버 재시작

```bash
# Django 서버 재시작
Ctrl+C로 중지 후
python manage.py runserver 8000

# React 서버 재시작
Ctrl+C로 중지 후
npm run dev
```

### 2. 캐시 클리어

```bash
# 브라우저 캐시 클리어 (Ctrl+Shift+Delete)
# 또는 하드 리프레시 (Ctrl+Shift+R)
```

### 3. 의존성 재설치

```bash
# Python 패키지
pip install -r requirements.txt

# Node.js 패키지
npm install
```

### 4. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

## 성능 문제

### 1. API 응답이 느린 경우

- 데이터베이스 쿼리 최적화 확인
- 추천 엔진 로직 최적화
- 제품 데이터 인덱싱 확인

### 2. 프론트엔드 렌더링이 느린 경우

- React DevTools Profiler 사용
- 불필요한 리렌더링 확인
- 이미지 최적화 확인

---

**마지막 업데이트**: 2024년 12월

