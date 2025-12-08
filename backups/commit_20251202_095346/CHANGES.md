# 변경사항 요약 (2025-12-02 09:53:46)

## 주요 변경사항

### 1. main.html 업데이트
- **Group1.png → Group7.png로 변경**
  - 이미지 경로: `{% static 'images/Group1.png' %}` → `{% static 'images/Group7.png' %}`

- **Navigation Buttons 위치 변경**
  - Group7.png와 Group2.png 사이로 이동
  - 맞춤 추천, 패키지 구성, 견적 및 구매 버튼

- **가전 패키지 추천받기 버튼 업데이트**
  - button1.png → button.png로 변경
  - 버튼 크기 조절: max-width: 400px
  - 배경 투명 처리

### 2. config/settings.py 업데이트
- **STATICFILES_DIRS 추가**
  - assets 폴더를 static 파일 디렉토리로 추가
  ```python
  STATICFILES_DIRS = [
      BASE_DIR / 'assets',
  ]
  ```

### 3. 새로 추가된 파일
- `api/static/images/Group7.png`
- `api/static/images/button.png`

## 파일 구조 변경

### 이전 구조:
1. Navigation Buttons
2. Group1 Image
3. Group2 Image

### 현재 구조:
1. Group7 Image
2. Navigation Buttons
3. Group2 Image

## 백업 정보
- 백업 날짜: 2025-12-02 09:53:46
- 백업 폴더: `backups/commit_20251202_095346/`
- 백업된 파일:
  - main.html
  - settings.py






