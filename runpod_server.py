"""
RunPod Voice AI Server
Combines Twilio voice calls + PersonaPlex TTS
"""
import os
import sys
import uuid
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Config
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

print("="*60)
print("RunPod Voice AI Server")
print("="*60)
print(f"Twilio Number: {TWILIO_NUMBER}")
print(f"Server: http://0.0.0.0:5001")
print("="*60)

# Voice mapping for Edge-TTS
VOICES = {
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

# Twilio voice mapping
TWILIO_VOICES = {
    'default': 'Polly.Matthew',
    'excited': 'Polly.Joanna',
    'cheerful': 'Polly.Kendra',
    'friendly': 'Polly.Kimberly',
    'calm': 'Polly.Salli',
    'professional': 'Polly.Joey',
    'serious': 'Polly.Justin',
    'sad': 'Polly.Emma',
    'whisper': 'Polly.Ivy',
    'narrator': 'Polly.Brian'
}

@app.route("/")
def index():
    return """
    <h1>RunPod Voice AI Server</h1>
    <p>Status: Running</p>
    <p>Twilio Webhook: /voice/webhook</p>
    <p>API: /call (POST)</p>
    """

@app.route("/health")
def health():
    return {"status": "ok", "twilio": client is not None}

@app.route("/voice/webhook", methods=['POST'])
def voice_webhook():
    """Handle incoming Twilio calls"""
    response = VoiceResponse()
    
    # Welcome message
    response.say(
        "Hello! You've reached the AI voice assistant. How can I help you today?",
        voice='Polly.Matthew'
    )
    
    # Gather speech input
    gather = Gather(
        input='speech',
        action='/voice/respond',
        language='en-US',
        speech_timeout='auto',
        hints='help, support, question, hello'
    )
    gather.say("Please tell me what you need.", voice='Polly.Matthew')
    response.append(gather)
    
    # Timeout fallback
    response.redirect('/voice/webhook')
    
    return str(response)

@app.route("/voice/respond", methods=['POST'])
def voice_respond():
    """Respond to caller's speech"""
    response = VoiceResponse()
    
    speech = request.form.get('SpeechResult', '')
    
    if speech:
        # Simple echo response (replace with AI logic)
        reply = f"I heard you say: {speech}. Let me help you with that."
        response.say(reply, voice='Polly.Matthew')
        
        # Continue conversation
        gather = Gather(input='speech', action='/voice/respond', timeout=5)
        gather.say("What else can I do for you?", voice='Polly.Matthew')
        response.append(gather)
    else:
        response.say("I didn't catch that. Could you repeat?", voice='Polly.Matthew')
        response.redirect('/voice/webhook')
    
    return str(response)

@app.route("/call", methods=['POST'])
def make_call():
    """Make outbound call with AI voice"""
    if not client:
        return jsonify({'error': 'Twilio not configured'}), 500
    
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message', 'Hello from AI Voice!')
    emotion = data.get('emotion', 'default')
    
    if not to_number:
        return jsonify({'error': 'No phone number'}), 400
    
    # Use Twilio's voice (similar to our Edge-TTS emotions)
    voice = TWILIO_VOICES.get(emotion, 'Polly.Matthew')
    
    twiml = VoiceResponse()
    twiml.say(message, voice=voice)
    
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=TWILIO_NUMBER
    )
    
    return jsonify({
        'success': True,
        'call_sid': call.sid,
        'to': to_number,
        'emotion': emotion
    })

@app.route("/tts", methods=['POST'])
def text_to_speech():
    """Generate AI voice audio (Edge-TTS)"""
    data = request.get_json()
    text = data.get('text', '')
    emotion = data.get('emotion', 'default')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    voice = VOICES.get(emotion, VOICES['default'])
    filename = f"tts_{uuid.uuid4()}.mp3"
    filepath = f"/tmp/{filename}"
    
    try:
        cmd = ['edge-tts', '--voice', voice, '--text', text, '--write-media', filepath]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode == 0:
            return send_file(filepath, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'TTS generation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/voices")
def list_voices():
    """List available voices"""
    return jsonify({
        'edge_tts': VOICES,
        'twilio': TWILIO_VOICES
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
