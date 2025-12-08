# 배포 환경 변수 가이드

## 필수 환경 변수

### Django 기본 설정
```bash
# Django Secret Key (필수)
# 생성 방법: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=your-production-secret-key-here

# Debug 모드 (프로덕션에서는 반드시 False)
DJANGO_DEBUG=False

# 허용된 호스트 (쉼표로 구분)
ALLOWED_HOSTS=your-app.railway.app,yourdomain.com
```

### 외부 API 키
```bash
# 카카오 API
KAKAO_REST_API_KEY=your_kakao_rest_api_key
KAKAO_JS_KEY=your_kakao_js_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

### 데이터베이스 설정 (Oracle)
```bash
# Oracle 사용 여부
USE_ORACLE=true

# Oracle 연결 정보
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=your_db_password
ORACLE_SID=xe

# Oracle Instant Client 경로 (Thick 모드 사용 시, 로컬 전용)
ORACLE_INSTANT_CLIENT_PATH=/path/to/instantclient
```

### 보안 설정 (선택사항)
```bash
# CSRF 신뢰 도메인 (HTTPS 사용 시)
CSRF_TRUSTED_ORIGINS=https://your-app.railway.app,https://yourdomain.com

# CORS 허용 도메인
CORS_ALLOWED_ORIGINS=https://your-app.railway.app,https://yourdomain.com

# SSL 강제 리다이렉트 (HTTPS 사용 시)
SECURE_SSL_REDIRECT=true
```

## 배포 플랫폼별 설정 방법

### Railway
1. Railway 대시보드 → 프로젝트 선택
2. Settings → Variables 탭
3. 환경 변수 추가

또는 Railway CLI 사용:
```bash
railway variables set DJANGO_SECRET_KEY=your-key
railway variables set DJANGO_DEBUG=False
```

### Render
1. Render 대시보드 → 서비스 선택
2. Environment 탭
3. Environment Variables 섹션에서 추가

또는 `render.yaml`에서 `sync: false`로 설정된 변수는 수동으로 설정 필요

### Fly.io
```bash
fly secrets set DJANGO_SECRET_KEY=your-key
fly secrets set DJANGO_DEBUG=False
fly secrets set ALLOWED_HOSTS=your-app.fly.dev
```

## 환경 변수 검증

배포 전 다음 스크립트로 환경 변수 확인:
```python
# check_env.py
import os
required_vars = [
    'DJANGO_SECRET_KEY',
    'DJANGO_DEBUG',
    'ALLOWED_HOSTS',
    'KAKAO_REST_API_KEY',
    'KAKAO_JS_KEY',
    'OPENAI_API_KEY',
]

missing = []
for var in required_vars:
    if not os.environ.get(var):
        missing.append(var)

if missing:
    print(f"❌ 누락된 환경 변수: {', '.join(missing)}")
else:
    print("✅ 모든 필수 환경 변수가 설정되었습니다.")
```

## 보안 주의사항

1. **절대 Git에 커밋하지 마세요**
   - `.env` 파일은 `.gitignore`에 포함되어야 함
   - 환경 변수는 배포 플랫폼의 환경 변수 설정 기능 사용

2. **프로덕션 Secret Key**
   - 개발용 키와 프로덕션 키는 반드시 분리
   - 강력한 랜덤 키 사용

3. **API 키 보호**
   - 외부에 노출되지 않도록 주의
   - 필요시 키 로테이션

4. **DEBUG 모드**
   - 프로덕션에서는 반드시 `False`
   - `True`로 설정 시 보안 취약점 노출

