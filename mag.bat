@echo off
REM Check if python is accessible in the environment path
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not added to your system PATH environment variable.
    pause
    exit /b
)

REM Run the CLI script and pass through all arguments
python "%~dp0mag.py" %*