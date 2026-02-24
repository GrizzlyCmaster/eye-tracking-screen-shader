@echo off
REM Build eye_tracker.py into standalone executable using PyInstaller

echo.
echo ========================================
echo Building eye_tracker.exe
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Building executable...
echo This may take a few minutes...
echo.

pyinstaller --onefile --windowed --icon=appicon.ico eye_tracker.py >nul 2>&1

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    echo.
    echo Trying without icon...
    pyinstaller --onefile --windowed eye_tracker.py
    if errorlevel 1 (
        echo Build failed. Check console output above.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable created: dist\eye_tracker.exe
echo.
echo You can now:
echo 1. Run eye_tracker.exe directly (no Python needed)
echo 2. Move it to any folder you want
echo 3. Share it with others (includes Python runtime)
echo.
pause
