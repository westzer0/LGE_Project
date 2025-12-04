# Figma 이미지 변환 테스트 가이드

## ✅ API 키 확인 완료

`.env` 파일에 OpenAI API 키가 설정되어 있어서 바로 사용 가능합니다.

## 테스트 방법

### 방법 1: Python 코드로 테스트

```python
# test_figma_conversion.py
from api.services.figma_to_code_service import figma_to_code_service
import os

# Figma 이미지 파일 경로
image_path = 'data/피그마UI/1. LG Main.pdf'

# 변환 실행
result = figma_to_code_service.convert_image_to_code(
    image_path=image_path,
    design_type='web_page'
)

if result.get('success'):
    print("✅ 변환 성공!")
    print("\n=== HTML ===")
    print(result['html'][:500])  # 처음 500자만 출력
    
    print("\n=== CSS ===")
    print(result['css'][:500])
    
    print("\n=== 색상 ===")
    print(result['colors'])
    
    print("\n=== 폰트 ===")
    print(result['fonts'])
    
    # 파일로 저장
    saved_files = figma_to_code_service.save_code_to_files(
        result,
        'output/figma_converted'
    )
    print(f"\n✅ 파일 저장 완료: {saved_files}")
else:
    print(f"❌ 변환 실패: {result.get('error')}")
```

### 방법 2: Django 관리 명령어로 테스트

```bash
python manage.py shell
```

```python
from api.services.figma_to_code_service import figma_to_code_service

# PDF 파일 테스트
result = figma_to_code_service.convert_image_to_code(
    image_path='data/피그마UI/1. LG Main.pdf',
    design_type='web_page'
)

print(result['success'])
print(result.get('html', '')[:200])
```

### 방법 3: API 엔드포인트로 테스트

```bash
# 서버 실행
python manage.py runserver

# 다른 터미널에서
curl -X POST http://localhost:8000/api/figma-to-code/ \
  -F "image=@data/피그마UI/1. LG Main.pdf" \
  -F "design_type=web_page" \
  -F "save_files=true"
```

또는 Postman/Thunder Client 사용:
- URL: `POST http://localhost:8000/api/figma-to-code/`
- Body: form-data
  - `image`: 파일 선택 (PDF, PNG, JPG)
  - `design_type`: `web_page` (선택)
  - `save_files`: `true` (선택)

## 주의사항

1. **PDF 파일**: Vision API는 이미지 파일(PNG, JPG)을 더 잘 처리합니다.
   - PDF는 먼저 이미지로 변환하는 것을 권장합니다.

2. **파일 크기**: Vision API는 최대 20MB까지 지원합니다.

3. **비용**: Vision API는 이미지당 비용이 발생합니다.
   - GPT-4o: 저해상도 $0.01, 고해상도 $0.03 per image

## 테스트할 수 있는 파일

`data/피그마UI/` 폴더에 있는 파일들:
- `1. LG Main.pdf`
- `1-1. 가전패키지추천 _ 안내 화면.pdf`
- `Component.pdf`
- `Frame 25564.pdf`
- 기타 PDF 파일들

## 예상 결과

변환 성공 시:
- HTML 구조 코드
- CSS 스타일 코드
- JavaScript 인터랙션 코드
- 컴포넌트 목록
- 색상 팔레트
- 폰트 정보
- 레이아웃 정보
- 반응형 브레이크포인트

## 문제 해결

### "OpenAI API를 사용할 수 없습니다" 오류
- `.env` 파일이 프로젝트 루트에 있는지 확인
- `python-dotenv`가 설치되어 있는지 확인: `pip install python-dotenv`
- Django 서버 재시작

### "JSON 파싱 실패" 오류
- Vision API 응답이 JSON 형식이 아닐 수 있음
- 프롬프트를 조정하거나 모델을 변경 필요

### "파일을 찾을 수 없습니다" 오류
- 이미지 파일 경로 확인
- 상대 경로가 아닌 절대 경로 사용 권장

