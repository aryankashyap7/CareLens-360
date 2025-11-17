@echo off
REM Setup script for CareLens 360 on Windows

echo ========================================
echo CareLens 360 - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check for .env file
if not exist .env (
    echo Creating .env file from template...
    copy env.example .env
    echo [WARNING] Please update .env with your credentials
) else (
    echo [OK] .env file exists
)
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Update .env file with your credentials
echo 2. Set up Google Cloud credentials (gcloud auth application-default login)
echo 3. Run: streamlit run src\app.py
echo.
pause

