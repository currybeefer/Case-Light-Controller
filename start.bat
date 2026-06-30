@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start /b pythonw src\fan_control.py
    exit /b
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    python src\fan_control.py
    exit /b
)
echo [Error] Python not found. Please install Python 3 from https://python.org
pause
