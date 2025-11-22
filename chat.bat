@echo off
chcp 65001 >nul
echo ========================================
echo   Chat voi AI Assistant
echo ========================================
echo.

REM Activate virtual environment
echo Kich hoat moi truong ao...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Khong tim thay moi truong ao!
    echo Chay setup.bat truoc neu chua setup.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Dang mo giao dien web...
echo   Trinh duyet se tu dong mo tai:
echo   http://localhost:8501
echo.
echo   Nhan Ctrl+C de dung
echo ========================================
echo.

streamlit run app.py

pause

