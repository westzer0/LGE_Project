# SQL Developer 설치 위치 안내

## 📍 현재 SQL Developer 위치

```
C:\Users\134\Downloads\sqldeveloper-23.1.1.345.2114-x64\sqldeveloper
```

## ✅ 권장 사항: 그대로 두기

**SQL Developer는 독립 실행형 애플리케이션이므로 프로젝트 폴더에 넣을 필요가 없습니다.**

### 장점:
- ✅ 프로젝트 폴더가 깔끔하게 유지됨
- ✅ 여러 프로젝트에서 동일한 SQL Developer 사용 가능
- ✅ 프로젝트를 이동/삭제해도 SQL Developer는 영향 없음
- ✅ Git 등 버전 관리에서 제외할 필요 없음

### 실행 방법:
1. `C:\Users\134\Downloads\sqldeveloper-23.1.1.345.2114-x64\sqldeveloper\sqldeveloper.exe` 실행
2. 또는 바탕화면/시작 메뉴에 바로가기 생성

---

## 🔄 옵션: 프로젝트 폴더로 옮기기

만약 프로젝트와 함께 관리하고 싶다면:

### 이동 경로:
```
C:\Users\134\Desktop\DX Project\tools\sqldeveloper\
```

### 장점:
- ✅ 프로젝트와 함께 관리
- ✅ 프로젝트별 독립적인 SQL Developer 설정 가능

### 단점:
- ❌ 프로젝트 폴더 크기 증가 (약 수백 MB)
- ❌ Git 등 버전 관리에서 제외해야 함 (`.gitignore`에 추가 필요)
- ❌ 프로젝트를 이동/삭제하면 SQL Developer도 함께 이동/삭제됨

---

## 🚀 빠른 실행을 위한 바로가기 생성

프로젝트 폴더에 바로가기만 만들어도 편리하게 사용할 수 있습니다:

### 방법 1: PowerShell로 바로가기 생성
```powershell
# 프로젝트 폴더에 바로가기 생성
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$PWD\SQL Developer.lnk")
$Shortcut.TargetPath = "C:\Users\134\Downloads\sqldeveloper-23.1.1.345.2114-x64\sqldeveloper\sqldeveloper.exe"
$Shortcut.WorkingDirectory = "C:\Users\134\Downloads\sqldeveloper-23.1.1.345.2114-x64\sqldeveloper"
$Shortcut.Save()
```

### 방법 2: 수동으로 바로가기 생성
1. `sqldeveloper.exe` 우클릭 → **바로가기 만들기**
2. 바로가기를 프로젝트 폴더로 이동
3. 이름을 `SQL Developer`로 변경

---

## 📝 결론

**권장**: SQL Developer는 현재 위치(`Downloads`)에 그대로 두고, 프로젝트 폴더에 바로가기만 생성하는 것을 추천합니다.

이렇게 하면:
- 프로젝트 폴더는 깔끔하게 유지
- SQL Developer는 편리하게 접근 가능
- 여러 프로젝트에서 공유 사용 가능

