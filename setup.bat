@echo off
chcp 65001 >nul
echo ========================================
echo   Initial Setup - First Time Only
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
echo OK
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo OK - Virtual environment created
)
echo.

REM Activate and upgrade pip
echo [3/5] Activating venv and upgrading pip...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
echo OK
echo.

REM Install dependencies
echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo OK
echo.

REM Pull Ollama model
echo [5/5] Pulling Ollama model (this may take a while)...
ollama pull qwen2.5:7b-instruct-q4_K_M
if errorlevel 1 (
    echo WARNING: Ollama pull failed. Make sure Ollama is installed and running.
    echo Download from: https://ollama.com
)
echo OK
echo.

echo ========================================
echo   Setup completed!
echo   You can now run: update.bat
echo ========================================
pause

