# 로컬 환경 전용 요소 안내 프롬프트

 

이 프로젝트에는 GitHub에 올라가지 않은 로컬 환경 전용 요소들이 있습니다. 새로운 로컬 환경에서 작업할 때 다음 사항들을 참고하세요.

 

## 필수 로컬 환경 요소

 

### 1. Node.js 바이너리

- **경로**: `node-v24.11.1-x64/` (프로젝트 루트 또는 상위 디렉토리)

- **설명**: Node.js v24.11.1 x64 버전의 로컬 바이너리

- **용도**: 프로젝트의 Node.js 런타임 의존성

- **설치 방법**:

  - 공식 Node.js 웹사이트에서 다운로드하거나

  - 기존 로컬 환경에서 해당 디렉토리를 복사

 

### 2. Cursor Talk to Figma MCP 서버

- **경로**: `cursor-talk-to-figma-mcp-main/` (프로젝트 루트 또는 상위 디렉토리)

- **설명**: Cursor와 Figma를 연동하는 MCP (Model Context Protocol) 서버

- **용도**: Figma 디자인과 Cursor 간의 통신을 위한 MCP 서버

- **설치 방법**:

  - GitHub에서 `cursor-talk-to-figma-mcp` 저장소를 클론하거나

  - 기존 로컬 환경에서 해당 디렉토리를 복사

  - MCP 서버 설정이 필요할 수 있음 (Cursor 설정 파일 확인)

 

### 3. ngrok 설정 및 사용

- **경로**: `ngrok/ngrok.exe` (프로젝트 내부에 설치됨)

- **설명**: 로컬 서버를 인터넷에 공개하기 위한 터널링 도구

- **용도**: 카카오 API 연동 등 외부에서 접근 가능한 URL 필요 시 사용

 

#### ngrok 초기 설정

```powershell

# 방법 1: 자동 설정 스크립트 실행

powershell -ExecutionPolicy Bypass -File setup_ngrok.ps1

 

# 방법 2: 간단 버전 (토큰을 인자로 전달)

powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_NGROK_TOKEN

```

 

**ngrok 인증 토큰 발급**: https://dashboard.ngrok.com/get-started/your-authtoken

 

#### ngrok으로 서버 실행

**PowerShell에서 실행 시:**
```powershell
# Django 서버 + ngrok 터널 자동 시작
.\start_server_fixed.bat
```

**CMD (명령 프롬프트)에서 실행 시:**
```batch
# Django 서버 + ngrok 터널 자동 시작
start_server_fixed.bat
```

**또는 수동으로:**
```powershell
# 터미널 1: Django 서버 시작
python manage.py runserver 8000

# 터미널 2: ngrok 터널 시작
.\ngrok\ngrok.exe http 8000
```

 

#### ngrok 관련 스크립트 파일

- `setup_ngrok.ps1` - ngrok 자동 다운로드 및 설정

- `setup_ngrok_simple.ps1` - 간단 버전 설정 스크립트

- `start_ngrok.bat` - ngrok 터널만 시작

- `start_server.bat` - Django 서버 + ngrok 시작 (기본)

- `start_server_fixed.bat` - Django 서버 + ngrok 시작 (가상환경 포함)

- `restart_server.bat` - Django 서버 재시작

- `check_status.bat` - 서버 및 ngrok 상태 확인

 

**중요**: ngrok 창에서 생성된 Forwarding URL (예: `https://xxxx-xxx-xxx.ngrok-free.app`)을 카카오 개발자 콘솔에 등록해야 합니다.

 

## 기타 로컬 전용 요소 (.gitignore에 포함됨)

 

### Python 관련

- `venv/` - Python 가상환경

- `__pycache__/` - Python 캐시 파일

- `*.pyc`, `*.pyo` - 컴파일된 Python 파일

 

### Node.js 관련

- `node_modules/` - npm 패키지 의존성

 

### 데이터베이스

