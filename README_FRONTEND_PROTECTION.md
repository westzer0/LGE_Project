# 프론트엔드 보호 시스템

## 🛡️ 개요

이 프로젝트는 프론트엔드 디자인의 무결성을 보장하기 위한 보호 시스템을 포함하고 있습니다.

## 📋 구성 요소

### 1. 스타일 가이드 문서
- **파일**: `FRONTEND_STYLE_GUIDE.md`
- **목적**: 프론트엔드 디자인의 핵심 규칙 문서화
- **용도**: 개발 시 참고 문서

### 2. 검증 스크립트
- **파일**: `validate_frontend_style.py`
- **목적**: 자동으로 스타일 규칙 준수 여부 검증
- **사용법**: 
  ```bash
  python validate_frontend_style.py
  ```

### 3. Git Pre-commit Hook
- **파일**: `.git/hooks/pre-commit`
- **목적**: 커밋 전 자동 검증으로 스타일 위반 방지
- **동작**: 스타일 검증 실패 시 커밋 거부

## 🚀 사용 방법

### 수동 검증
프론트엔드를 수정한 후, 커밋하기 전에 검증 스크립트를 실행하세요:

**Windows PowerShell:**
```powershell
.\validate_frontend.bat
```

**또는 배치 파일 직접 실행:**
```batch
validate_frontend.bat
```

**또는 Python 직접 실행:**
```bash
python validate_frontend_style.py
```

### 자동 검증 (Git Hook)
Git hook이 설정되어 있으면, 커밋 시 자동으로 검증이 실행됩니다.

**Windows에서 Git Hook 활성화:**

**PowerShell:**
```powershell
.\setup_git_hook.ps1
```

**또는 배치 파일:**
```batch
.\setup_git_hook.bat
```

**또는 수동으로:**
```powershell
# Git hook 파일 복사
Copy-Item pre-commit_template.txt -Destination .git\hooks\pre-commit -Force

# Git Bash에서 실행 권한 부여 (선택사항)
chmod +x .git/hooks/pre-commit
```

## ⚠️ 중요 사항

### 절대 변경하면 안 되는 것들:

1. **Breadcrumb padding**: `padding: 7px 0px 0px;`
2. **온보딩 단계 수**: 7단계 고정
3. **프로그레스 바 계산식**: (단계 / 7) × 100%
4. **Header/Breadcrumb 높이 및 위치**
5. **other_recommendations.html의 padding**: `0 60px 0 20px`

### 검증 실패 시

검증에 실패하면:
1. `FRONTEND_STYLE_GUIDE.md`를 확인하세요
2. 실패한 항목을 수정하세요
3. 다시 검증을 실행하세요

## 🔧 검증 규칙 추가

새로운 스타일 규칙을 추가하려면:
1. `FRONTEND_STYLE_GUIDE.md`에 규칙 추가
2. `validate_frontend_style.py`에 검증 로직 추가
3. 테스트 실행

## 📞 문의

프론트엔드 스타일 관련 문제가 있으면:
- `FRONTEND_STYLE_GUIDE.md` 참고
- `validate_frontend_style.py` 실행하여 문제 확인

---

**마지막 업데이트**: 2025-01-27
