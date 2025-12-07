# 🪰 Fly.io 배포 가이드 (Sleep 없음!)

Render보다 빠르고 sleep이 없는 무료 옵션입니다.

## 🚀 배포하기

### 1단계: Fly.io CLI 설치

**Windows (PowerShell):**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**또는 수동 설치:**
1. https://fly.io/docs/getting-started/installing-flyctl/ 접속
2. Windows용 다운로드

### 2단계: 로그인
```bash
fly auth login
```
브라우저가 열리면 GitHub로 로그인

### 3단계: 프로젝트 초기화
```bash
fly launch
```

질문에 답변:
- App name: `lge-project` (원하는 이름)
- Region: `icn` (서울) 또는 `nrt` (도쿄)
- PostgreSQL: No (Oracle 사용)
- Redis: No

### 4단계: 환경 변수 설정
```bash
fly secrets set DJANGO_SECRET_KEY="your-secret-key"
fly secrets set DJANGO_DEBUG="False"
fly secrets set ALLOWED_HOSTS="lge-project.fly.dev"
fly secrets set KAKAO_REST_API_KEY="your-key"
fly secrets set KAKAO_JS_KEY="your-key"
fly secrets set OPENAI_API_KEY="your-key"
fly secrets set USE_ORACLE="true"
fly secrets set ORACLE_HOST="project-db-campus.smhrd.com"
fly secrets set ORACLE_PORT="1524"
fly secrets set ORACLE_USER="campus_24K_LG3_DX7_p3_4"
fly secrets set ORACLE_PASSWORD="your-password"
fly secrets set ORACLE_SID="xe"
```

### 5단계: 배포
```bash
fly deploy
```

### 6단계: 완료!
배포 완료 후 `https://lge-project.fly.dev` 접속!

## ✅ 장점
- ✅ Sleep 없음 (항상 실행)
- ✅ 전 세계 CDN
- ✅ 빠른 속도
- ✅ 완전 무료 (제한적)

## ⚠️ 주의사항
- Dockerfile 필요 (이미 생성됨)
- CLI 사용 필요
- 무료 플랜: 월 3개 VM, 160GB 네트워크

## 🔧 문제 해결
```bash
# 로그 확인
fly logs

# 앱 상태 확인
fly status

# 재배포
fly deploy
```

