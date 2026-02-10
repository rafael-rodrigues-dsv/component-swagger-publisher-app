@echo off
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

    REM Create virtual environment
    python -m venv .venv

    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        echo [ERROR] Make sure Python is installed and in PATH
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

