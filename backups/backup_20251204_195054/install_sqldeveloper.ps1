# SQL Developer 설치 스크립트
# 사용법: 다운로드한 sqldeveloper 파일의 경로를 지정하고 실행

param(
    [string]$DownloadedFile = "",
    [string]$InstallPath = "C:\sqldeveloper"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SQL Developer 설치 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 설치 경로 생성
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Write-Host "[✓] 설치 디렉토리 생성: $InstallPath" -ForegroundColor Green
} else {
    Write-Host "[!] 설치 디렉토리 이미 존재: $InstallPath" -ForegroundColor Yellow
}

# 다운로드 파일 찾기
if ([string]::IsNullOrEmpty($DownloadedFile)) {
    Write-Host ""
    Write-Host "다운로드 파일 자동 검색 중..." -ForegroundColor Yellow
    
    $searchPaths = @(
        "$env:USERPROFILE\Downloads",
        "$env:USERPROFILE\Desktop",
        "C:\Users\$env:USERNAME\Downloads",
        "C:\Users\$env:USERNAME\Desktop"
    )
    
    $foundFile = $null
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $file = Get-ChildItem -Path $path -Filter "*sqldeveloper*" -ErrorAction SilentlyContinue | 
                    Where-Object { $_.Extension -in @('.zip', '.exe', '.msi') } | 
                    Sort-Object LastWriteTime -Descending | 
                    Select-Object -First 1
            
            if ($file) {
                $foundFile = $file.FullName
                Write-Host "[✓] 파일 발견: $foundFile" -ForegroundColor Green
                break
            }
        }
    }
    
    if (-not $foundFile) {
        Write-Host ""
        Write-Host "[!] 다운로드 파일을 찾을 수 없습니다." -ForegroundColor Red
        Write-Host ""
        Write-Host "다음 단계를 따라주세요:" -ForegroundColor Yellow
        Write-Host "1. 아래 링크에서 파일 다운로드:" -ForegroundColor White
        Write-Host "   https://naver.me/GypmDxPj" -ForegroundColor Cyan
        Write-Host "   비밀번호: 20250714" -ForegroundColor Cyan
        Write-Host "2. sqldeveloper-23.1.1.34 파일 다운로드" -ForegroundColor White
        Write-Host "3. 이 스크립트를 다시 실행하거나, 다운로드한 파일 경로를 지정:" -ForegroundColor White
        Write-Host "   .\install_sqldeveloper.ps1 -DownloadedFile 'C:\path\to\sqldeveloper.zip'" -ForegroundColor Cyan
        Write-Host ""
        exit
    }
    
    $DownloadedFile = $foundFile
}

# 파일 확인
if (-not (Test-Path $DownloadedFile)) {
    Write-Host "[✗] 파일을 찾을 수 없습니다: $DownloadedFile" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "다운로드 파일: $DownloadedFile" -ForegroundColor White
Write-Host "설치 경로: $InstallPath" -ForegroundColor White
Write-Host ""

# 파일 확장자에 따라 처리
$fileExtension = [System.IO.Path]::GetExtension($DownloadedFile).ToLower()

if ($fileExtension -eq '.zip') {
    Write-Host "[*] ZIP 파일 압축 해제 중..." -ForegroundColor Yellow
    
    # 기존 설치 제거 (선택사항)
    if (Test-Path $InstallPath) {
        $existingFiles = Get-ChildItem -Path $InstallPath -ErrorAction SilentlyContinue
        if ($existingFiles.Count -gt 0) {
            Write-Host "[!] 기존 파일이 있습니다. 덮어쓰시겠습니까? (Y/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -ne 'Y' -and $response -ne 'y') {
                Write-Host "[*] 설치 취소됨" -ForegroundColor Yellow
                exit
            }
            Remove-Item -Path "$InstallPath\*" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    # 압축 해제
    Expand-Archive -Path $DownloadedFile -DestinationPath $InstallPath -Force
    Write-Host "[✓] 압축 해제 완료" -ForegroundColor Green
    
    # 압축 해제 후 구조 확인 및 sqldeveloper.exe 찾기
    $sqldeveloperExe = Get-ChildItem -Path $InstallPath -Recurse -Filter "sqldeveloper.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($sqldeveloperExe) {
        Write-Host "[✓] sqldeveloper.exe 발견: $($sqldeveloperExe.FullName)" -ForegroundColor Green
        
        # 바탕화면에 바로가기 생성
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "SQL Developer.lnk"
        
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $sqldeveloperExe.FullName
        $Shortcut.WorkingDirectory = $sqldeveloperExe.DirectoryName
        $Shortcut.Description = "Oracle SQL Developer"
        $Shortcut.Save()
        
        Write-Host "[✓] 바탕화면 바로가기 생성 완료" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "설치 완료!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "SQL Developer 실행 파일: $($sqldeveloperExe.FullName)" -ForegroundColor White
        Write-Host "바탕화면 바로가기: $shortcutPath" -ForegroundColor White
        Write-Host ""
        Write-Host "SQL Developer를 실행하시겠습니까? (Y/N)" -ForegroundColor Yellow
        $runResponse = Read-Host
        if ($runResponse -eq 'Y' -or $runResponse -eq 'y') {
            Start-Process -FilePath $sqldeveloperExe.FullName
            Write-Host "[✓] SQL Developer 실행 중..." -ForegroundColor Green
        }
    } else {
        Write-Host "[!] sqldeveloper.exe를 찾을 수 없습니다. 수동으로 확인해주세요." -ForegroundColor Yellow
        Write-Host "설치 경로: $InstallPath" -ForegroundColor White
    }
    
} elseif ($fileExtension -eq '.exe' -or $fileExtension -eq '.msi') {
    Write-Host "[*] 설치 파일 실행 중..." -ForegroundColor Yellow
    Start-Process -FilePath $DownloadedFile -Wait
    Write-Host "[✓] 설치 완료" -ForegroundColor Green
} else {
    Write-Host "[✗] 지원하지 않는 파일 형식입니다: $fileExtension" -ForegroundColor Red
    Write-Host "ZIP, EXE, MSI 파일만 지원합니다." -ForegroundColor Yellow
}

