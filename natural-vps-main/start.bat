@echo off
REM Natural VPS Startup Script
cd /d "%~dp0"

echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if not errorlevel 1 (
    echo Port 5000 is already in use. Choose a different port:
    echo set PORT=8000
    set /p PORT="Enter port (default 5000): "
    if "%PORT%"=="" set PORT=5000
)

echo.
echo Starting Natural VPS...
echo.

python run.py

pause
