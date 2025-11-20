@echo off
echo ========================================
echo   Initial Setup - First Time Only
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
echo OK
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
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
echo [3/6] Activating venv and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo OK
echo.

REM Install dependencies
echo [4/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo OK
echo.

REM Pull Ollama model
echo [5/6] Pulling Ollama model (this may take a while)...
ollama pull qwen2.5:7b-instruct-q4_K_M
if errorlevel 1 (
    echo WARNING: Ollama pull failed. Make sure Ollama is installed and running.
    echo Download from: https://ollama.com
)
echo OK
echo.

REM Create sample data
echo [6/6] Creating sample data for testing...
python scripts/create_sample_data.py
if errorlevel 1 (
    echo WARNING: Failed to create sample data, continuing...
)
echo OK
echo.

echo ========================================
echo   Setup completed!
echo   You can now run: start.bat
echo ========================================
pause

