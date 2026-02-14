#!/usr/bin/env python3
"""
OpenClaw Voice Bridge - REST API for Twilio Voice Control
This allows OpenClaw to trigger calls, send TTS messages, and manage voice interactions
"""

import os
import sys
import json
import time
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from functools import wraps

app = Flask(__name__)

# Twilio credentials from env
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# Simple API key for security
API_KEY = os.getenv('VOICE_API_KEY', 'openclaw-voice-secret')

# Initialize Twilio
client = Client(TWILIO_SID, TWILIO_TOKEN)

# Track active calls
active_calls = {}

def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Voice-Key') or request.args.get('key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

print("="*60)
print("OpenClaw Voice Bridge")
print("="*60)
print(f"Twilio: {TWILIO_NUMBER}")
print(f"API Key: {API_KEY}")
print("="*60)

@app.route("/")
def home():
    return jsonify({
        "service": "OpenClaw Voice Bridge",
        "endpoints": [
            "POST /api/call - Make outbound call",
            "POST /api/speak - Send TTS to active call",
            "POST /api/end - Hang up call",
            "GET /api/calls - List active calls",
            "GET /api/status - Check service status"
        ]
    })

@app.route("/api/status")
@require_key
def status():
    return jsonify({
        "status": "running",
        "twilio_connected": bool(client),
        "twilio_number": TWILIO_NUMBER,
        "active_calls": len(active_calls)
    })

@app.route("/api/call", methods=['POST'])
@require_key
def make_call():
    """Make an outbound call"""
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message', 'Hello from OpenClaw!')
    emotion = data.get('emotion', 'Polly.Matthew')
    
    if not to_number:
        return jsonify({'error': 'Missing phone number'}), 400
    
    try:
        # Create TwiML response
        twiml = VoiceResponse()
        twiml.say(message, voice=emotion)
        
        gather = Gather(action=request.url_root + 'api/gather', timeout=10, speechTimeout='auto')
        gather.say("Please speak your response.", voice=emotion)
        twiml.append(gather)
        
        # Make the call
        call = client.calls.create(
            twiml=str(twiml),
            to=to_number,
            from_=TWILIO_NUMBER,
            status_callback=request.url_root + 'api/status_callback',
            status_callback_event=['completed', 'answered']
        )
        
        active_calls[call.sid] = {
            'to': to_number,
            'message': message,
            'status': 'initiated',
            'started': time.time()
        }
        
        return jsonify({
            'success': True,
            'call_sid': call.sid,
            'to': to_number,
            'status': call.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/speak", methods=['POST'])
@require_key
def speak():
    """Send TTS to active call"""
    data = request.get_json()
    call_sid = data.get('call_sid')
    message = data.get('message')
    emotion = data.get('emotion', 'Polly.Matthew')
    
    if not call_sid or not message:
        return jsonify({'error': 'Missing call_sid or message'}), 400
    
    try:
        twiml = VoiceResponse()
        twiml.say(message, voice=emotion)
        
        client.calls(call_sid).update(twiml=str(twiml))
        
        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/gather", methods=['POST'])
def gather_response():
    """Handle caller's speech response"""
    speech = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid', '')
    
    # Store for OpenClaw to retrieve
    if call_sid in active_calls:
        active_calls[call_sid]['last_response'] = speech
        active_calls[call_sid]['last_response_time'] = time.time()
    
    # Respond back
    response = VoiceResponse()
    if speech:
        response.say(f"You said: {speech}", voice='Polly.Matthew')
    else:
        response.say("I didn't catch that. Goodbye!", voice='Polly.Matthew')
    
    response.hangup()
    return str(response)

@app.route("/api/calls")
@require_key
def list_calls():
    """List all calls with responses"""
    # Clean up old calls
    now = time.time()
    for sid in list(active_calls.keys()):
        if now - active_calls[sid].get('started', 0) > 3600:
            del active_calls[sid]
    
    return jsonify({
        'calls': active_calls,
        'count': len(active_calls)
    })

@app.route("/api/call/<call_sid>/response")
@require_key
def get_response(call_sid):
    """Get caller's speech response"""
    if call_sid not in active_calls:
        return jsonify({'error': 'Call not found'}), 404
    
    return jsonify({
        'call_sid': call_sid,
        'response': active_calls[call_sid].get('last_response'),
        'timestamp': active_calls[call_sid].get('last_response_time')
    })

@app.route("/api/end", methods=['POST'])
@require_key
def end_call():
    """Hang up a call"""
    data = request.get_json()
    call_sid = data.get('call_sid')
    
    if not call_sid:
        return jsonify({'error': 'Missing call_sid'}), 400
    
    try:
        client.calls(call_sid).update(status='completed')
        
        if call_sid in active_calls:
            active_calls[call_sid]['status'] = 'ended'
        
        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'status': 'ended'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/status_callback", methods=['POST'])
def status_callback():
    """Handle Twilio status callbacks"""
    call_sid = request.form.get('CallSid')
    status = request.form.get('CallStatus')
    
    print(f"Call {call_sid}: {status}")
    
    if call_sid in active_calls:
        active_calls[call_sid]['status'] = status
        
        if status in ['completed', 'busy', 'failed', 'no-answer']:
            active_calls[call_sid]['ended'] = time.time()
    
    return '', 200

@app.route("/voice", methods=['POST'])
def voice_webhook():
    """Twilio voice webhook - handles incoming calls"""
    response = VoiceResponse()
    response.say("Hello! This is OpenClaw voice bridge. How can I help?", voice='Polly.Matthew')
    
    gather = Gather(action=request.url_root + 'api/gather', timeout=5, speechTimeout='auto')
    gather.say("Please speak now.", voice='Polly.Matthew')
    response.append(gather)
    
    return str(response)

if __name__ == '__main__':
    print("Starting OpenClaw Voice Bridge on port 5001...")
    print("\nTo use from OpenClaw:")
    print(f"  curl -H 'X-Voice-Key: {API_KEY}' http://YOUR_URL/api/status")
    print("\n")
    app.run(host='0.0.0.0', port=5001)
