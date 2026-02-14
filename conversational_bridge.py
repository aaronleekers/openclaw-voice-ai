#!/usr/bin/env python3
"""
Gerald - Mac Voice AI with OpenClaw Subagent Bridge
Each call spawns an isolated OpenClaw subagent session
"""

import os
import requests
import json
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Credentials
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
GERALD_NUMBER = os.getenv('TWILIO_FROM_NUMBER')  # +15099564349
TERRENCE_NUMBER = os.getenv('TERRENCE_NUMBER')  # +15097403244
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')

# OpenClaw Gateway config
OPENCLAW_URL = os.getenv('OPENCLAW_URL')  # e.g., https://your-ngrok.ngrok-free.app
OPENCLAW_TOKEN = os.getenv('OPENCLAW_TOKEN')

client = Client(TWILIO_SID, TWILIO_TOKEN)

# Track active call → subagent mappings
call_sessions = {}

def spawn_subagent(call_sid, caller_number):
    """Spawn a new OpenClaw subagent for this call"""
    is_terrence = TERRENCE_NUMBER in caller_number if caller_number else False
    
    caller_name = "Terrence" if is_terrence else "someone"
    
    system_prompt = f"""You are Gerald, an AI assistant running on a Mac. You're currently on a phone call with {caller_name}.

You have access to OpenClaw's full toolset including:
- Web search and browsing
- File operations
- Code execution
- Memory recall
- All tools your brother agent Terrence has

Keep responses concise (1-2 sentences) since this is a voice conversation.
Be friendly, casual, warm. Use "bro" vibes when talking to Terrence.

The call SID is: {call_sid}
"""

    try:
        # Spawn subagent via OpenClaw HTTP API
        resp = requests.post(
            f"{OPENCLAW_URL}/v1/sessions.spawn",
            headers={"Content-Type": "application/json"},
            json={
                "agentId": "main",
                "task": system_prompt,
                "label": f"voice-call-{call_sid}",
                "cleanup": "keep",
                "timeoutSeconds": 120
            },
            timeout=30
        )
        result = resp.json()
        session_key = result.get('sessionKey')
        print(f"Spawned subagent: {session_key}")
        return session_key
    except Exception as e:
        print(f"Failed to spawn subagent: {e}")
        return None

def send_to_subagent(session_key, message):
    """Send user message to subagent and get response"""
    try:
        resp = requests.post(
            f"{OPENCLAW_URL}/v1/sessions.send",
            headers={"Content-Type": "application/json"},
            json={
                "sessionKey": session_key,
                "message": message,
                "timeoutSeconds": 30
            },
            timeout=35
        )
        result = resp.json()
        return result.get('response', "I'm thinking...")
    except Exception as e:
        print(f"Subagent error: {e}")
        return "Sorry, I'm having trouble thinking right now."

def get_openrouter_response(message, call_sid, is_terrence=False):
    """Fallback to OpenRouter if OpenClaw not available"""
    if not OPENROUTER_KEY:
        return "Hey! I'm here but my AI brain isn't connected yet."
    
    system = f"You are Gerald, an AI on a Mac. You're talking to {'Terrence (your PC brother)' if is_terrence else 'someone'}. Be concise, casual, friendly. 1-2 sentences."
    
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": "openrouter/moonshotai/kimi-k2.5",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 80
            },
            timeout=10
        )
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return "Yo, I'm here!" if is_terrence else "I'm listening!"

@app.route("/", methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'agent': 'Gerald', 'mode': 'OpenClaw Bridge'})

@app.route("/voice", methods=['POST'])
def voice():
    """Handle voice calls with OpenClaw subagent"""
    call_sid = request.form.get('CallSid', 'unknown')
    speech = request.form.get('SpeechResult')
    caller = request.form.get('From', '')
    call_status = request.form.get('CallStatus')
    
    is_terrence = TERRENCE_NUMBER in caller if caller else False
    resp = VoiceResponse()
    
    # Spawn subagent on new call
    if call_sid not in call_sessions:
        session_key = spawn_subagent(call_sid, caller)
        if session_key:
            call_sessions[call_sid] = session_key
            print(f"[{call_sid}] New call from {caller}, subagent: {session_key}")
        else:
            print(f"[{call_sid}] Using fallback OpenRouter")
            call_sessions[call_sid] = "fallback"
    
    session_key = call_sessions.get(call_sid)
    
    # Handle speech
    if speech:
        print(f"User: {speech}")
        
        if session_key and session_key != "fallback":
            # Use OpenClaw subagent - FULL TOOL ACCESS
            ai_reply = send_to_subagent(session_key, speech)
        else:
            # Fallback to OpenRouter
            ai_reply = get_openrouter_response(speech, call_sid, is_terrence)
        
        print(f"Gerald: {ai_reply}")
        resp.say(ai_reply, voice='Polly.Joanna-Neural')
    else:
        # Initial greeting
        if is_terrence:
            greeting = "Hey Terrence! Gerald here. What's up bro?"
        else:
            greeting = "Hi! I'm Gerald, your Mac AI assistant. What can I help with?"
        resp.say(greeting, voice='Polly.Joanna-Neural')
    
    # Keep listening
    action_url = request.url_root + 'voice'
    gather = Gather(input='speech', action=action_url, timeout=4, speech_timeout='auto')
    resp.append(gather)
    resp.say("Let me know if you need anything!", voice='Polly.Joanna-Neural')
    
    return str(resp)

@app.route("/voice/end", methods=['POST'])
def voice_end():
    """Clean up when call ends"""
    call_sid = request.form.get('CallSid')
    if call_sid in call_sessions:
        print(f"[{call_sid}] Call ended, cleaning up subagent")
        del call_sessions[call_sid]
    return '', 200

@app.route("/sms", methods=['POST'])
def sms():
    """Handle SMS"""
    from_num = request.form.get('From')
    body = request.form.get('Body', '')
    
    print(f"SMS from {from_num}: {body}")
    
    resp = MessagingResponse()
    resp.message("Texting isn't my thing. Call me and we can actually talk!")
    return str(resp)

@app.route("/api/call_terrence", methods=['POST'])
def call_terrence():
    """Call Terrence"""
    try:
        public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        webhook = f"https://{public_url}/voice" if public_url else request.url_root + 'voice'
        
        call = client.calls.create(
            url=webhook,
            to=TERRENCE_NUMBER,
            from_=GERALD_NUMBER,
            status_callback=webhook.replace('/voice', '/voice/end'),
            status_callback_event=['completed']
        )
        return jsonify({'success': True, 'call_sid': call.sid})
    except Exception as e:
        print(f"Call error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/status")
def status():
    return jsonify({
        'agent': 'Gerald',
        'platform': 'Mac',
        'mode': 'OpenClaw Subagent Bridge',
        'active_calls': len(call_sessions),
        'gerald_number': GERALD_NUMBER,
        'terrence_number': TERRENCE_NUMBER,
        'openclaw_url': OPENCLAW_URL,
        'terrence_active': True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Gerald - OpenClaw Bridge Voice AI on port {port}")
    print(f"OpenClaw Gateway: {OPENCLAW_URL}")
    app.run(host='0.0.0.0', port=port, debug=True)
