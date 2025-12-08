# GitHub에 ERD 업로드하는 방법

## 📋 준비사항

1. `ERD.mmd` 파일이 생성되어 있어야 합니다
2. Git 저장소가 초기화되어 있어야 합니다

---

## 🚀 방법 1: Git 명령어로 업로드 (권장)

### 단계별 가이드

#### 1단계: 파일 확인
```powershell
# ERD.mmd 파일이 있는지 확인
ls ERD.mmd
```

#### 2단계: Git에 파일 추가
```powershell
git add ERD.mmd
```

#### 3단계: 커밋
```powershell
git commit -m "Add ERD diagram"
```

또는 더 자세한 메시지:
```powershell
git commit -m "Add ERD diagram with all table comments and relationships"
```

#### 4단계: GitHub에 푸시
```powershell
git push
```

만약 처음 푸시하는 경우:
```powershell
git push -u origin main
```
또는
```powershell
git push -u origin master
```

---

## 🌐 방법 2: GitHub 웹 인터페이스로 업로드

### 단계별 가이드

1. **GitHub 저장소로 이동**
   - 브라우저에서 GitHub 저장소 페이지 열기

2. **파일 업로드**
   - "Add file" 버튼 클릭
   - "Upload files" 선택

3. **파일 드래그 앤 드롭**
   - `ERD.mmd` 파일을 드래그하여 업로드 영역에 놓기
   - 또는 "choose your files" 클릭하여 파일 선택

4. **커밋**
   - 하단의 "Commit changes" 섹션에서
   - 커밋 메시지 입력: "Add ERD diagram"
   - "Commit changes" 버튼 클릭

---

## ✅ 업로드 후 확인

### GitHub에서 ERD 확인하기

1. **파일 직접 확인**
   - 저장소에서 `ERD.mmd` 파일 클릭
   - GitHub가 자동으로 Mermaid 다이어그램을 렌더링합니다!

2. **README에 포함하기 (선택사항)**
   - `README.md` 파일에 ERD를 포함하려면:
   
   ````markdown
   ## 데이터베이스 ERD
   
   ![ERD](ERD.mmd)
   ````
   
   또는 직접 코드 블록으로:
   
   ````markdown
   ## 데이터베이스 ERD
   
   ```mermaid
   erDiagram
       ...
   ```
   ````

---

## 🔧 문제 해결

### 문제 1: "ERD.mmd 파일이 없습니다"

**해결 방법:**
1. `generate_erd.py` 스크립트를 실행하여 ERD 생성:
   ```powershell
   python generate_erd.py
   ```

2. 또는 `LLM_ERD_PROMPT.md`의 프롬프트를 사용하여 LLM으로 ERD 생성

### 문제 2: "Git 저장소가 초기화되지 않았습니다"

**해결 방법:**
```powershell
# Git 초기화
git init

# 원격 저장소 연결 (이미 있는 경우)
git remote add origin https://github.com/사용자명/저장소명.git

# 또는 기존 원격 저장소 확인
git remote -v
```

### 문제 3: "GitHub에 푸시 권한이 없습니다"

**해결 방법:**
1. GitHub 인증 확인
2. Personal Access Token 사용 (필요한 경우)
3. SSH 키 설정 (권장)

---

## 📝 추가 팁

### ERD 파일을 자동으로 업데이트하기

`generate_erd.py` 스크립트를 실행한 후 자동으로 커밋하고 푸시하려면:

```powershell
# 스크립트 실행
python generate_erd.py

# 자동 커밋 및 푸시
git add ERD.mmd
git commit -m "Update ERD diagram"
git push
```

또는 배치 파일로 만들기 (`update_erd.bat`):
```batch
@echo off
python generate_erd.py
git add ERD.mmd
git commit -m "Update ERD diagram"
git push
```

### ERD를 README에 포함하기

`README.md` 파일에 다음을 추가:

````markdown
## 📊 데이터베이스 구조

데이터베이스 ERD는 [ERD.mmd](ERD.mmd) 파일을 참조하세요.

또는 직접 표시:

```mermaid
erDiagram
    ...
```
````

---

## 🎉 완료!

ERD 파일이 GitHub에 업로드되면:
- ✅ GitHub가 자동으로 Mermaid 다이어그램을 렌더링합니다
- ✅ 파일을 클릭하면 시각적인 ERD를 볼 수 있습니다
- ✅ 다른 개발자들과 공유할 수 있습니다

---

## 참고 링크

- [Mermaid ERD 문법](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)
- [GitHub Mermaid 지원](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)
- [Git 기본 명령어](https://git-scm.com/docs)
