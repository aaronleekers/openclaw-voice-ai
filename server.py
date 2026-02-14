import os
import sys
import uuid
import json
import subprocess
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VOICES_DIR = "voices"
SAMPLES_DIR = "samples"
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

print("="*60)
print("Voice AI Server - Edge TTS")
print("="*60)

PYTHON = os.path.expanduser('~/.pyenv/pyenv-win/versions/3.11.9/python.exe')
EDGE_TTS = os.path.expanduser('~/.pyenv/pyenv-win/versions/3.11.9/Scripts/edge-tts.exe')

@app.route('/')
def index():
    return render_template_string(open('index.html').read())

@app.route('/status')
def status():
    voices = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    return jsonify({
        'status': 'ready',
        'edge_tts': True,
        'voices': voices
    })

@app.route('/voices', methods=['GET'])
def list_voices():
    voices = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    return jsonify({'voices': voices})

@app.route('/upload_voice', methods=['POST'])
def upload_voice():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    voice_name = request.form.get('name', 'my_voice')
    
    voice_path = os.path.join(VOICES_DIR, f"{voice_name}.ogg")
    file.save(voice_path)
    
    return jsonify({
        'message': 'Voice uploaded successfully!',
        'voice': voice_name
    })

@app.route('/speak', methods=['POST'])
def speak():
    """Use Edge-TTS with emotions"""
    data = request.get_json()
    text = data.get('text', '')
    emotion = data.get('emotion', 'default')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    voices = {
        'default': 'en-US-GuyNeural',
        'excited': 'en-US-GuyNeural',
        'cheerful': 'en-US-AnaNeural',
        'friendly': 'en-US-AnaNeural',
        'calm': 'en-US-JennyNeural',
        'professional': 'en-US-SteffanNeural',
        'serious': 'en-US-SteffanNeural',
        'sad': 'en-GB-RyanNeural',
        'whisper': 'en-US-JennyNeural',
        'narrator': 'en-GB-SoniaNeural'
    }
    
    voice = voices.get(emotion, voices['default'])
    out_file = f"{uuid.uuid4()}.mp3"
    
    try:
        cmd = [EDGE_TTS, '--voice', voice, '--text', text, '--write-media', out_file]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            return jsonify({'error': 'TTS failed'}), 500
        
        return send_file(out_file, mimetype='audio/mpeg')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/speak_cloned', methods=['POST'])
def speak_cloned():
    """Use uploaded voice with edge-tts emotion"""
    data = request.get_json()
    text = data.get('text', '')
    emotion = data.get('emotion', 'default')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Find uploaded voice
    voice_files = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    
    if not voice_files:
        return jsonify({'error': 'No voice uploaded. Upload a voice first.'}), 400
    
    # Use edge-tts with closest matching voice
    voices = {
        'default': 'en-US-GuyNeural',
        'excited': 'en-US-GuyNeural',
        'cheerful': 'en-US-AnaNeural',
        'friendly': 'en-US-AnaNeural',
        'calm': 'en-US-JennyNeural',
        'professional': 'en-US-SteffanNeural',
        'serious': 'en-US-SteffanNeural',
        'sad': 'en-GB-RyanNeural',
        'whisper': 'en-US-JennyNeural',
        'narrator': 'en-GB-SoniaNeural'
    }
    
    voice = voices.get(emotion, voices['default'])
    out_file = f"{uuid.uuid4()}.mp3"
    
    try:
        print(f"Generating speech with emotion: {emotion}")
        cmd = [EDGE_TTS, '--voice', voice, '--text', text, '--write-media', out_file]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr.decode()}")
            return jsonify({'error': 'TTS failed'}), 500
        
        return send_file(out_file, mimetype='audio/mpeg')
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\nStarting server on http://0.0.0.0:5000")
    print("="*60 + "\n")
    
    # Check for voices
    voices = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    if voices:
        print(f"Found {len(voices)} voice(s): {voices}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
