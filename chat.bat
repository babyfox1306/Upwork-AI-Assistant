@echo off
echo ========================================
echo   Chat với AI Assistant
echo ========================================
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
echo   Đang mở giao diện web...
echo   Trình duyệt sẽ tự động mở tại:
echo   http://localhost:8501
echo.
echo   Nhấn Ctrl+C để dừng
echo ========================================
echo.

streamlit run app.py

pause

