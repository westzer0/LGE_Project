# Django 서버 실행 가이드

## 기본 명령어

### 1. 가상환경 활성화
```powershell
# 프로젝트 디렉토리로 이동
cd "C:\Users\134\Desktop\DX Project"

# 가상환경 활성화
.\venv\Scripts\Activate.ps1
```

### 2. Django 서버 시작
```powershell
python manage.py runserver
```

또는 특정 포트 지정:
```powershell
python manage.py runserver 8000
```

### 3. 브라우저에서 접속
서버 시작 후 아래 주소로 접속:
- http://127.0.0.1:8000/
- http://localhost:8000/

## 서버 실행 예시

```powershell
# 1. 프로젝트 디렉토리로 이동
cd "C:\Users\134\Desktop\DX Project"

# 2. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 3. 서버 실행
python manage.py runserver
```

## 서버 중지
- 터미널에서 `Ctrl + C` 누르기

## 유용한 관리 명령어

### 데이터베이스 마이그레이션
```powershell
python manage.py makemigrations  # 변경사항 감지
python manage.py migrate          # DB에 적용
```

### 관리자 계정 생성
```powershell
python manage.py createsuperuser
```

### Django Shell 접속
```powershell
python manage.py shell
```

## 문제 해결

### 포트가 이미 사용 중인 경우
```powershell
# 다른 포트 사용 (예: 8080)
python manage.py runserver 8080
```

### 가상환경이 활성화되지 않는 경우
```powershell
# PowerShell 실행 정책 확인
Get-ExecutionPolicy

# 실행 정책 변경 (필요한 경우)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

