@echo off
echo ========================================
echo   Cập Nhật Dữ Liệu
echo ========================================
echo.

REM Activate virtual environment
echo [1/4] Kích hoạt môi trường ảo...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Không tìm thấy môi trường ảo!
    echo Chạy setup.bat trước nếu chưa setup.
    pause
    exit /b 1
)
echo OK
echo.

REM Pull from GitHub
echo [2/4] Cập nhật từ GitHub (GitHub Actions đã crawl tự động)...
git pull origin main
if errorlevel 1 (
    echo WARNING: Git pull thất bại, tiếp tục...
)
echo OK
echo.

REM Sync ChromaDB (embedding jobs mới)
echo [3/4] Sync ChromaDB (embedding jobs mới)...
python scripts/local_sync_and_rag.py
if errorlevel 1 (
    echo WARNING: Sync ChromaDB có lỗi, tiếp tục...
)
echo OK
echo.

REM AI Analysis & Summary
echo [4/4] AI phân tích và tóm tắt...
python scripts/analyze_and_summarize.py
if errorlevel 1 (
    echo WARNING: AI Analysis có lỗi, tiếp tục...
)
echo OK
echo.

echo ========================================
echo   Hoàn thành! Dữ liệu đã được cập nhật.
echo   Jobs mới đã được phân tích bởi AI.
echo ========================================
pause

