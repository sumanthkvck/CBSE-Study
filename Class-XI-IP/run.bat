@echo off
title IP Learn — Class XI Informatics Practices
echo.
echo  ====================================
echo   IP Learn — Class XI CBSE
echo  ====================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo.
    echo  Please install Python 3.8+ from:
    echo    https://python.org/downloads
    echo.
    echo  IMPORTANT: During install, check the box that says
    echo  "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo  Checking and installing dependencies...
python -m pip install -r requirements.txt --quiet --upgrade
if errorlevel 1 (
    echo.
    echo  ERROR: Could not install dependencies.
    echo  Try running this window as Administrator.
    pause
    exit /b 1
)

echo.
echo  Starting IP Learn...
echo  The app will open in your browser at http://localhost:8501
echo  Keep this window open while using the app.
echo  Press Ctrl+C or close this window to stop.
echo.
python -m streamlit run app/main.py
echo.
echo  App stopped.
pause
