@echo off
echo ========================================
echo    PROTEIN TRACKER SERVER LAUNCHER
echo ========================================
echo.
echo Starting server...
echo.
echo Open your browser and go to:
echo   http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
.venv\Scripts\python.exe main.py

pause
