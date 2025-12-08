# 데이터베이스 연결 테스트 결과

## 설정 확인

`config/settings.py` 파일의 데이터베이스 설정:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ.get('DB_NAME', 'MAPPP'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'project-db-campus.smhrd.com'),
        'PORT': os.environ.get('DB_PORT', '1524'),
    }
}
```

## 연결 정보

- **호스트**: `project-db-campus.smhrd.com`
- **포트**: `1524`
- **서비스명**: `MAPPP`
- **사용자**: `campus_24K_LG3_DX7_p3_4`
- **비밀번호**: 환경 변수에서 로드

## 테스트 방법

다음 명령어로 연결을 테스트할 수 있습니다:

```bash
python check_db.py
```

또는

```bash
python verify_db_connection.py
```

## 중요 사항

1. `.env` 파일이 있어야 환경 변수를 로드할 수 있습니다.
2. `.env` 파일이 없으면 스크립트가 환경 변수를 직접 설정합니다.
3. `oracledb` 패키지가 설치되어 있어야 합니다.

