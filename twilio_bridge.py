"""
Simple Twilio Voice Bridge for OpenClaw
Runs locally - no RunPod needed

Usage:
1. pip install flask twilio pyngrok
2. python twilio_bridge.py
3. Copy the ngrok URL
4. Set Twilio webhook to: https://your-ngrok-url/voice
5. Call (509) 740-3244 to test
"""

import os
import json
import time
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from functools import wraps

# Try tunnels for public URL
try:
    from pyngrok import ngrok
    USE_NGROK = True
    USE_CLOUDFLARE = False
except ImportError:
    USE_NGROK = False
    USE_CLOUDFLARE = False

# Check for cloudflared
def check_cloudflare():
    import subprocess
    try:
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        return True
    except:
        return False

app = Flask(__name__)

# Twilio credentials
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID', 'YOUR_TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '+15097403244')

# Simple API key
API_KEY = os.getenv('OPENCLAW_API_KEY', 'openclaw-secret-123')

# Init Twilio
client = Client(TWILIO_SID, TWILIO_TOKEN)

# Track calls
calls_db = {}

def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def home():
    return jsonify({
        "service": "OpenClaw Twilio Bridge",
        "status": "running",
        "twilio_number": TWILIO_NUMBER,
        "api_key": API_KEY,
        "endpoints": {
            "GET /api/status": "Check status",
            "POST /api/call": "Make outbound call",
            "POST /api/speak": "Send TTS to call",
            "POST /api/end": "Hang up call",
            "GET /api/calls": "List calls",
            "POST /voice": "Twilio webhook (incoming)"
        }
    })

@app.route("/api/status")
@require_key
def status():
    """Get service status"""
    return jsonify({
        "status": "running",
        "twilio": {
            "number": TWILIO_NUMBER,
            "connected": bool(client)
        },
        "active_calls": len([c for c in calls_db.values() if c.get('status') == 'in-progress']),
        "total_calls": len(calls_db)
    })

