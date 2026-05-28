from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import os
import json
import random
import subprocess
import time
import threading
import whisper

app = Flask(__name__)
CORS(app)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_DIR = os.path.join(BASE_DIR, 'background')
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PRESETS_DIR = os.path.join(BASE_DIR, 'presets')
USED_FILES = os.path.join(BASE_DIR, 'used_files.json')

# Ensure directories exist
for directory in [BACKGROUND_DIR, AUDIO_DIR, OUTPUT_DIR, PRESETS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Initialize used files tracking
if not os.path.exists(USED_FILES):
    with open(USED_FILES, 'w') as f:
        json.dump({'videos': [], 'audios': []}, f)

def get_used_files():
    try:
        with open(USED_FILES, 'r') as f:
            return json.load(f)
    except:
        return {'videos': [], 'audios': []}

def save_used_files(data):
    with open(USED_FILES, 'w') as f:
        json.dump(data, f)

def count_files(directory, extensions):
    if not os.path.exists(directory):
        return 0
    count = 0
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in extensions):
            count += 1
    return count

def get_video_files():
    if not os.path.exists(BACKGROUND_DIR):
        return []
    return [f for f in os.listdir(BACKGROUND_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]

def get_audio_files():
    if not os.path.exists(AUDIO_DIR):
        return []
    return [f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac'))]

def get_output_files():
    if not os.path.exists(OUTPUT_DIR):
        return []
    return [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.mp4')]

def get_presets():
    presets = []
    if os.path.exists(PRESETS_DIR):
        for file in os.listdir(PRESETS_DIR):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(PRESETS_DIR, file), 'r') as f:
                        preset = json.load(f)
                        preset['filename'] = file
                        presets.append(preset)
                except:
                    pass
    return presets

def save_preset(preset_data):
    filename = preset_data['name'].replace(' ', '_').lower() + '.json'
    filepath = os.path.join(PRESETS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(preset_data, f, indent=2)
    return True

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_audio_duration(audio_path):
    """Get audio duration in seconds using ffprobe"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper (offline)"""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['segments']

def create_caption_filter(segments, preset, video_width=1080, video_height=1920):
    """Create FFmpeg filter for captions"""
    # Calculate scale factor for 9:16 ratio at 1080px width
    scale_factor = video_width / 1080
    
    fonts_dir = "/usr/share/fonts"
    font_files = []
    for root, dirs, files in os.walk(fonts_dir):
        for file in files:
            if file.endswith('.ttf') or file.endswith('.otf'):
                font_files.append(os.path.join(root, file))
    
    font_file = random.choice(font_files) if font_files else ""
    
    # Escape text for FFmpeg
    def escape_text(text):
        return text.replace("'", "'\\''").replace(':', '\\:').replace(',', '\\,')
    
    filters = []
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = escape_text(segment['text'].strip())
        
        # Caption styling based on preset
        font_size = int(preset.get('fontSize', 32)) * scale_factor
        font_color = preset.get('textColor', '#ffffff').replace('#', '')
        bg_color = preset.get('bgColor', '#000000').replace('#', '')
        bg_opacity = int(preset.get('bgOpacity', 80)) / 255.0
        box_border_radius = int(preset.get('borderRadius', 10)) * scale_factor
        padding = int(preset.get('padding', 10)) * scale_factor
        
        # Position calculation
        pos_x = int(preset.get('posX', 50))
        pos_y = int(preset.get('posY', 50))
        
        # Convert percentage to pixels
        x_pos = int((pos_x / 100) * video_width)
        y_pos = int((pos_y / 100) * video_height)
        
        # Glow effect
        glow_enabled = preset.get('glowEnabled', False)
        glow_color = preset.get('glowColor', '#667eea').replace('#', '')
        glow_size = int(preset.get('glowSize', 10)) * scale_factor
        
        shadow = ""
        if glow_enabled:
            shadow = f":shadowcolor={glow_color}:shadowx=0:shadowy=0:shadowblur={glow_size}"
        
        filter_str = f"drawtext=text='{text}':fontfile={font_file}:fontsize={font_size}:fontcolor={font_color}:x={x_pos}:y={y_pos}:enable='between(t,{start},{end})':box=1:boxcolor={bg_color}@{bg_opacity}:boxborderw={padding}:borderw=0:font={preset.get('fontFamily', 'Arial')}:text_align={preset.get('textAlign', 'center')}{shadow}"
        filters.append(filter_str)
    
    return ','.join(filters)

def generate_video_stream():
    """Generate videos with captions"""
    def generate():
        try:
            used = get_used_files()
            used_videos = used['videos']
            used_audios = used['audios']
            
            all_videos = get_video_files()
            all_audios = get_audio_files()
            
            # Filter out used files
            available_videos = [v for v in all_videos if v not in used_videos]
            available_audios = [a for a in all_audios if a not in used_audios]
            
            if not available_audios:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No unused audio files available'})}\n\n"
                return
            
            if not available_videos:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No unused video files available'})}\n\n"
                return
            
            presets = get_presets()
            if not presets:
                # Default preset
                presets = [{
                    'fontSize': '32',
                    'textColor': '#ffffff',
                    'bgColor': '#000000',
                    'bgOpacity': '80',
                    'posX': '50',
                    'posY': '80',
                    'textAlign': 'center',
                    'borderRadius': '10',
                    'padding': '10',
                    'glowEnabled': False,
                    'glowColor': '#667eea',
                    'glowSize': '10',
                    'fontFamily': 'Arial'
                }]
            
            total_audios = len(available_audios)
            processed = 0
            
            for audio_file in available_audios:
                audio_path = os.path.join(AUDIO_DIR, audio_file)
                
                # Get audio duration
                audio_duration = get_audio_duration(audio_path)
                yield f"data: {json.dumps({'type': 'log', 'message': f'Processing audio: {audio_file} (Duration: {audio_duration:.2f}s)'})}\n\n"
                
                # Select random unused video(s) that match audio length
                selected_videos = []
                total_video_duration = 0
                
                random.shuffle(available_videos)
                
                for video_file in available_videos:
                    if total_video_duration >= audio_duration:
                        break
                    
                    video_path = os.path.join(BACKGROUND_DIR, video_file)
                    video_duration = get_video_duration(video_path)
                    selected_videos.append((video_file, video_path, video_duration))
                    total_video_duration += video_duration
                
                if not selected_videos:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Skipping {audio_file}: No suitable videos found'})}\n\n"
                    continue
                
                # Choose random preset
                preset = random.choice(presets)
                preset_name = preset.get("name", "Default")
                yield f"data: {json.dumps({'type': 'log', 'message': f'Using preset: {preset_name}'})}\n\n"
                
                # Transcribe audio
                yield f"data: {json.dumps({'type': 'log', 'message': 'Transcribing audio...'})}\n\n"
                segments = transcribe_audio(audio_path)
                
                if not segments:
                    yield f"data: {json.dumps({'type': 'log', 'message': 'No transcription found, skipping...'})}\n\n"
                    continue
                
                # Create output filename
                output_filename = f"video_{int(time.time())}_{audio_file.rsplit('.', 1)[0]}.mp4"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                # Build FFmpeg command
                # First, concatenate videos and mute them
                concat_file = os.path.join(BASE_DIR, 'concat_list.txt')
                with open(concat_file, 'w') as f:
                    for video_file, video_path, _ in selected_videos:
                        f.write(f"file '{video_path}'\n")
                
                # Create temporary muted concatenated video
                temp_video = os.path.join(BASE_DIR, 'temp_concat.mp4')
                
                yield f"data: {json.dumps({'type': 'log', 'message': 'Concatenating and muting videos...'})}\n\n"
                
                concat_cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat', '-safe', '0', '-i', concat_file,
                    '-c', 'copy', '-an',
                    temp_video
                ]
                
                subprocess.run(concat_cmd, capture_output=True)
                
                # Get concatenated video duration
                concat_duration = get_video_duration(temp_video)
                
                # Trim or loop video to match audio length
                temp_trimmed = os.path.join(BASE_DIR, 'temp_trimmed.mp4')
                
                if concat_duration < audio_duration:
                    # Loop video to match audio length
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Looping video to match audio length ({audio_duration:.2f}s)...'})}\n\n"
                    loop_cmd = [
                        'ffmpeg', '-y',
                        '-stream_loop', '-1',
                        '-i', temp_video,
                        '-t', str(audio_duration),
                        '-c:v', 'libx264', '-an',
                        temp_trimmed
                    ]
                else:
                    # Trim video to match audio length
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Trimming video to match audio length ({audio_duration:.2f}s)...'})}\n\n"
                    loop_cmd = [
                        'ffmpeg', '-y',
                        '-i', temp_video,
                        '-t', str(audio_duration),
                        '-c:v', 'libx264', '-an',
                        temp_trimmed
                    ]
                
                subprocess.run(loop_cmd, capture_output=True)
                
                # Add captions and audio
                yield f"data: {json.dumps({'type': 'log', 'message': 'Adding captions and audio...'})}\n\n"
                
                caption_filter = create_caption_filter(segments, preset)
                
                final_cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_trimmed,
                    '-i', audio_path,
                    '-vf', caption_filter,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-shortest',
                    '-pix_fmt', 'yuv420p',
                    output_path
                ]
                
                result = subprocess.run(final_cmd, capture_output=True, text=True)
                
                # Cleanup temp files
                for temp_file in [concat_file, temp_video, temp_trimmed]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                # Mark files as used
                used['videos'].extend([v[0] for v in selected_videos])
                used['audios'].append(audio_file)
                save_used_files(used)
                
                processed += 1
                progress = int((processed / total_audios) * 100)
                
                yield f"data: {json.dumps({'type': 'progress', 'progress': progress})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': f'Completed: {output_filename}'})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'message': 'All videos generated successfully!'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac']
    output_extensions = ['.mp4']
    
    return jsonify({
        'videos': count_files(BACKGROUND_DIR, video_extensions),
        'audios': count_files(AUDIO_DIR, audio_extensions),
        'outputs': count_files(OUTPUT_DIR, output_extensions)
    })

@app.route('/api/presets', methods=['GET'])
def get_presets_api():
    presets = get_presets()
    return jsonify(presets)

@app.route('/api/presets', methods=['POST'])
def save_preset_api():
    try:
        preset_data = request.json
        if not preset_data or 'name' not in preset_data:
            return jsonify({'success': False, 'error': 'Invalid preset data'}), 400
        
        save_preset(preset_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate')
def generate():
    return generate_video_stream()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎬 Video Caption Maker")
    print("="*50)
    print(f"📁 Background videos: {BACKGROUND_DIR}")
    print(f"🎵 Audio files: {AUDIO_DIR}")
    print(f"📤 Output folder: {OUTPUT_DIR}")
    print(f"💾 Presets: {PRESETS_DIR}")
    print("="*50)
    print("\n🌐 Starting server...")
    print("Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
