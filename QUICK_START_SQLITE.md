# SQLite로 빠른 테스트 시작 가이드

## 문제 상황

Oracle 11g는 Django 4.x+의 IDENTITY 컬럼을 지원하지 않아 `ORA-02000: missing ALWAYS keyword` 오류가 발생합니다.

## 즉시 해결 (5분 소요)

### 방법 1: .env 파일 사용 (가장 간단, 모든 OS 지원)

`.env` 파일에 추가:
```env
USE_SQLITE_FOR_TESTING=True
```

그 다음:
```bash
python manage.py migrate
python test_content_based_filtering.py
```

### 방법 2: 환경 변수 사용

**Linux/Mac (Bash)**:
```bash
USE_SQLITE_FOR_TESTING=true python test_content_based_filtering.py
```

**Windows (PowerShell)**:
```powershell
$env:USE_SQLITE_FOR_TESTING="true"
python test_content_based_filtering.py
```

**Windows (CMD)**:
```cmd
set USE_SQLITE_FOR_TESTING=true
python test_content_based_filtering.py
```

### 방법 2: settings.py 직접 수정

`config/settings.py`에서 SQLite로 변경:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### 방법 3: .env 파일 사용

`.env` 파일에 추가:

```env
USE_SQLITE_FOR_TESTING=True
```

## 실행 순서

### .env 파일 사용 (권장)

`.env` 파일에 `USE_SQLITE_FOR_TESTING=True` 추가 후:

```bash
# 1. SQLite 모드로 마이그레이션 실행
python manage.py migrate

# 2. 테스트 데이터 생성 (선택사항)
python manage.py shell
# >>> from api.models import Product, ProductSpec
# >>> Product.objects.create(name="LG OLED TV", category="TV", price=1500000, is_active=True)

# 3. 테스트 실행
python test_content_based_filtering.py
```

### 환경 변수 사용

**Linux/Mac**:
```bash
USE_SQLITE_FOR_TESTING=true python manage.py migrate
USE_SQLITE_FOR_TESTING=true python test_content_based_filtering.py
```

**Windows PowerShell**:
```powershell
$env:USE_SQLITE_FOR_TESTING="true"
python manage.py migrate
python test_content_based_filtering.py
```

**Windows CMD**:
```cmd
set USE_SQLITE_FOR_TESTING=true
python manage.py migrate
python test_content_based_filtering.py
```

## 예상 결과

```
[테스트] SQLite 모드로 실행합니다 (Oracle 11g 호환성 문제 해결)
============================================================
콘텐츠 기반 필터링 테스트
============================================================

=== TASTE 문자열 파싱 테스트 ===
  ✅ 정상 통과

=== 제품 피처 추출 테스트 ===
제품: LG OLED TV
  추출된 피처: ['TV', 'OLED', '4K', '스마트']
  ✅ 정상 통과

=== 벡터화 테스트 ===
  ✅ 정상 통과

=== 코사인 유사도 테스트 ===
  ✅ 정상 통과

=== 점수 등급 부여 테스트 ===
  ✅ 정상 통과

=== TASTE 문자열 기반 추천 테스트 ===
  ✅ 정상 통과 (제품 데이터가 있으면)
```

## Oracle DB로 복귀

테스트 완료 후 Oracle DB로 복귀하려면:

**Linux/Mac**:
```bash
unset USE_SQLITE_FOR_TESTING
```

**Windows PowerShell**:
```powershell
Remove-Item Env:\USE_SQLITE_FOR_TESTING
```

**또는 .env 파일에서 제거**:
```env
# USE_SQLITE_FOR_TESTING=True  # 주석 처리
```

## 주의사항

1. **SQLite는 테스트용**: 프로덕션에서는 Oracle DB 사용
2. **마이그레이션**: SQLite와 Oracle DB는 별도 마이그레이션 필요
3. **데이터**: SQLite 데이터는 Oracle DB와 공유되지 않음

## .env 파일 25번째 줄 수정

`.env` 파일의 25번째 줄에 주석이 잘못 포함되어 있을 수 있습니다:

```env
# 잘못된 예
KAKAO_JS_KEY=abc # 주석

# 올바른 예
KAKAO_JS_KEY=abc
# 주석은 별도 줄에 작성
```

## 장기적 해결책

1. **Oracle 업그레이드**: Oracle 12c 이상으로 업그레이드 (IDENTITY 컬럼 지원)
2. **Django 다운그레이드**: Django 3.2.x 사용 (권장하지 않음)
3. **커스텀 마이그레이션**: Oracle 11g 호환 마이그레이션 작성 (복잡함)

## 참고

- Oracle 11g는 EOL(End-of-Life) 상태
- 장기적으로는 Oracle 12c+ 또는 다른 DB로 마이그레이션 권장
- 개발/테스트 단계에서는 SQLite 사용이 가장 빠름

