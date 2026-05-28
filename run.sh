#!/bin/bash

# Video Caption Maker Launcher
# This script launches the web app and opens it in Chrome

echo "🎬 Video Caption Maker - Starting..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Navigate to app directory
cd "$(dirname "$0")"

# Create required directories if they don't exist
mkdir -p background audio output presets

# Install required packages if needed
echo "📦 Checking dependencies..."
pip3 install flask flask-cors openai-whisper moviepy --quiet --root-user-action=ignore 2>/dev/null

# Start the Flask server in background
echo "🚀 Starting server..."
python3 app.py > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to be ready..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Server failed to start. Check server.log for details."
    cat server.log
    exit 1
fi

# Try to open in Chrome
if command -v google-chrome &> /dev/null; then
    google-chrome http://localhost:5000 --new-window
elif command -v chromium-browser &> /dev/null; then
    chromium-browser http://localhost:5000 --new-window
elif command -v chromium &> /dev/null; then
    chromium http://localhost:5000 --new-window
elif command -v chrome &> /dev/null; then
    chrome http://localhost:5000 --new-window
else
    echo "⚠️  Chrome not found. Please open http://localhost:5000 in your browser manually."
fi

echo ""
echo "✅ Server is running at http://localhost:5000"
echo "📁 Background videos folder: $(pwd)/background"
echo "🎵 Audio files folder: $(pwd)/audio"
echo "📤 Output folder: $(pwd)/output"
echo "💾 Presets folder: $(pwd)/presets"
echo ""
echo "Press Ctrl+C to stop the server"

# Keep the script running and handle cleanup
trap "kill $SERVER_PID 2>/dev/null; echo 'Server stopped.'; exit 0" INT TERM

# Wait for server process
wait $SERVER_PID
