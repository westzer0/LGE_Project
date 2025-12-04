# Oracle DB 빠른 확인 가이드

## 🚀 엔터만 치면 확인하기

### 방법 1: 배치 파일 (가장 간단) ⭐

**PowerShell 또는 CMD에서:**
```powershell
.\oracle_quick.bat
```

또는 더블클릭으로 실행해도 됩니다!

---

### 방법 2: PowerShell 스크립트

**PowerShell에서:**
```powershell
.\oracle_test.ps1
```

---

### 방법 3: Python 직접 실행

**PowerShell에서:**
```powershell
python oracle_quick.py
```

---

## 📋 사용 가능한 스크립트

### 1. `oracle_quick.bat` / `oracle_quick.py`
- **용도**: 빠른 연결 확인 + 테이블 목록
- **실행**: `.\oracle_quick.bat` 또는 더블클릭
- **결과**: 콘솔에 연결 상태와 테이블 목록 출력

### 2. `oracle_test.ps1` / `oracle_test.bat`
- **용도**: 상세한 연결 테스트
- **실행**: `.\oracle_test.ps1` 또는 `.\oracle_test.bat`
- **결과**: 연결 정보 + 각 테이블의 행 개수

### 3. `oracle_analyze.ps1`
- **용도**: 전체 DB 분석
- **실행**: `.\oracle_analyze.ps1`
- **결과**: `ORACLE_DB_ANALYSIS_RESULT.md` 파일 생성

---

## 💡 추천 사용법

### 일상적인 확인
```powershell
.\oracle_quick.bat
```

### 상세 분석이 필요할 때
```powershell
.\oracle_analyze.ps1
```

---

## ⚡ 더 빠르게: PowerShell Alias 설정

PowerShell 프로필에 다음을 추가하면 `oracle` 명령어로 바로 실행할 수 있습니다:

```powershell
# PowerShell 프로필 열기
notepad $PROFILE

# 다음 내용 추가
function oracle { python oracle_quick.py }
Set-Alias -Name o -Value oracle
```

그러면:
```powershell
oracle    # 또는
o         # 이렇게만 쳐도 실행됩니다!
```

---

## 📝 예상 출력

```
============================================================
Oracle DB 연결 확인
============================================================

✅ 연결 성공!
   사용자: CAMPUS_24K_LG3_DX7_P3_4
   서버 시간: 2024-12-02 15:30:45

✅ 테이블 5개 발견:

  • PRODUCTS                                   1,234개 행
  • PRODUCT_SPECS                                567개 행
  • PRODUCT_REVIEWS                            8,901개 행
  • ONBOARDING_SESSIONS                          123개 행
  • PORTFOLIOS                                    45개 행

============================================================
```

---

## ❓ 문제 해결

### "실행 정책 오류"가 나올 때

PowerShell에서:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 파일을 찾을 수 없다고 나올 때

프로젝트 루트 디렉토리에서 실행하세요:
```powershell
cd "C:\Users\134\Desktop\DX Project"
.\oracle_quick.bat
```

---

## 🎯 가장 빠른 방법

**더블클릭만 하면 됩니다!**
- `oracle_quick.bat` 파일을 더블클릭
- 자동으로 연결 확인하고 결과를 보여줍니다



