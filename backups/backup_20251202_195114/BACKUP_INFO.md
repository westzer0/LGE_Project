# 백업 정보

## 백업 일시
- **날짜**: 2025-12-02
- **시간**: 19:51:14
- **백업 디렉토리**: `backups/backup_20251202_195114`

## Git 커밋 정보
- **커밋 해시**: e1b8476
- **커밋 메시지**: 백업: 작업 내용 저장 - 2025-12-02 19:51:11
- **변경된 파일**: 80개
- **추가된 라인**: 1,619줄
- **삭제된 라인**: 1,097줄

## 백업된 주요 내용

### 수정된 파일
- `api/templates/onboarding.html` - 온보딩 페이지 메인
- `api/templates/onboarding_step2.html` - 온보딩 2단계
- `api/templates/onboarding_step3.html` - 온보딩 3단계
- `api/templates/onboarding_step4.html` - 온보딩 4단계
- `api/templates/onboarding_step5.html` - 온보딩 5단계
- `api/templates/onboarding_step6.html` - 온보딩 6단계
- `api/templates/result.html` - 결과 페이지
- `api/views.py` - 뷰 로직
- `config/settings.py` - 설정 파일
- `config/urls.py` - URL 설정

### 새로 추가된 이미지 파일
- `api/static/images/신규 가전제품/` - 새로운 가전제품 이미지들
- `api/static/images/신규온보딩/` - 온보딩 관련 이미지들

## 백업 복원 방법

1. Git을 사용한 복원:
   ```bash
   git checkout e1b8476
   ```

2. 파일 복원:
   ```bash
   # 백업 디렉토리에서 필요한 파일을 복사
   cp -r backups/backup_20251202_195114/api/* api/
   cp -r backups/backup_20251202_195114/config/* config/
   ```

## 참고사항
- 모든 변경사항은 Git에 커밋되었습니다.
- 데이터베이스 파일(`db.sqlite3`)도 백업에 포함되어 있습니다.
- 백업은 프로젝트 루트의 `backups/backup_20251202_195114/` 디렉토리에 저장되었습니다.





