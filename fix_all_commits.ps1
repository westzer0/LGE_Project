# 깨진 커밋 메시지 일괄 수정 스크립트

$ErrorActionPreference = "Stop"

# 커밋 메시지 파일들
$commit7590408 = @"
feat: Add taste-based scoring logic and recommendation phrase generation

- Add taste-based scoring logic system
- Add recommendation phrase generation based on taste combinations
- Add analysis commands for taste recommendations
- Add scoring logic explanation and JSON data
- Update recommendation engine with taste scoring
"@

$commit57880e5 = @"
feat: Add main page integration, AI chatbot, API key configuration

- Add main page template (main.html)
- Add AI chatbot functionality (ai-chatbot.js)
- Add API key configuration using python-dotenv (.env file)
- Improve Kakao SDK integration (error handling, loading logic)
- Improve recommendation logic (result formatting, error handling)
- Add documentation (DRF guide, server start guide, view products guide)
- Add environment setup files (env.example)
"@

$commitCa8c15b = @"
merge: Main page integration and banner image application (previous commit recovery)

- Add banner images (banner2.png)
- Update main.html template
- Add backup files from previous commit
"@

$commitA122c68 = @"
merge: Main page integration and image assets addition

- Add import excel command
- Add product specs migration
- Add banner and icon images
- Add backup files from previous commits
- Update views and URLs
"@

# UTF-8 인코딩 (BOM 없음)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# 각 커밋 메시지를 파일로 저장
[System.IO.File]::WriteAllText("$PWD\commit_7590408.txt", $commit7590408, $utf8NoBom)
[System.IO.File]::WriteAllText("$PWD\commit_57880e5.txt", $commit57880e5, $utf8NoBom)
[System.IO.File]::WriteAllText("$PWD\commit_ca8c15b.txt", $commitCa8c15b, $utf8NoBom)
[System.IO.File]::WriteAllText("$PWD\commit_a122c68.txt", $commitA122c68, $utf8NoBom)

Write-Host "커밋 메시지 파일 생성 완료"
Write-Host "다음 명령어를 순서대로 실행하세요:"
Write-Host ""
Write-Host "1. git rebase -i 57880e5^"
Write-Host "   (7590408 커밋의 'pick'을 'reword'로 변경하고 저장)"
Write-Host "   (나오는 편집기에서 commit_7590408.txt 내용으로 교체)"
Write-Host ""
Write-Host "2. git rebase -i 339d212^"
Write-Host "   (57880e5 커밋의 'pick'을 'reword'로 변경하고 저장)"
Write-Host "   (나오는 편집기에서 commit_57880e5.txt 내용으로 교체)"
Write-Host ""
Write-Host "3. merge 커밋들은 별도 처리 필요"

