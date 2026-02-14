#!/usr/bin/env python3
"""
Gerald - Mac Voice AI with OpenClaw HTTP Bridge (Simplified MVP)
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
GERALD_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
TERRENCE_NUMBER = os.getenv('TERRENCE_NUMBER')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')

# OpenClaw config
OPENCLAW_URL = os.getenv('OPENCLAW_URL', '').rstrip('/')  # Remove trailing slash
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'default-secret')

client = Client(TWILIO_SID, TWILIO_TOKEN)

# In-memory conversation storage (use Redis in production)
conversations = {}
active_calls = {}

def get_ai_response(call_sid, message, caller_number):
    """Get AI response - tries OpenClaw first, falls back to OpenRouter"""
    is_terrence = TERRENCE_NUMBER in caller_number if caller_number else False
    
    # Initialize conversation context
    if call_sid not in conversations:
        conversations[call_sid] = []
    
    conversations[call_sid].append({"role": "user", "content": message})
    
    # Try OpenClaw HTTP bridge first
    if OPENCLAW_URL:
        try:
            # Simple HTTP bridge to OpenClaw
            resp = requests.post(
                f"{OPENCLAW_URL}/voice-bridge",
                headers={"X-Webhook-Secret": WEBHOOK_SECRET, "Content-Type": "application/json"},
                json={
                    "agent": "gerald",
                    "call_sid": call_sid,
                    "caller": caller_number,
                    "message": message,
                    "history": conversations[call_sid][-5:]  # Last 5 messages
                },
                timeout=15
            )
            if resp.status_code == 200:
                reply = resp.json().get('response', '...')
                conversations[call_sid].append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            print(f"OpenClaw bridge failed: {e}")
    
    # Fallback to OpenRouter
    if not OPENROUTER_KEY:
        return "Hey! I'm here but need my AI connected."
    
    system = f"You are Gerald, an AI on a Mac. Talking to {'Terrence (PC brother)' if is_terrence else 'someone'}. Be concise, casual, friendly. 1-2 sentences max."
    
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": "openrouter/moonshotai/kimi-k2.5",
                "messages": [{"role": "system", "content": system}] + conversations[call_sid][-5:],
                "max_tokens": 80
            },
            timeout=10
        )
        reply = r.json()['choices'][0]['message']['content']
        conversations[call_sid].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return "Yo, I'm here!" if is_terrence else "I'm listening!"

@app.route("/", methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'agent': 'Gerald', 'mode': 'Secure Bridge'})

@app.route("/voice", methods=['POST'])
def voice():
    """Handle incoming voice calls"""
    call_sid = request.form.get('CallSid', 'unknown')
    speech = request.form.get('SpeechResult')
    caller = request.form.get('From', '')
    
    is_terrence = TERRENCE_NUMBER in caller if caller else False
    
    print(f"[{call_sid}] Call from {caller}, speech: {speech}")
    
    resp = VoiceResponse()
    
    try:
        if speech:
            # User said something - get AI response
            ai_reply = get_ai_response(call_sid, speech, caller)
            print(f"Gerald: {ai_reply}")
            resp.say(ai_reply, voice='Polly.Joanna-Neural')
        else:
            # Initial greeting
            greeting = "Hey Terrence! Gerald here. What's up?" if is_terrence else "Hi! I'm Gerald. How can I help?"
            resp.say(greeting, voice='Polly.Joanna-Neural')
        
        # Continue listening
        action_url = request.url_root.rstrip('/') + '/voice'
        gather = Gather(input='speech', action=action_url, timeout=5, speech_timeout='auto')
        resp.append(gather)
        resp.say("Talk soon!", voice='Polly.Joanna-Neural')
        
    except Exception as e:
        print(f"Voice handler error: {e}")
        resp.say("Sorry, I'm having trouble right now. Call back in a minute!")
    
    return str(resp)

@app.route("/api/callback", methods=['POST'])
def trigger_callback():
    """OpenClaw can call this to make Gerald call the user back"""
    # Verify secret
    if request.headers.get('X-Webhook-Secret') != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    phone = data.get('phone', TERRENCE_NUMBER)
    message = data.get('message', 'Hey! Calling you back with an update.')
    
    try:
        public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        webhook = f"https://{public_url}/voice" if public_url else request.url_root.rstrip('/') + '/voice'
        
        call = client.calls.create(
            url=webhook,
            to=phone,
            from_=GERALD_NUMBER
        )
        
        # Store callback message to be spoken first
        active_calls[call.sid] = {"callback_message": message}
        
        return jsonify({'success': True, 'call_sid': call.sid})
    except Exception as e:
        print(f"Callback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/status")
def status():
    return jsonify({
        'agent': 'Gerald',
        'platform': 'Mac',
        'gerald_number': GERALD_NUMBER,
        'terrence_number': TERRENCE_NUMBER,
        'openclaw_connected': bool(OPENCLAW_URL),
        'active_conversations': len(conversations)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Gerald - Secure Voice Bridge on port {port}")
    print(f"OpenClaw URL: {OPENCLAW_URL or 'Not configured'}")
    app.run(host='0.0.0.0', port=port)
