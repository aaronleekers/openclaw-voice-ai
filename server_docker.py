import os
import sys
import uuid
import json
import torch
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from TTS.api import TTS

app = Flask(__name__)
CORS(app)

print("="*60)
print("🎙️  Voice AI Server with XTTS v2")
print("="*60)

# Setup device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\n📦 Device: {device}")
if device == "cuda":
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Create directories
VOICES_DIR = "/app/voices"
SAMPLES_DIR = "/app/samples"
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

# Load XTTS v2
print("\n⬇️  Loading XTTS v2 model (1.87GB)...")
try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)

print("\n" + "="*60)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/status')
def status():
    voices = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    return jsonify({
        'status': 'ready',
        'device': device,
        'gpu': torch.cuda.get_device_name(0) if device == 'cuda' else None,
        'voices': voices,
        'model': 'XTTS v2'
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
    
    voice_path = os.path.join(VOICES_DIR, f"{voice_name}.wav")
    file.save(voice_path)
    
    return jsonify({
        'message': 'Voice uploaded successfully!',
        'voice': voice_name,
        'path': voice_path
    })

@app.route('/speak_cloned', methods=['POST'])
def speak_cloned():
    """Generate speech using voice cloning"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Find uploaded voice
    voice_files = [f for f in os.listdir(VOICES_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]
    
    if not voice_files:
        return jsonify({'error': 'No voice uploaded. Upload a voice first.'}), 400
    
    try:
        speaker_wav = os.path.join(VOICES_DIR, voice_files[0])
        out_path = f"/tmp/{uuid.uuid4()}.wav"
        
        print(f"🎯 Cloning voice from: {voice_files[0]}")
        print(f"📝 Text: {text[:50]}...")
        
        # Clone the voice
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language="en",
            file_path=out_path
        )
        
        print("✅ Speech generated!")
        return send_file(out_path, mimetype='audio/wav')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/speak', methods=['POST'])
def speak():
    """Generate speech without cloning (default voice)"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        out_path = f"/tmp/{uuid.uuid4()}.wav"
        
        # Use default speaker
        tts.tts_to_file(
            text=text,
            speaker_wav=None,
            language="en",
            file_path=out_path
        )
        
        return send_file(out_path, mimetype='audio/wav')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Starting server on http://0.0.0.0:5000")
    print("📱 Access at: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
