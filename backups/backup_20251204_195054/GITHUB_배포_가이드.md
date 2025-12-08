# GitHub 배포 가이드

## ✅ 보안 설정 완료

모든 민감한 정보가 환경 변수로 이동되었습니다:
- ✅ `SECRET_KEY` → `DJANGO_SECRET_KEY` 환경 변수
- ✅ 데이터베이스 비밀번호 → `DB_PASSWORD` 환경 변수
- ✅ 데이터베이스 사용자명 → `DB_USER` 환경 변수
- ✅ API 키들 → 이미 환경 변수 사용 중

## 📋 배포 전 체크리스트

### 1. .env 파일 생성 (필수!)

프로젝트 루트에 `.env` 파일을 생성하고 다음 정보를 입력하세요:

```bash
# .env 파일 생성 (프로젝트 루트에)
# Windows: type nul > .env
# 또는 메모장으로 .env 파일 생성
```

`.env` 파일 내용:
```env
# Django Secret Key
DJANGO_SECRET_KEY=django-insecure-8zb-1$0d6^f=&c@v8-l2-9b*9ydnp7k3m0-s_y8gljjkvtiyt8

# 카카오 API 키
KAKAO_REST_API_KEY=your_kakao_rest_api_key_here
KAKAO_JS_KEY=your_kakao_js_key_here

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# Oracle 데이터베이스 설정
DB_NAME=MAPPP
DB_USER=campus_24K_LG3_DX7_p3_4
DB_PASSWORD=smhrd4
DB_HOST=project-db-campus.smhrd.com
DB_PORT=1524
```

⚠️ **중요**: `.env` 파일은 `.gitignore`에 포함되어 있어 GitHub에 업로드되지 않습니다.

### 2. .gitignore 확인

다음 항목들이 `.gitignore`에 포함되어 있는지 확인:
- ✅ `.env`
- ✅ `*.env`
- ✅ `venv/`
- ✅ `db.sqlite3`
- ✅ `__pycache__/`
- ✅ `*.pyc`

### 3. 테스트 파일 정리

다음 파일들은 배포 전에 삭제하거나 `.gitignore`에 추가하는 것을 고려하세요:
- `test_oracle_connection.py` (테스트용, 삭제하거나 `.gitignore`에 추가)
- `test_figma_conversion.py` (테스트용)

### 4. 민감한 정보 확인

다음 명령어로 하드코딩된 비밀번호나 API 키가 있는지 확인:

```bash
# settings.py에서 하드코딩된 비밀번호 확인
grep -i "password\|secret\|api_key" config/settings.py
```

### 5. SQL Developer 관련

- SQL Developer는 프로젝트 폴더에 없으므로 문제 없습니다.
- 만약 `tools/sqldeveloper/` 같은 폴더가 있다면 `.gitignore`에 추가하세요.

## 🚀 GitHub 배포 절차

### 1. Git 상태 확인
```bash
git status
```

### 2. 변경사항 스테이징
```bash
git add .
```

### 3. 커밋
```bash
git commit -m "feat: Oracle DB 연결 설정 및 보안 개선"
```

### 4. 원격 저장소 확인
```bash
git remote -v
```

### 5. 푸시
```bash
git push origin main
# 또는
git push origin master
```

## ⚠️ 주의사항

### 절대 GitHub에 올리면 안 되는 것들:
- ❌ `.env` 파일
- ❌ 실제 비밀번호나 API 키
- ❌ `db.sqlite3` (로컬 개발용 데이터베이스)
- ❌ `venv/` 폴더
- ❌ 개인 정보가 포함된 데이터 파일

### 안전하게 올려도 되는 것들:
- ✅ `env.example` (템플릿 파일)
- ✅ `settings.py` (환경 변수 사용)
- ✅ 소스 코드
- ✅ 문서 파일

## 🔍 배포 후 확인

1. GitHub 저장소에서 `.env` 파일이 없는지 확인
2. `settings.py`에 하드코딩된 비밀번호가 없는지 확인
3. 다른 사람이 클론했을 때 `env.example`을 참고하여 `.env` 파일을 만들 수 있는지 확인

## 📝 README 업데이트 권장

`README.md`에 다음 내용을 추가하는 것을 권장합니다:

```markdown
## 환경 설정

1. `.env` 파일 생성:
   ```bash
   cp env.example .env
   ```

2. `.env` 파일에 실제 값 입력:
   - `DJANGO_SECRET_KEY`: Django 시크릿 키
   - `DB_USER`, `DB_PASSWORD`: 데이터베이스 인증 정보
   - `OPENAI_API_KEY`, `KAKAO_REST_API_KEY` 등: API 키

3. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

4. 데이터베이스 마이그레이션:
   ```bash
   python manage.py migrate
   ```
```

## ✅ 최종 확인

배포 전에 다음을 확인하세요:

- [ ] `.env` 파일이 프로젝트에 있지만 Git에 추가되지 않음 (`git status`로 확인)
- [ ] `settings.py`에 하드코딩된 비밀번호 없음
- [ ] `env.example` 파일이 최신 상태
- [ ] `.gitignore`에 필요한 항목들이 모두 포함됨
- [ ] 테스트 파일 정리 완료

이제 안전하게 GitHub에 배포할 수 있습니다! 🎉

