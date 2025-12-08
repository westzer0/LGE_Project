# 배포 체크리스트

## 배포 전 필수 확인 사항

### 1. 환경 변수 설정
- [ ] `DJANGO_SECRET_KEY` - Django 시크릿 키 (프로덕션용 강력한 키)
- [ ] `DJANGO_DEBUG=False` - 프로덕션에서는 반드시 False
- [ ] `ALLOWED_HOSTS` - 배포 도메인 설정 (예: your-app.railway.app)
- [ ] `KAKAO_REST_API_KEY` - 카카오 REST API 키
- [ ] `KAKAO_JS_KEY` - 카카오 JavaScript 키
- [ ] `OPENAI_API_KEY` - OpenAI API 키
- [ ] `USE_ORACLE=true` - Oracle DB 사용 여부
- [ ] `ORACLE_HOST` - Oracle DB 호스트
- [ ] `ORACLE_PORT` - Oracle DB 포트
- [ ] `ORACLE_USER` - Oracle DB 사용자
- [ ] `ORACLE_PASSWORD` - Oracle DB 비밀번호
- [ ] `ORACLE_SID` - Oracle SID
- [ ] `CSRF_TRUSTED_ORIGINS` - CSRF 신뢰 도메인 (필요시)
- [ ] `CORS_ALLOWED_ORIGINS` - CORS 허용 도메인 (필요시)

### 2. 코드 준비
- [ ] `requirements.txt` 정리 완료 (필수 패키지만 포함)
- [ ] `Dockerfile` 검증 완료
- [ ] React 빌드 설정 확인 (`vite.config.js`)
- [ ] Django settings.py 프로덕션 설정 확인
- [ ] 정적 파일 수집 경로 확인

### 3. 데이터베이스
- [ ] 마이그레이션 파일 최신 상태 확인
- [ ] 프로덕션 DB 연결 정보 확인
- [ ] Oracle Instant Client 설정 (필요시)

### 4. 빌드 및 테스트
- [ ] 로컬에서 `npm run build` 성공 확인
- [ ] 로컬에서 `python manage.py collectstatic` 성공 확인
- [ ] 로컬에서 `python manage.py migrate` 성공 확인
- [ ] API 엔드포인트 테스트 완료

### 5. 배포 플랫폼별 설정

#### Railway
- [ ] `railway_deploy.sh` 스크립트 검증
- [ ] Railway 프로젝트 생성 및 연결
- [ ] 환경 변수 설정 완료
- [ ] 빌드 명령어 설정: `bash railway_deploy.sh`
- [ ] 시작 명령어: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

#### Render
- [ ] `render.yaml` 설정 확인
- [ ] Render 서비스 생성
- [ ] 환경 변수 설정 완료
- [ ] 빌드 명령어 자동 실행 확인

#### Fly.io
- [ ] `fly.toml` 설정 확인
- [ ] `fly launch` 실행 완료
- [ ] 환경 변수 설정 완료 (`fly secrets set`)
- [ ] `fly deploy` 실행

### 6. 배포 후 확인
- [ ] 애플리케이션 정상 실행 확인
- [ ] 정적 파일 (CSS, JS, 이미지) 로드 확인
- [ ] React 앱 정상 렌더링 확인
- [ ] API 엔드포인트 동작 확인
- [ ] 데이터베이스 연결 확인
- [ ] 외부 API (카카오, OpenAI) 연동 확인
- [ ] 로그 확인 (에러 없음)

### 7. 보안 확인
- [ ] DEBUG=False 확인
- [ ] SECRET_KEY 노출되지 않음
- [ ] API 키 노출되지 않음
- [ ] HTTPS 설정 (가능한 경우)
- [ ] CORS 설정 적절히 구성

## 배포 명령어

### Railway
```bash
# 로컬에서 Railway CLI 설치 후
railway login
railway init
railway up
```

### Render
```bash
# GitHub에 푸시하면 자동 배포
git push origin main
```

### Fly.io
```bash
fly launch
fly secrets set DJANGO_SECRET_KEY=your-secret-key
fly deploy
```

## 문제 해결

### 정적 파일이 로드되지 않는 경우
1. `python manage.py collectstatic` 실행 확인
2. WhiteNoise 설정 확인
3. STATIC_ROOT 경로 확인

### React 앱이 표시되지 않는 경우
1. `npm run build` 실행 확인
2. 빌드 출력 경로 확인 (`staticfiles/react`)
3. Django URL 설정 확인

### 데이터베이스 연결 실패
1. 환경 변수 확인
2. Oracle Instant Client 설정 확인 (필요시)
3. 방화벽/네트워크 설정 확인

## 연락처 및 참고
- 프로젝트 문서: `COMET_PROMPT.md`
- 로컬 환경 설정: `LOCAL_ENV_PROMPT.md`

