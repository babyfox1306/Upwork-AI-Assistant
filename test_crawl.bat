@echo off
echo ========================================
echo   Test Crawler (Simulate GitHub Actions)
echo ========================================
echo.

REM Activate virtual environment
echo Kích hoạt môi trường ảo...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Không tìm thấy môi trường ảo!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Test 1: Crawl với CI mode (skip tech blogs)
echo ========================================
echo.

REM Set CI environment variable để simulate GitHub Actions
set CI=true
set GITHUB_ACTIONS=true

echo Đang chạy crawler với CI mode...
echo (Sẽ skip tech blogs, chỉ crawl job boards)
echo.

python scripts/crawl_multi_source.py

if errorlevel 1 (
    echo.
    echo ❌ TEST FAILED: Crawler có lỗi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Test 2: Kiểm tra output
echo ========================================
echo.

if exist data\raw_jobs.jsonl (
    echo ✓ File raw_jobs.jsonl tồn tại
    for %%A in (data\raw_jobs.jsonl) do echo   Size: %%~zA bytes
) else (
    echo ❌ File raw_jobs.jsonl không tồn tại!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ TEST PASSED!
echo ========================================
echo.
echo Crawler hoạt động tốt, có thể push lên GitHub.
echo.
pause

