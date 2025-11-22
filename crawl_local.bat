@echo off
echo ========================================
echo   Crawl Local (Nếu muốn crawl thủ công)
echo ========================================
echo.
echo Lưu ý: GitHub Actions đã tự động crawl mỗi 15 phút
echo Chỉ chạy script này nếu muốn crawl ngay lập tức
echo.

REM Activate virtual environment
echo Kích hoạt môi trường ảo...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Không tìm thấy môi trường ảo!
    echo Chạy setup.bat trước nếu chưa setup.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Đang crawl jobs từ RSS feeds...
echo ========================================
echo.

python scripts/crawl_multi_source.py

echo.
echo ========================================
echo   Hoàn thành!
echo ========================================
pause

