@echo off
title Video Caption Maker Launcher
color 0A

echo ==========================================
echo   Video Caption Maker - Setup & Launch
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected.
echo.

REM Create necessary folders if they don't exist
if not exist "background" mkdir background
if not exist "audio" mkdir audio
if not exist "output" mkdir output
if not exist "presets" mkdir presets
echo [OK] Folders created/verified.
echo.

REM Install/Upgrade required Python packages
echo Installing/Updating required packages...
echo This may take a few minutes on first run...
echo.

pip install --quiet flask flask-cors openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 2>nul
if %errorlevel% neq 0 (
    REM Fallback to CPU version if GPU version fails
    pip install --quiet flask flask-cors openai-whisper torch torchvision torchaudio
)

pip install --quiet moviepy numpy scipy librosa

echo [OK] Packages installed/updated.
echo.

REM Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg not found in PATH.
    echo The app may not work correctly without FFmpeg.
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo.
) else (
    echo [OK] FFmpeg detected.
)

echo.
echo ==========================================
echo   Starting Web Server...
echo ==========================================
echo.
echo Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Start the Flask application
python app.py

pause
