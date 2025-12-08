# SQLite로 빠른 테스트 시작 가이드 (PowerShell)

## PowerShell 명령어

### 방법 1: 환경 변수 설정 후 실행 (권장)

```powershell
# PowerShell에서 환경 변수 설정
$env:USE_SQLITE_FOR_TESTING="true"

# 마이그레이션 실행
python manage.py migrate

# 테스트 실행
python test_content_based_filtering.py

# 환경 변수 제거 (선택사항)
Remove-Item Env:\USE_SQLITE_FOR_TESTING
```

### 방법 2: 한 줄로 실행

```powershell
# 환경 변수 설정과 함께 실행
$env:USE_SQLITE_FOR_TESTING="true"; python manage.py migrate
$env:USE_SQLITE_FOR_TESTING="true"; python test_content_based_filtering.py
```

### 방법 3: .env 파일 사용 (가장 간단)

`.env` 파일에 추가:
```env
USE_SQLITE_FOR_TESTING=True
```

그 다음 일반 명령어로 실행:
```powershell
python manage.py migrate
python test_content_based_filtering.py
```

## 전체 실행 순서 (PowerShell)

```powershell
# 1. 가상환경 활성화 (이미 활성화되어 있다면 생략)
.\venv\Scripts\Activate.ps1

# 2. 환경 변수 설정
$env:USE_SQLITE_FOR_TESTING="true"

# 3. 마이그레이션 실행
python manage.py migrate

# 4. 테스트 실행
python test_content_based_filtering.py

# 5. 환경 변수 제거 (선택사항)
Remove-Item Env:\USE_SQLITE_FOR_TESTING
```

## PowerShell vs Bash 명령어 비교

| 작업 | Bash (Linux/Mac) | PowerShell (Windows) |
|------|------------------|----------------------|
| 환경 변수 설정 | `export USE_SQLITE_FOR_TESTING=true` | `$env:USE_SQLITE_FOR_TESTING="true"` |
| 환경 변수 확인 | `echo $USE_SQLITE_FOR_TESTING` | `$env:USE_SQLITE_FOR_TESTING` |
| 환경 변수 제거 | `unset USE_SQLITE_FOR_TESTING` | `Remove-Item Env:\USE_SQLITE_FOR_TESTING` |
| 한 줄 실행 | `USE_SQLITE_FOR_TESTING=true python ...` | `$env:USE_SQLITE_FOR_TESTING="true"; python ...` |

## .env 파일 사용 (가장 권장)

`.env` 파일에 추가하면 PowerShell, CMD, Bash 모두에서 동일하게 작동:

```env
USE_SQLITE_FOR_TESTING=True
```

그 다음:
```powershell
python manage.py migrate
python test_content_based_filtering.py
```

## 문제 해결

### PowerShell 실행 정책 오류

```powershell
# 실행 정책 확인
Get-ExecutionPolicy

# 실행 정책 변경 (관리자 권한 필요)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 환경 변수가 적용되지 않는 경우

```powershell
# 환경 변수 확인
$env:USE_SQLITE_FOR_TESTING

# 강제로 설정
$env:USE_SQLITE_FOR_TESTING="true"
python test_content_based_filtering.py
```

## 참고

- PowerShell에서 환경 변수는 현재 세션에만 유효합니다
- 새 PowerShell 창을 열면 환경 변수가 사라집니다
- 영구적으로 설정하려면 `.env` 파일 사용을 권장합니다

