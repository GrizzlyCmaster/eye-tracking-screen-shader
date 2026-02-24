@echo off
REM Eye Tracker Launcher
REM Runs the eye tracking application using the Python virtual environment

cd /d "%~dp0"

REM Path to the venv Python executable
set PYTHON_EXE=..\..\.venv\Scripts\python.exe

REM Check if venv exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python virtual environment not found!
    echo Expected location: ..\..\.venv\Scripts\python.exe
    exit /b 1
)

REM Run the ENHANCED eye tracker with calibration
"%PYTHON_EXE%" eye_tracker_enhanced.py

REM Only pause if there was an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred. Press any key to close...
    pause
)
