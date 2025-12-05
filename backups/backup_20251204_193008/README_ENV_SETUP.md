# 환경 변수 설정 가이드

## API 키 설정 방법

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 입력하세요.

### 1. .env 파일 생성

프로젝트 루트 디렉토리(`C:\Users\134\Desktop\DX Project`)에 `.env` 파일을 생성합니다.

### 2. .env 파일 내용

```env
# 카카오 API 키
# 발급: https://developers.kakao.com/console/app
KAKAO_REST_API_KEY=여기에_카카오_REST_API_키_입력
KAKAO_JS_KEY=여기에_카카오_JavaScript_키_입력

# OpenAI API 키
# 발급: https://platform.openai.com/api-keys
OPENAI_API_KEY=여기에_OpenAI_API_키_입력
```

### 3. Windows에서 .env 파일 생성 방법

#### 방법 1: PowerShell에서 생성
```powershell
cd "C:\Users\134\Desktop\DX Project"
@"
# 카카오 API 키
KAKAO_REST_API_KEY=여기에_키_입력
KAKAO_JS_KEY=여기에_키_입력

# OpenAI API 키
OPENAI_API_KEY=여기에_키_입력
"@ | Out-File -FilePath .env -Encoding UTF8
```

#### 방법 2: 메모장으로 생성
1. 메모장을 엽니다
2. 위의 내용을 입력합니다
3. "다른 이름으로 저장" → 파일명: `.env` (맨 앞에 점 포함)
4. 인코딩: UTF-8 선택
5. 저장 위치: 프로젝트 루트 디렉토리

#### 방법 3: 명령 프롬프트에서 생성
```cmd
cd C:\Users\134\Desktop\DX Project
type nul > .env
notepad .env
```

### 4. python-dotenv 설치

```bash
pip install python-dotenv
```

또는

```powershell
pip install python-dotenv
```

### 5. 설정 확인

Django 서버를 시작하면 콘솔에 API 키 설정 상태가 표시됩니다:

```
✅ .env 파일 로드 완료: C:\Users\134\Desktop\DX Project\.env
[API Keys Status]
  KAKAO_JS_KEY: ✅ 설정됨
  OPENAI_API_KEY: ✅ 설정됨
```

### 6. API 키 발급 링크

- **카카오 API**: https://developers.kakao.com/console/app
- **OpenAI API**: https://platform.openai.com/api-keys

### 주의사항

- `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 올라가지 않습니다.
- `.env` 파일에는 실제 API 키를 입력하세요.
- `env.example` 파일은 템플릿일 뿐 실제 API 키를 입력하지 마세요.

