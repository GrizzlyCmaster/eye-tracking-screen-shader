@echo off
REM Basic Eye Tracker Launcher (simpler, no calibration)

cd /d "%~dp0"

set PYTHON_EXE=..\..\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python virtual environment not found!
    exit /b 1
)

echo Starting basic eye tracker...
"%PYTHON_EXE%" eye_tracker.py

if %ERRORLEVEL% NEQ 0 (
    pause
)
