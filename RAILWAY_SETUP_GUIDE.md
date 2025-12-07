# 🚂 Railway GitHub 저장소 연결 가이드

Railway에서 "No repositories found" 오류가 발생할 때 해결 방법입니다.

## 🔍 문제 상황

Railway에서 GitHub 저장소를 선택할 때 저장소가 보이지 않는 경우:
- "No repositories found - try a different search"
- "Configure GitHub App" 메시지가 보임

## ✅ 해결 방법

### 방법 1: GitHub App 권한 재설정 (가장 일반적)

1. **Railway 대시보드에서**
   - 우측 상단 프로필 아이콘 클릭
   - "Settings" 선택
   - "Connected Accounts" 또는 "GitHub" 섹션 찾기

2. **GitHub 연결 해제 후 재연결**
   - "Disconnect" 클릭
   - "Connect GitHub" 다시 클릭
   - GitHub 인증 화면에서 **모든 저장소 접근 권한** 허용

3. **저장소 접근 권한 확인**
   - GitHub에서 저장소가 **Private**인 경우:
     - Railway가 해당 저장소에 접근할 수 있도록 권한 부여 필요
   - GitHub 인증 시 "All repositories" 또는 해당 저장소 선택

### 방법 2: GitHub에서 직접 권한 확인

1. **GitHub 설정 확인**
   - https://github.com/settings/applications 접속
   - "Authorized OAuth Apps" 또는 "Installed GitHub Apps" 클릭
   - "Railway" 앱 찾기

2. **권한 수정**
   - "Railway" 클릭
   - "Repository access" 확인
   - "All repositories" 또는 "Only select repositories"에서 저장소 선택

### 방법 3: 저장소 검색

1. **저장소 이름으로 검색**
   - Railway 저장소 선택 화면에서
   - 검색창에 `LGE_Project` 입력
   - 또는 `westzer0/LGE_Project` 전체 경로 입력

2. **조직/개인 계정 확인**
   - 저장소가 조직(Organization)에 있는 경우
   - 조직 권한이 Railway에 부여되어 있는지 확인

### 방법 4: 저장소를 Public으로 변경 (임시 해결)

1. **GitHub에서 저장소 설정**
   - https://github.com/westzer0/LGE_Project/settings 접속
   - 맨 아래 "Danger Zone" → "Change visibility"
   - "Make public" 선택 (임시로)

2. **배포 후 다시 Private으로 변경 가능**

### 방법 5: Railway CLI 사용 (대안)

GitHub 연결이 안 될 때 CLI로 배포:

```bash
# 1. Railway CLI 설치
npm i -g @railway/cli

# 2. 로그인
railway login

# 3. 프로젝트 초기화
railway init

# 4. 배포
railway up
```

## 🔧 단계별 체크리스트

### 1단계: GitHub 계정 확인
- [ ] Railway에 로그인한 GitHub 계정이 `westzer0`인지 확인
- [ ] 다른 계정으로 로그인했다면 올바른 계정으로 재로그인

### 2단계: 저장소 접근 권한 확인
- [ ] 저장소가 Private인 경우 Railway에 권한 부여
- [ ] GitHub Settings → Applications → Railway → Repository access 확인

### 3단계: Railway에서 재연결
- [ ] Railway Settings → Connected Accounts → GitHub Disconnect
- [ ] 다시 Connect → 모든 저장소 권한 허용

### 4단계: 저장소 검색
- [ ] 검색창에 `LGE_Project` 또는 `westzer0` 입력
- [ ] 필터에서 "Private repositories" 포함 확인

## 🎯 빠른 해결 (가장 확실한 방법)

1. **Railway 대시보드**
   - 우측 상단 프로필 → Settings
   - "Connected Accounts" → GitHub "Disconnect"

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - GitHub 재인증 (이때 **모든 저장소 권한** 체크)

3. **저장소 선택**
   - `westzer0/LGE_Project` 검색 또는 선택

## ⚠️ 주의사항

- **Private 저장소**: Railway가 접근하려면 명시적으로 권한 부여 필요
- **조직 저장소**: 조직 관리자가 Railway 앱을 승인해야 할 수 있음
- **2FA 활성화**: GitHub 2단계 인증이 켜져 있으면 추가 인증 필요

## 🔗 참고 링크

- Railway 문서: https://docs.railway.app/guides/github
- GitHub App 권한: https://github.com/settings/applications

