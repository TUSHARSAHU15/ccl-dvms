@echo off
echo ============================================================
echo  Automated GitHub Push for CCL DVMS Deployment
echo ============================================================
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/username/ccl-dvms.git): "
if "%REPO_URL%"=="" (
    echo No repository URL entered. Exiting...
    pause
    exit /b
)

echo.
echo Adding remote origin...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo Pushing main branch to GitHub...
git branch -M main
git push -u origin main

echo.
echo ============================================================
echo  SUCCESS! Code pushed to GitHub.
echo  Now go to Render.com and select your repository to go 24/7 Live!
echo ============================================================
pause
