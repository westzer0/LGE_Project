@echo off
echo ========================================
echo Oracle Instant Client 경로 확인
echo ========================================
echo.

set "CHECK_PATH=C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0"

echo 확인할 경로: %CHECK_PATH%
echo.

if exist "%CHECK_PATH%" (
    echo [OK] 경로가 존재합니다.
    echo.
    echo 폴더 내용:
    dir /b "%CHECK_PATH%" | findstr /i "oci.dll instantclient"
    echo.
    
    if exist "%CHECK_PATH%\oci.dll" (
        echo [OK] oci.dll 파일을 찾았습니다!
        echo.
        echo 올바른 경로: %CHECK_PATH%
        echo.
        echo .env 파일에 다음을 추가하세요:
        echo ORACLE_INSTANT_CLIENT_PATH=%CHECK_PATH%
    ) else (
        echo [WARNING] oci.dll 파일을 찾을 수 없습니다.
        echo.
        echo 하위 폴더 확인 중...
        echo.
        for /d %%d in ("%CHECK_PATH%\*") do (
            if exist "%%d\oci.dll" (
                echo [OK] 하위 폴더에서 발견: %%d
                echo.
                echo 올바른 경로: %%d
                echo.
                echo .env 파일에 다음을 추가하세요:
                echo ORACLE_INSTANT_CLIENT_PATH=%%d
                goto :found
            )
        )
        echo [ERROR] oci.dll 파일을 찾을 수 없습니다.
        echo Instant Client가 제대로 설치되지 않았을 수 있습니다.
    )
) else (
    echo [ERROR] 경로가 존재하지 않습니다.
    echo.
    echo 확인 사항:
    echo   1. 경로가 올바른지 확인
    echo   2. Instant Client가 설치되어 있는지 확인
)

:found
echo.
echo ========================================
pause

