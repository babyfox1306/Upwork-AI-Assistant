@echo off
echo ========================================
echo   Fix ChromaDB Version Issue
echo ========================================
echo.
echo Step 1: Activate venv...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Khong tim thay venv!
    pause
    exit /b 1
)
echo OK
echo.
echo Step 2: Upgrade ChromaDB...
pip install --upgrade "chromadb>=1.3.5"
echo.
echo Step 3: (Optional) Xoa database cu neu co conflict...
echo Neu van loi, xoa thu muc: data\chroma_db
echo.
echo Done!
pause

