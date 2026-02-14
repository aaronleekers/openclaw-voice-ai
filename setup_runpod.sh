#!/bin/bash
# RunPod Voice AI Setup Script
# Run this inside your RunPod instance

set -e

echo "=================================="
echo "🚀 RunPod Voice AI Setup"
echo "=================================="
echo ""

# Check if we're on RunPod
if [ ! -d "/workspace" ]; then
    echo "⚠️  Warning: /workspace not found. Are you on RunPod?"
fi

WORKDIR="/workspace/voice-ai"
mkdir -p $WORKDIR
cd $WORKDIR

echo "📦 Installing dependencies..."
pip install -q flask flask-cors twilio python-dotenv edge-tts

echo "📝 Creating server files..."

# Create .env template
cat > .env << 'EOF'
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+15097403244
EOF

echo "⚠️  IMPORTANT: Edit .env file with your actual Twilio credentials!"
echo ""

# Create the server
cat > runpod_server.py << 'EOF'
"""RunPod Voice AI Server"""
import os
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

client = Client(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID else None

print("="*60)
print("Voice AI Server Running!")
print(f"Twilio: {TWILIO_NUMBER}")
print("="*60)

@app.route("/")
def index():
    return "Voice AI Server - Running!"

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/voice/webhook", methods=['POST'])
def webhook():
    response = VoiceResponse()
    response.say("Hello! AI Voice Server is working!", voice='Polly.Matthew')
    
    gather = Gather(input='speech', action='/voice/respond')
    gather.say("What can I help you with?")
    response.append(gather)
    
    return str(response)

@app.route("/voice/respond", methods=['POST'])
def respond():
    response = VoiceResponse()
    speech = request.form.get('SpeechResult', '')
    
    if speech:
        response.say(f"You said: {speech}", voice='Polly.Matthew')
    else:
        response.say("I didn't catch that.", voice='Polly.Matthew')
    
    return str(response)

@app.route("/call", methods=['POST'])
def call():
    if not client:
        return jsonify({'error': 'Twilio not configured'}), 500
    
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message', 'Hello!')
    
    if not to_number:
        return jsonify({'error': 'No number'}), 400
    
    twiml = VoiceResponse()
    twiml.say(message, voice='Polly.Matthew')
    
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=TWILIO_NUMBER
    )
    
    return jsonify({'call_sid': call.sid})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
EOF

echo "✅ Files created!"
echo ""
echo "=================================="
echo "Next Steps:"
echo "=================================="
echo ""
echo "1. Edit .env file:"
echo "   nano .env"
echo ""
echo "2. Add your Twilio credentials:"
echo "   TWILIO_ACCOUNT_SID=AC..."
echo "   TWILIO_AUTH_TOKEN=..."
echo "   TWILIO_FROM_NUMBER=+15097403244"
echo ""
echo "3. Start server:"
echo "   python runpod_server.py"
echo ""
echo "4. Your public URL:"
echo "   https://[pod-id]-5001.proxy.runpod.net"
echo ""
echo "5. Set Twilio webhook to:"
echo "   https://[pod-id]-5001.proxy.runpod.net/voice/webhook"
echo ""
echo "=================================="
