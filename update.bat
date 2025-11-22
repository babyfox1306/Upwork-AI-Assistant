@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ========================================
echo   Cap Nhat Du Lieu - Update ^& Sync
echo ========================================
echo.
echo Chon che do:
echo   1. Day du (Git Pull + Sync + AI Analysis) - Mac dinh
echo   2. Chi Sync ChromaDB (nhanh, khong git pull, khong AI)
echo.
set /p choice="Nhap lua chon (1 hoac 2, Enter = 1): "
set "choice=!choice: =!"
if "!choice!"=="" set choice=1
if "!choice!"=="2" goto sync_only
if "!choice!"=="1" goto full_update
goto full_update

:full_update
echo.
echo ========================================
echo   Che do: Day du
echo ========================================
echo.

REM Activate virtual environment
echo [1/4] Kich hoat moi truong ao...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Khong tim thay moi truong ao!
    echo Chay setup.bat truoc neu chua setup.
    pause
    exit /b 1
)
echo OK
echo.

REM Pull from GitHub
echo [2/4] Cap nhat tu GitHub (GitHub Actions da crawl tu dong)...
git pull origin main
if errorlevel 1 (
    echo WARNING: Git pull that bai, tiep tuc...
)
echo OK
echo.

REM Sync ChromaDB (embedding jobs moi)
echo [3/4] Sync ChromaDB (embedding jobs moi)...
python scripts/local_sync_and_rag.py
if errorlevel 1 (
    echo WARNING: Sync ChromaDB co loi, tiep tuc...
)
echo OK
echo.

REM AI Analysis ^& Summary
echo [4/4] AI phan tich va tom tat...
python scripts/analyze_and_summarize.py
if errorlevel 1 (
    echo WARNING: AI Analysis co loi, tiep tuc...
)
echo OK
echo.

echo ========================================
echo   Hoan thanh! Du lieu da duoc cap nhat.
echo   Jobs moi da duoc phan tich boi AI.
echo ========================================
goto end

:sync_only
echo.
echo ========================================
echo   Che do: Chi Sync ChromaDB
echo ========================================
echo.

REM Activate virtual environment
echo Kich hoat moi truong ao...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Khong tim thay moi truong ao!
    pause
    exit /b 1
)
echo OK
echo.

REM Sync ChromaDB only
echo Dang sync jobs vao ChromaDB...
echo (Co the mat vai phut neu co nhieu jobs moi)
echo.
python scripts/local_sync_and_rag.py
if errorlevel 1 (
    echo WARNING: Sync ChromaDB co loi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Hoan thanh! ChromaDB da duoc sync.
echo ========================================
goto end

:end
pause

