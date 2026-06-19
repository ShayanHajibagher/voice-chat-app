@echo off
title AI Voice Chat v7 - Installer
cd /d "%~dp0"

echo ========================================
echo  AI Voice Chat - Setup
echo ========================================
echo.

echo Step 1: Creating virtual environment...
echo.
if not exist ".venv" (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo Make sure Python 3.8+ is installed and on your PATH.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

echo.
echo Step 2: Installing Python dependencies...
echo.
call .venv\Scripts\activate.bat
pip install -r src\requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

echo Step 3: Downloading models...
echo.
cd src
python download_model.py
cd ..

echo.
echo ========================================
echo  Setup complete!
echo.
echo  To start, run:   start.bat
echo ========================================
pause
