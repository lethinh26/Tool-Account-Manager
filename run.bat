@echo off

if not exist ".venv\Scripts\pythonw.exe" (
    echo ERROR: Environment not found!
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" main.py
exit
