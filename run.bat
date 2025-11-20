@echo off
echo ========================================
echo  Vehicle Detection System - Starting
echo ========================================
echo.

REM Activate virtual environment
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Start uvicorn server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
