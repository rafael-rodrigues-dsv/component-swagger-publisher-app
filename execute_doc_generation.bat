@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  OpenAPI Documentation Publisher - Auto Execution Script
REM  Windows Batch Script
REM ============================================================

echo.
echo ============================================================
echo   OpenAPI Documentation Publisher
echo   Auto-setup and Execution
echo ============================================================
echo.

REM Check if .venv exists
if exist ".venv\" (
    echo [INFO] Virtual environment found at .venv
    echo.
) else (
echo [INFO] Virtual environment not found. Creating...
    echo.

    REM Define Python path - try known working path first
    set "PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe"

    REM Check if Python exists at expected location
    if not exist "!PYTHON_CMD!" (
        REM Try other common locations
        if exist "C:\Python314\python.exe" (
            set "PYTHON_CMD=C:\Python314\python.exe"
        ) else if exist "C:\Program Files\Python314\python.exe" (
            set "PYTHON_CMD=C:\Program Files\Python314\python.exe"
        ) else (
            REM Try using python from PATH as last resort
            set "PYTHON_CMD=python"
        )
    )

    echo [INFO] Using Python: !PYTHON_CMD!
    echo.

    REM Create virtual environment
    "!PYTHON_CMD!" -m venv .venv

    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        echo [ERROR] Python command used: !PYTHON_CMD!
        echo [ERROR] Make sure Python 3.14+ is installed
        pause
        exit /b 1
    )

    echo [OK] Virtual environment created successfully!
    echo.
)

REM Activate virtual environment first
call .venv\Scripts\activate.bat

REM Always check and install dependencies
echo [INFO] Checking and installing dependencies from requirements.txt...
echo.
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo [OK] Dependencies are up to date!
echo.


echo [OK] Virtual environment activated
echo.

REM Execute main.py
echo ============================================================
echo   Starting OpenAPI Documentation Publisher
echo ============================================================
echo.

python main.py

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ============================================================
if %EXIT_CODE% EQU 0 (
    echo [OK] Execution completed successfully!
) else (
    echo [ERROR] Execution failed with exit code: %EXIT_CODE%
)
echo ============================================================
echo.

REM Keep window open if error
if %EXIT_CODE% NEQ 0 (
    pause
)

exit /b %EXIT_CODE%

