@echo off
title Video Caption Maker Launcher
color 0A

echo ==========================================
echo   Video Caption Maker - Setup ^& Launch
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

REM Check if requirements are already installed
echo Checking installed packages...
python -c "import flask; import whisper; import moviepy; import torch" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] All required packages already installed.
    echo.
) else (
    echo Installing required packages for the first time...
    echo This may take several minutes depending on your internet speed...
    echo.
    
    python -m pip install --upgrade pip --quiet
    
    echo Installing Flask and dependencies...
    python -m pip install flask flask-cors --quiet
    
    echo Installing PyTorch (this is large, please wait)...
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
    
    echo Installing Whisper AI...
    python -m pip install openai-whisper --quiet
    
    echo Installing MoviePy and audio processing libraries...
    python -m pip install moviepy numpy scipy librosa --quiet
    
    echo.
    echo [OK] All packages installed successfully!
    echo.
)

REM Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg not found in PATH.
    echo The app may not work correctly without FFmpeg.
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo OR place ffmpeg.exe in this folder.
    echo.
) else (
    echo [OK] FFmpeg detected.
)

echo.
echo ==========================================
echo   Starting Web Server...
echo ==========================================
echo.
echo Opening browser in 3 seconds...
echo If it doesn't open, manually go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Wait 3 seconds then open browser
timeout /t 3 /nobreak >nul
start http://localhost:5000

REM Start the Flask application (runs until Ctrl+C)
python app.py
