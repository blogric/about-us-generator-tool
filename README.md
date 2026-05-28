# 🎬 Video Caption Maker

A lightweight local web application for automatically generating videos with captions from audio files.

## Features

- **Caption Designer**: Create and customize caption designs with live preview
  - Font family, size, weight, and color
  - Background color and opacity
  - Position controls (horizontal & vertical)
  - Text alignment
  - Glow effects
  - Border radius and padding
  - Save and load presets locally

- **Video Maker**: Automatic video generation
  - Detects videos in `background` folder
  - Detects audio files in `audio` folder
  - Mutes background videos
  - Transcribes audio offline using Whisper AI
  - Matches video length to audio duration
  - Applies random caption presets
  - Exports in MP4 format (9:16 ratio, 1080px width)
  - Tracks used files to avoid duplicates

## Installation

### Requirements
- Python 3.8 or higher
- FFmpeg (for video processing)
- Chrome/Chromium browser

### Setup

1. Navigate to the application folder:
   ```bash
   cd /workspace
   ```

2. Run the launcher script:
   ```bash
   ./run.sh
   ```

   Or manually:
   ```bash
   # Install dependencies
   pip3 install flask flask-cors openai-whisper moviepy

   # Start the server
   python3 app.py
   ```

3. Open your browser to `http://localhost:5000`

## Usage

### Caption Designer Tab

1. Adjust caption settings using the controls on the left
2. See live preview on the right side
3. Enter a preset name and click "Save Preset"
4. Load saved presets anytime

### Video Maker Tab

1. Place your background videos in the `background` folder
2. Place your audio files in the `audio` folder
3. View file counts at the top
4. Click "Execute Generation" to start
5. Monitor progress in the log output
6. Find generated videos in the `output` folder

## Folder Structure

```
/workspace/
├── app.py              # Main application
├── run.sh             # Launcher script
├── templates/
│   └── index.html     # Web interface
├── background/        # Place background videos here
├── audio/            # Place audio files here
├── output/           # Generated videos appear here
├── presets/          # Saved caption presets
└── used_files.json   # Tracks processed files
```

## Supported Formats

- **Videos**: MP4, AVI, MOV, MKV
- **Audio**: MP3, WAV, M4A, AAC
- **Output**: MP4 (H.264 video, AAC audio)

## Technical Details

- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Backend**: Flask (Python)
- **Transcription**: OpenAI Whisper (offline)
- **Video Processing**: FFmpeg
- **Storage**: Local JSON files for presets and tracking

## Notes

- The app runs completely offline after initial Whisper model download
- Videos are automatically muted during processing
- Each audio file is processed only once (tracked in used_files.json)
- To reset tracking, delete the `used_files.json` file
