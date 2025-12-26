@echo off
REM Keep window open even if there's an error
title LLM Chatbot Server

echo ============================================================
echo Starting LLM Financial Chatbot Server
echo ============================================================
echo.
echo Current directory: %CD%
echo.

REM Change to script directory
cd /d "%~dp0"
echo Changed to: %CD%
echo.

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Found virtual environment
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo.
echo Starting server on http://127.0.0.1:8000
echo Keep this window open!
echo Press Ctrl+C to stop
echo.
echo ============================================================
echo.

python -m uvicorn src.server:app --reload --port 8000

echo.
echo Server stopped.
pause
