@echo off
echo Starting Account Manager Tool...
echo.

uv run main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start the application!
    echo Please make sure you have run install.bat first.
    pause
)
