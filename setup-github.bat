@echo off
REM Eye Tracking Screen Shader - GitHub Repository Setup (Batch version)
REM PowerShell version recommended - run: powershell -ExecutionPolicy Bypass -File setup-github.ps1

echo.
echo ===========================================
echo Eye Tracking Screen Shader - GitHub Setup
echo ===========================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git is not installed or not in PATH
    pause
    exit /b 1
)

REM Get git version
git --version

REM Display instructions
echo.
echo GITHUB REPOSITORY SETUP INSTRUCTIONS
echo ====================================
echo.
echo 1. MANUALLY CREATE REPOSITORY:
echo    - Go to https://github.com/new
echo    - Repository name: eye-tracking-screen-shader
echo    - Description: GPU-accelerated eye-tracking shader with foveated rendering for FPS gaming
echo    - Public (recommended)
echo    - Do NOT initialize with README/.gitignore/license
echo.
echo 2. CONFIGURE GIT REMOTE:
echo    git remote set-url origin https://github.com/YOUR_USERNAME/eye-tracking-screen-shader.git
echo.
echo 3. PUSH TO GITHUB:
echo    git branch -M main
echo    git push -u origin main
echo.
echo 4. OR USE POWERSHELL VERSION FOR INTERACTIVE SETUP:
echo    powershell -ExecutionPolicy Bypass -File setup-github.ps1
echo.
echo RECOMMENDED: Use the PowerShell script for guided setup
echo.
pause
