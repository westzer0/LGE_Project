# SESSION_ID 생성 및 변환 문제 분석 및 해결 방안

## 문제 상황

### 발견된 문제
1. **UUID 형식 SESSION_ID**: 정상적으로 생성되고 저장됨
   - 예: `888f6879-56eb-4f0b-874a-ae6708894cf5`
   - 예: `1ea06eea-20e5-439d-92d2-661b5c2d3b8d`

2. **타임스탬프 기반 SESSION_ID**: 여전히 생성되고 있음
   - 예: `1765270756659` (밀리초 타임스탬프)
   - 총 1005개의 타임스탬프 기반 SESSION_ID 발견

### 원인 분석

#### 1. 프론트엔드에서 타임스탬프 기반 ID 생성
- `api/static/js/onboarding-flow.js`의 `generateSessionId()` 함수:
  ```javascript
  generateSessionId() {
      return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  ```
  - 이 함수는 타임스탬프를 포함한 문자열을 생성
  - 하지만 실제로는 `sess_` 접두사가 있어서 숫자만 있는 것은 아님

#### 2. 백엔드에서 타임스탬프 변환 로직
- `api/views.py` 853-863번째 줄:
  ```python
  # session_id가 숫자 문자열이면 UUID로 변환 (타임스탬프 기반 ID 방지)
  try:
      timestamp = int(session_id)
      namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
      session_id = str(uuid.uuid5(namespace, f"onboarding_session_{timestamp}"))
  except (ValueError, TypeError):
      pass
  ```
  - 숫자 문자열이면 타임스탬프로 인식하고 UUID5로 변환
  - 하지만 **이미 DB에 타임스탬프로 저장된 레코드는 변환되지 않음**

#### 3. 실제 문제점
- 프론트엔드에서 타임스탬프 기반 ID를 생성하는 경로가 있음
- 백엔드에서 변환하지만, 이미 저장된 데이터는 그대로 남아있음
- 두 가지 형식이 혼재되어 있음

## 해결 방안

### 1. 즉시 조치: 프론트엔드에서 타임스탬프 기반 ID 생성 차단

#### `api/static/js/onboarding-flow.js` 수정
```javascript
generateSessionId() {
    // UUID v4 형식으로 생성 (완전히 고유한 ID 보장)
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
    })
}
```

### 2. 백엔드 변환 로직 개선

#### `api/views.py` 853-863번째 줄 개선
- 타임스탬프를 UUID로 변환하는 로직은 유지하되, 변환 전에 DB에 이미 존재하는지 확인
- 변환된 UUID로도 조회하여 중복 방지

### 3. 기존 데이터 마이그레이션 (선택사항)

타임스탬프 기반 SESSION_ID를 UUID로 변환하는 마이그레이션 스크립트 작성

## 권장 조치사항

1. **즉시**: 프론트엔드에서 타임스탬프 기반 ID 생성 차단
2. **단기**: 백엔드 변환 로직 개선
3. **중기**: 기존 타임스탬프 기반 SESSION_ID 마이그레이션 (필요시)

