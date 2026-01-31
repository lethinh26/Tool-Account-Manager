@echo off
setlocal EnableExtensions

echo Installing Account Manager Tool (uv + venv)...
echo.

REM 1/ Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM 2/ Define uv expected install dir
set "UV_BIN=%USERPROFILE%\.local\bin"
set "UV_EXE=%UV_BIN%\uv.exe"

REM 3/ Check uv
where uv >nul 2>&1
if errorlevel 1 (
    REM If not in PATH, check if already installed in UV_BIN
    if exist "%UV_EXE%" (
        echo uv is installed but not in PATH. Using: "%UV_EXE%"
    ) else (
        echo uv not found. Installing uv...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        REM Do NOT trust exit code alone; verify file exists
        if not exist "%UV_EXE%" (
            echo.
            echo ERROR: uv install script ran but "%UV_EXE%" not found.
            echo Please check internet / antivirus / permissions.
            pause
            exit /b 1
        )
    )
)

REM 4/ Ensure current session can find uv
set "PATH=%UV_BIN%;%PATH%"

REM 5/ Pick uv command (prefer PATH, fallback to full path)
where uv >nul 2>&1
if errorlevel 1 (
    set "UV_CMD=%UV_EXE%"
) else (
    set "UV_CMD=uv"
)

echo Using uv: %UV_CMD%
echo.

REM 6/ Create venv if missing
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %UV_CMD% venv
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create venv!
        pause
        exit /b 1
    )
)

REM 7/ Install requirements into venv
echo Installing required packages into .venv...
%UV_CMD% pip install -r requirements.txt --python ".venv\Scripts\python.exe"
if errorlevel 1 (
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
echo   run.bat
echo.
pause
