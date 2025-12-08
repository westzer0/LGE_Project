@echo off
cd /d "c:\Users\134\Desktop\DX Project"
echo Fetching from origin...
git fetch origin
echo.
echo Pulling from origin/main...
git pull origin main
echo.
echo Checking for commit c5fda2a...
git log --all --oneline | findstr "c5fda2a"
if errorlevel 1 (
    echo Commit c5fda2a NOT found
) else (
    echo Commit c5fda2a found!
)
echo.
echo Recent local commits:
git log --oneline -5
echo.
echo Recent remote commits:
git log origin/main --oneline -5
echo.
echo Commits in remote but not in local:
git log HEAD..origin/main --oneline
pause
