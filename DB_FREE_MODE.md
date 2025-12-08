# DB 연결 없이 서버 실행하기

DB가 잠겼거나 연결할 수 없을 때도 Django 서버를 실행할 수 있습니다.

## 방법 1: 환경 변수 설정 (.env 또는 환경 변수)

`.env` 파일에 다음을 추가하거나, 환경 변수로 설정:

```bash
DISABLE_DB=true
```

또는 PowerShell에서:

```powershell
$env:DISABLE_DB="true"
python manage.py runserver
```

## 방법 2: 배치 파일 사용

`start_server_no_db.bat` 파일을 실행:

```batch
start_server_no_db.bat
```

## 방법 3: 직접 실행

PowerShell이나 CMD에서:

```bash
# Windows CMD
set DISABLE_DB=true && python manage.py runserver

# Windows PowerShell
$env:DISABLE_DB="true"; python manage.py runserver
```

## 주의사항

1. **서버는 정상 시작됩니다**: Django 서버는 DB 연결 없이도 시작할 수 있습니다.

2. **DB를 사용하는 API는 명확한 에러 메시지 반환**: 
   - DB 조회가 필요한 API 호출 시 `503 Service Unavailable` 상태와 함께 명확한 에러 메시지를 반환합니다.
   - 예: 제품 목록, 포트폴리오 조회, 온보딩 데이터 저장 등
   - 에러 메시지: "데이터베이스 연결이 비활성화되었습니다. (DISABLE_DB=true)"

3. **정상 작동하는 것들**:
   - 정적 파일 서빙 (CSS, JavaScript, 이미지)
   - 템플릿 렌더링 (HTML 페이지)
   - DB를 사용하지 않는 API 엔드포인트
   - Django ORM을 사용하는 기능 (SQLite 사용, 예: 온보딩 세션 저장)
   - 프론트엔드 UI/UX 확인

4. **부분적으로 작동하는 것들**:
   - 온보딩 설문: Django DB(SQLite)에는 저장되지만 Oracle DB에는 저장되지 않음
   - 제품 목록: Django ORM으로 저장된 제품만 조회 가능 (Oracle DB의 제품은 조회 불가)

5. **DB 다시 연결하려면**:
   - `DISABLE_DB` 환경 변수를 제거하거나 `false`로 설정
   - DB 잠금 해제 후 서버 재시작

## DB 연결 상태 확인

`/api/health/` 엔드포인트로 확인 가능:

```bash
curl http://localhost:8000/api/health/
```

응답:
- `"database": "connected"` - DB 연결됨
- `"database": "disconnected"` - DB 연결 안됨

## 설정 옵션

| 환경 변수 | 설명 | 기본값 |
|---------|------|--------|
| `DISABLE_DB` | DB 연결 완전 비활성화 | `false` |
| `USE_ORACLE` | Oracle DB 사용 여부 | `false` (SQLite 사용) |

DB 연결 없이 실행: `DISABLE_DB=true`
Oracle 사용 (DB 잠금 해제 후): `USE_ORACLE=true`
SQLite 사용: 환경 변수 없음 또는 `USE_ORACLE=false`
