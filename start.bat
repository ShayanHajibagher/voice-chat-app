@echo off
title AI Voice Chat v7
cd /d "%~dp0"

if not exist ".venv" (
    echo [ERROR] Virtual environment not found.
    echo Run install.bat first to set up dependencies.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
cd src
python web_server.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
