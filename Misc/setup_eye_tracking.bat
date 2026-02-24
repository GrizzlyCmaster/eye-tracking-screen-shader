@echo off
REM Eye Tracking Setup Script for ShaderGlass
REM This script helps install required Python dependencies

echo.
echo ========================================
echo Eye Tracking Setup for ShaderGlass
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check and install required packages
echo Installing required Python packages...
echo.

echo Installing opencv-python...
pip install opencv-python
if errorlevel 1 (
    echo WARNING: opencv-python installation had issues
)

echo.
echo Installing gaze-tracking...
pip install gaze-tracking
if errorlevel 1 (
    echo WARNING: gaze-tracking installation had issues
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run eye_tracker.py to start eye detection
echo    Command: python eye_tracker.py
echo.
echo 2. In ShaderGlass, import the zoom-fisheye preset:
echo    Import custom... ^> navigate to:
echo    ShaderGlass\Scripts\slang-shaders\custom\zoom-fisheye\zoom-fisheye.slangp
echo.
echo 3. (Optional) Run EyeTrackingBridge.exe to automate parameter updates
echo.
echo For detailed instructions, see: EYE_TRACKING_README.md
echo.
pause
