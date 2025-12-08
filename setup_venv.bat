@echo off
chcp 65001 >nul
echo ========================================
echo  Python 가상환경 설정
echo ========================================
echo.

REM Python 설치 확인
echo [1/4] Python 설치 확인...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo.
    echo Python을 설치하거나 PATH 환경 변수를 설정해주세요.
    echo.
    pause
    exit /b 1
)
python --version
echo [OK] Python 확인 완료
echo.

REM 가상환경 존재 확인
echo [2/4] 가상환경 확인...
if exist "venv\Scripts\python.exe" (
    echo [정보] 가상환경이 이미 존재합니다.
    echo       위치: %CD%\venv
    echo.
) else (
    echo [정보] 가상환경이 없습니다. 생성 중...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [오류] 가상환경 생성에 실패했습니다.
        echo.
        pause
        exit /b 1
    )
    echo [OK] 가상환경 생성 완료
    echo.
)

REM 가상환경 활성화
echo [3/4] 가상환경 활성화...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [경고] 가상환경 활성화에 실패했습니다.
    echo        수동으로 활성화해주세요: venv\Scripts\activate.bat
    echo.
) else (
    echo [OK] 가상환경 활성화 완료
    echo.
)

REM pip 업그레이드
echo [4/4] pip 업그레이드 및 패키지 설치...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet --disable-pip-version-check
if %ERRORLEVEL% NEQ 0 (
    echo [경고] pip 업그레이드 실패 (계속 진행)
    echo.
)

REM requirements.txt 확인 및 설치
if exist "requirements.txt" (
    echo [정보] requirements.txt를 찾았습니다. 패키지 설치 중...
    echo        (이 작업은 몇 분이 걸릴 수 있습니다)
    echo.
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [경고] 일부 패키지 설치에 실패했습니다.
        echo        수동으로 설치해주세요: pip install -r requirements.txt
        echo.
    ) else (
        echo [OK] 모든 패키지 설치 완료
        echo.
    )
) else (
    echo [정보] requirements.txt 파일을 찾을 수 없습니다.
    echo        패키지는 수동으로 설치해주세요.
    echo.
)

echo ========================================
echo  가상환경 설정 완료!
echo ========================================
echo.
echo [사용 방법]
echo   1. 가상환경 활성화:
echo      venv\Scripts\activate.bat
echo.
echo   2. 가상환경 비활성화:
echo      deactivate
echo.
echo   3. 서버 시작:
echo      start_server_fixed.bat
echo      또는
echo      python manage.py runserver 8000
echo.
echo ========================================
pause