- `db.sqlite3` - SQLite 데이터베이스 파일

- `libs/oracle_client/` - Oracle Instant Client (용량이 커서 Git 제외)

 

### 환경 변수 및 시크릿

- `.env` - 환경 변수 파일 (API 키 등)

- `*.env` - 기타 환경 변수 파일

 

### 로그 및 임시 파일

- `logs/` - 애플리케이션 로그 파일

- `backups/` - 백업 파일

- `*.tmp`, `*.temp` - 임시 파일

 

### IDE 설정

- `.vscode/` - VS Code 설정

- `.idea/` - IntelliJ/PyCharm 설정

 

## 초기 설정 가이드 (전체 프로세스)

 

새로운 로컬 환경에서 프로젝트를 설정할 때:

 

### 1. Node.js 설정

- `node-v24.11.1-x64/` 디렉토리가 있는지 확인

- 없으면 Node.js v24.11.1을 설치하거나 해당 버전의 바이너리를 준비

 

### 2. MCP 서버 설정

- `cursor-talk-to-figma-mcp-main/` 디렉토리 확인

- Cursor의 MCP 설정에서 해당 서버 경로가 올바르게 설정되어 있는지 확인

 

### 3. Python 가상환경 설정

```bash

python -m venv venv

# Windows

venv\Scripts\activate

# Linux/Mac

source venv/bin/activate

 

pip install -r requirements.txt

```

 

### 4. Node.js 의존성 설치

```bash

npm install

```

 

### 5. 환경 변수 설정

- `env.example` 파일을 참고하여 `.env` 파일 생성

- 필요한 API 키 및 설정 값 입력:

  - `DJANGO_SECRET_KEY` - Django 시크릿 키

  - `KAKAO_REST_API_KEY`, `KAKAO_JS_KEY` - 카카오 API 키

  - `OPENAI_API_KEY` - OpenAI API 키

  - Oracle DB 사용 시: `ORACLE_*` 환경 변수들

 

### 6. 데이터베이스 초기화

```bash

# SQLite 사용 (기본)

python manage.py migrate

 

# Oracle 사용

# .env 파일에 USE_ORACLE=true 설정

# ORACLE_INSTANT_CLIENT_PATH 설정 확인

python manage.py migrate

```

 

### 7. ngrok 설정 및 서버 실행

```powershell

# ngrok 초기 설정 (최초 1회만)

powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_NGROK_TOKEN

 

# 서버 시작 (Django + ngrok)
# PowerShell에서는 .\ 접두사 필요
.\start_server_fixed.bat

 

# 또는 수동으로:

# 터미널 1: python manage.py runserver 8000

# 터미널 2: .\ngrok\ngrok.exe http 8000

```

 

### 8. 서버 상태 확인

**PowerShell:**
```powershell
.\check_status.bat
```

**CMD:**
```batch
check_status.bat
```

 

## 주의사항

 

- 위의 로컬 전용 요소들은 Git에 커밋되지 않으므로, 각 로컬 환경에서 별도로 설정해야 합니다.

- `node-v24.11.1-x64`와 `cursor-talk-to-figma-mcp-main`은 프로젝트 외부에 있을 수 있으므로, 경로를 확인하고 필요시 Cursor 설정을 업데이트하세요.

- Oracle Instant Client는 용량이 크므로 Git에 포함되지 않으며, Oracle 데이터베이스를 사용하는 경우 별도로 설치해야 합니다.

- ngrok URL은 매번 실행 시 변경될 수 있으므로, 카카오 개발자 콘솔에 새로운 URL을 등록해야 할 수 있습니다.

- `start_server_fixed.bat`는 가상환경을 자동으로 활성화하므로 권장됩니다.

- **PowerShell 사용 시**: PowerShell에서는 현재 디렉토리의 배치 파일을 실행할 때 `.\` 접두사가 필요합니다 (예: `.\start_server_fixed.bat`). CMD에서는 접두사 없이 실행 가능합니다.
