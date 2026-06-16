@echo off
title AI Voice Chat
cd /d "%~dp0"

if not exist ".venv" (
    echo [ERROR] Virtual environment not found.
    echo Run install.bat first to set up dependencies.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
cd src
python cli.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
