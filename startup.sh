#!/bin/bash
# Auto-startup script for Voice AI Server on RunPod
# This runs automatically when the pod starts

LOGFILE="/workspace/voice-ai/server.log"

echo "========================================" >> $LOGFILE
echo "Voice AI Auto-Startup" >> $LOGFILE
echo "$(date)" >> $LOGFILE
echo "========================================" >> $LOGFILE

# Create directory
mkdir -p /workspace/voice-ai
cd /workspace/voice-ai

# Check if already set up
if [ ! -f "/workspace/voice-ai/.setup_complete" ]; then
    echo "First time setup..." >> $LOGFILE
    
    # Install dependencies
    pip install flask flask-cors twilio python-dotenv edge-tts -q >> $LOGFILE 2>&1
    
    # Create server.py
    cat > /workspace/voice-ai/server.py << 'SERVEREOF'
import os
import sys
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

# Load env vars
load_dotenv()

app = Flask(__name__)

# Twilio setup
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER]):
    print("ERROR: Missing Twilio credentials!")
    print("Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER")
    sys.exit(1)

client = Client(TWILIO_SID, TWILIO_TOKEN)

print("="*60)
print("Voice AI Server - Running on RunPod")
print("="*60)
print(f"Twilio Number: {TWILIO_NUMBER}")
print(f"Port: 5001")
print("="*60)

@app.route("/")
def home():
    return """
    <h1>Voice AI Server</h1>
    <p>Status: Running</p>
    <p>Twilio Webhook: /voice/webhook</p>
    <p>API: /call (POST)</p>
    <hr>
    <p><a href="/health">Health Check</a></p>
    """

@app.route("/health")
def health():
    return {
        "status": "ok",
        "twilio_number": TWILIO_NUMBER,
        "server": "voice-ai",
        "port": 5001
    }

@app.route("/voice/webhook", methods=['POST'])
def webhook():
    """Handle incoming calls"""
    response = VoiceResponse()
    response.say("Hello! You've reached the AI voice assistant.", voice='Polly.Matthew')
    
    gather = Gather(
        input='speech',
        action='/voice/respond',
        timeout=5,
        language='en-US'
    )
    gather.say("How can I help you today?", voice='Polly.Matthew')
    response.append(gather)
    
    return str(response)

@app.route("/voice/respond", methods=['POST'])
def respond():
    """Respond to caller"""
    response = VoiceResponse()
    speech = request.form.get('SpeechResult', '')
    
    if speech:
        reply = f"You said: {speech}. I'm your AI assistant running on RunPod!"
        response.say(reply, voice='Polly.Matthew')
        
        # Continue conversation
        gather = Gather(input='speech', action='/voice/respond', timeout=5)
        gather.say("Anything else?", voice='Polly.Matthew')
        response.append(gather)
    else:
        response.say("I didn't catch that.", voice='Polly.Matthew')
        response.redirect('/voice/webhook')
    
    return str(response)

@app.route("/call", methods=['POST'])
def make_call():
    """Make outbound call"""
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message', 'Hello from AI!')
    emotion = data.get('emotion', 'default')
    
    if not to_number:
        return jsonify({'error': 'No phone number provided'}), 400
    
    # Map emotion to voice
    voices = {
        'default': 'Polly.Matthew',
        'excited': 'Polly.Joanna',
        'friendly': 'Polly.Kimberly',
        'calm': 'Polly.Salli',
        'professional': 'Polly.Joey'
    }
    voice = voices.get(emotion, 'Polly.Matthew')
    
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
        'status': call.status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
SERVEREOF

    # Mark setup complete
    touch /workspace/voice-ai/.setup_complete
    echo "Setup complete!" >> $LOGFILE
fi

# Start server
echo "Starting server..." >> $LOGFILE
cd /workspace/voice-ai
exec python server.py >> $LOGFILE 2>&1
