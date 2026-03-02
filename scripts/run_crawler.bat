@echo off
REM Job Board Crawler - Windows batch execution script (moved to scripts) 
REM Usage: scripts\run_crawler.bat [mode] [options]

setlocal enabledelayedexpansion
cd /d "%~dp0"
REM go to repo root and remember it
cd ..
set REPO_ROOT=%cd%
cd "%~dp0"

set VENV_PATH=%REPO_ROOT%\.venv
set OUTPUT_DIR=%REPO_ROOT%\output
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set MODE=%1
if "%MODE%"=="" set MODE=quick

if "%1"=="--help" (
    call :print_usage
    exit /b 0
)

REM Check virtual environment
if not exist "%VENV_PATH%" (
    echo [ERROR] Virtual environment not found at %VENV_PATH%
    echo Please run: python -m venv %VENV_PATH%
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found
    exit /b 1
)

REM Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo =====================================================
echo  Job Board Discovery Crawler v1.0
echo =====================================================
echo.

REM Set defaults based on mode
set LIMIT=10
set DETECT_CAREERS=
set OUTPUT_NAME=job_discovery
set EXTRA_ARGS=%*

if /i "%MODE%"=="quick" (
    set LIMIT=10
    set OUTPUT_NAME=quick_discovery
    goto :run_crawler
)

if /i "%MODE%"=="standard" (
    set LIMIT=50
    set OUTPUT_NAME=standard_discovery
    goto :run_crawler
)

if /i "%MODE%"=="extensive" (
    set LIMIT=100
    set DETECT_CAREERS=--detect-careers
    set OUTPUT_NAME=extensive_discovery
    goto :run_crawler
)

if /i "%MODE%"=="resume" (
    echo [*] Resuming from last checkpoint...
    %PYTHON_EXE% %REPO_ROOT%\run.py --engine brave --filter --resume %EXTRA_ARGS%
    goto :success
)

if /i "%MODE%"=="test" (
    echo [*] Running unit tests...
    %PYTHON_EXE% - << ENDPYTHON
from crawler import DuckDuckGoJobBoardCrawler
print("\n" + "="*60)
print("UNIT TESTS")
print("="*60)
c = DuckDuckGoJobBoardCrawler()
tests = [("https://indeed.com", True), ("https://linkedin.com", True), ("https://acme.com", False)]
for url, expected in tests:
    result = c.is_job_aggregator(url)
    status = "✓" if result == expected else "✗"
    print(f"{status} Aggregator: {url}")
print("="*60)
ENDPYTHON
    goto :success
)

echo [ERROR] Unknown mode: %MODE%
call :print_usage
exit /b 1

:run_crawler
echo [*] Crawling job boards (limit: %LIMIT%)...
%PYTHON_EXE% %REPO_ROOT%\run.py --engine brave --filter --limit %LIMIT% %DETECT_CAREERS% --output %OUTPUT_DIR%\%OUTPUT_NAME% %EXTRA_ARGS%
if errorlevel 1 goto :error

:success
echo.
echo [OK] Crawler completed successfully^^!
echo [*] Results saved to: %OUTPUT_DIR%
echo.
dir /b "%OUTPUT_DIR%\*.xlsx" 2>nul
echo.
exit /b 0

:error
echo.
echo [ERROR] Crawler encountered an error
exit /b 1

:print_usage
echo.
echo Usage: scripts\run_crawler.bat [MODE] [OPTIONS]
echo.
echo MODES:
echo   quick       - Discover 10 job boards (default)
echo   standard    - Discover 50 job boards
echo   extensive   - Discover 100+ job boards with career pages
echo   resume      - Resume from last checkpoint
echo   test        - Run unit tests only
echo.
echo OPTIONS:
echo   --help      - Show this message
echo   --limit N   - Override limit (e.g., --limit 25)
echo.
echo EXAMPLES:
echo   scripts\run_crawler.bat quick
echo   scripts\run_crawler.bat standard
echo   scripts\run_crawler.bat extensive
echo   scripts\run_crawler.bat resume
echo.
goto :eof

