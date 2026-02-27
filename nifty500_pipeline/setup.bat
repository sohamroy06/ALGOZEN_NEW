@echo off
REM NIFTY 500 Pipeline - Windows Setup Script
REM ==========================================
REM This script sets up the Python environment and installs dependencies.

echo ========================================================================
echo NIFTY 500 DATA PIPELINE - SETUP
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/5] Python found: 
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo Pip upgraded successfully.
echo.

REM Install dependencies
echo [5/5] Installing dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

echo ========================================================================
echo SETUP COMPLETED SUCCESSFULLY!
echo ========================================================================
echo.
echo Next steps:
echo   1. The virtual environment is now active (you should see "(venv)" in your prompt)
echo   2. Run the pipeline: python main.py
echo   3. To deactivate virtual environment later: deactivate
echo.
echo For more information, see README.md
echo ========================================================================
echo.
