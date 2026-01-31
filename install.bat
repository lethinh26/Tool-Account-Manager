@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo Installing Account Manager Tool (uv + venv)...
echo.

REM 1) Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM 2) Check uv (install if missing)
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo uv not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install uv!
        pause
        exit /b 1
    )
)

echo uv found!
echo.

REM 3) Create venv (.venv) if not exists
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    uv venv
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to create venv!
        pause
        exit /b 1
    )
)

REM 4) Install requirements into that venv (NOT system)
echo Installing required packages into .venv...
uv pip install -r requirements.txt --python ".venv\Scripts\python.exe"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install packages!
    pause
    exit /b 1
)

echo.
echo =====================================
echo Installation completed successfully!
echo =====================================
echo.
echo To run the tool:
echo   .venv\Scripts\python.exe main.py
echo or (recommended)
echo   uv run main.py
echo.
pause