@app.route("/api/call", methods=['POST'])
@require_key
def make_call():
    """
    Make an outbound call
    
    Body:
    {
        "to": "+1234567890",
        "message": "Hello from OpenClaw!",
        "voice": "Polly.Matthew",
        "gather": true
    }
    """
    data = request.get_json() or {}
    to_number = data.get('to')
    message = data.get('message', 'Hello!')
    voice = data.get('voice', 'Polly.Matthew')
    gather = data.get('gather', False)
    
    if not to_number:
        return jsonify({'error': 'Missing "to" phone number'}), 400
    
    try:
        # Build TwiML
        twiml = VoiceResponse()
        twiml.say(message, voice=voice)
        
        if gather:
            g = Gather(
                input='speech',
                action=request.url_root.rstrip('/') + '/api/gather',
                timeout=5,
                language='en-US'
            )
            g.say("Please respond after the beep.")
            twiml.append(g)
        
        # Make call
        call = client.calls.create(
            twiml=str(twiml),
            to=to_number,
            from_=TWILIO_NUMBER,
            status_callback=request.url_root.rstrip('/') + '/api/callback',
            status_callback_event=['completed', 'answered', 'failed']
        )
        
        # Store call
        calls_db[call.sid] = {
            'sid': call.sid,
            'to': to_number,
            'from': TWILIO_NUMBER,
            'message': message,
            'status': call.status,
            'created': time.time()
        }
        
        return jsonify({
            'success': True,
            'call_sid': call.sid,
            'to': to_number,
            'status': call.status,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/speak", methods=['POST'])
@require_key
def speak():
    """
    Speak to active call
    
    Body:
    {
        "call_sid": "CAxxxxx",
        "message": "Your message here",
        "voice": "Polly.Matthew"
    }
    """
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    message = data.get('message')
    voice = data.get('voice', 'Polly.Matthew')
    
    if not call_sid or not message:
        return jsonify({'error': 'Missing call_sid or message'}), 400
    
    try:
        twiml = VoiceResponse()
        twiml.say(message, voice=voice)
        
        client.calls(call_sid).update(twiml=str(twiml))
        
        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/end", methods=['POST'])
@require_key
def end_call():
    """Hang up a call"""
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    
    if not call_sid:
        return jsonify({'error': 'Missing call_sid'}), 400
    
    try:
        client.calls(call_sid).update(status='completed')
        
        if call_sid in calls_db:
            calls_db[call_sid]['status'] = 'completed'
            calls_db[call_sid]['ended'] = time.time()
        
        return jsonify({'success': True, 'call_sid': call_sid})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/calls")
@require_key
def list_calls():
    """List all calls"""
    # Get recent from Twilio
    try:
        twilio_calls = client.calls.list(limit=20)
        recent = []
        for c in twilio_calls:
            recent.append({
                'sid': c.sid,
                'to': c.to,
                'from_': c.from_,
                'status': c.status,
                'duration': c.duration,
                'date': str(c.date_created)
            })
        return jsonify({'calls': recent, 'count': len(recent)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/call/<call_sid>")
@require_key
def get_call(call_sid):
    """Get specific call details"""
    try:
        call = client.calls(call_sid).fetch()
        return jsonify({
            'sid': call.sid,
            'to': call.to,
            'from': call.from_,
            'status': call.status,
            'duration': call.duration,
            'price': call.price,
            'direction': call.direction
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route("/api/callback", methods=['POST'])
def callback():
    """Handle Twilio status callbacks"""
    call_sid = request.form.get('CallSid')
    status = request.form.get('CallStatus')
    duration = request.form.get('CallDuration')
    
    print(f"[Twilio] Call {call_sid} status: {status}")
    
    if call_sid in calls_db:
        calls_db[call_sid]['status'] = status
        if duration:
            calls_db[call_sid]['duration'] = duration
    
    return '', 200

@app.route("/api/gather", methods=['POST'])
def gather():
    """Handle speech input"""
    call_sid = request.form.get('CallSid')
    speech = request.form.get('SpeechResult', '')
    
    print(f"[Speech] Call {call_sid}: {speech}")
    
    # Store response
    if call_sid in calls_db:
        if 'responses' not in calls_db[call_sid]:
            calls_db[call_sid]['responses'] = []
        calls_db[call_sid]['responses'].append({
            'speech': speech,
            'time': time.time()
        })
    
    # Send to OpenClaw (if configured)
    openclaw_url = os.getenv('OPENCLAW_WEBHOOK_URL')
    if openclaw_url and speech:
        try:
            import requests
            requests.post(openclaw_url, json={
                'type': 'voice_response',
                'call_sid': call_sid,
                'speech': speech,
                'from': request.form.get('From'),
                'timestamp': time.time()
            }, timeout=5)
        except:
            pass  # Don't fail if OpenClaw is down
    
    # Respond
    response = VoiceResponse()
    if speech:
        response.say(f"You said: {speech}", voice='Polly.Matthew')
    else:
        response.say("I didn't hear anything. Goodbye!", voice='Polly.Matthew')
    
    return str(response)

@app.route("/voice", methods=['POST'])
def voice_webhook():
    """Handle incoming calls from Twilio"""
    from_number = request.form.get('From')
    call_sid = request.form.get('CallSid')
    
    print(f"[Incoming] Call from {from_number}")
    
    # Store
    calls_db[call_sid] = {
        'sid': call_sid,
        'from': from_number,
        'to': TWILIO_NUMBER,
        'status': 'in-progress',
        'direction': 'inbound',
        'created': time.time()
    }
    
    # Send to OpenClaw (if configured)
    openclaw_url = os.getenv('OPENCLAW_WEBHOOK_URL')
    if openclaw_url:
        try:
            import requests
            requests.post(openclaw_url, json={
                'type': 'incoming_call',
                'call_sid': call_sid,
                'from': from_number,
                'timestamp': time.time()
            }, timeout=5)
        except:
            pass
    
    # Voice response
    response = VoiceResponse()
    response.say("Hello! You've reached the OpenClaw voice service.", voice='Polly.Matthew')
    
    gather = Gather(
        input='speech',
        action=request.url_root.rstrip('/') + '/api/gather',
        timeout=5,
        language='en-US'
    )
    gather.say("How can I help you?")
    response.append(gather)
    
    return str(response)

if __name__ == '__main__':
    print("="*60)
    print("OpenClaw Twilio Bridge")
    print("="*60)
    
    # Start ngrok if available
    public_url = None
    if USE_NGROK:
        print("Starting ngrok tunnel...")
        try:
            tunnel = ngrok.connect(5001, "http")
            public_url = tunnel.public_url
            print(f"Public URL: {public_url}")
            print(f"Set Twilio webhook to: {public_url}/voice")
        except Exception as e:
            print(f"ngrok failed: {e}")
            print("Install: pip install pyngrok")
            print("Or use your own tunnel (Cloudflare, localtunnel, etc.)")
    else:
        print("Install pyngrok for public URL: pip install pyngrok")
        print(f"Local URL: http://localhost:5001")
    
    print("="*60)
    print(f"Twilio Number: {TWILIO_NUMBER}")
    print(f"API Key: {API_KEY}")
    print("="*60)
    print("\nOpenClaw Endpoints:")
    print("  GET  /api/status")
    print("  POST /api/call")
    print("  POST /api/speak")
    print("  POST /api/end")
    print("  GET  /api/calls")
    print("")
    
    # Save URL to file for OpenClaw
    if public_url:
        with open('twilio_bridge_url.txt', 'w') as f:
            f.write(public_url)
        print(f"URL saved to: twilio_bridge_url.txt")
    
    print("Starting server on port 5001...\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
