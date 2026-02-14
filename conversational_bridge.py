#!/usr/bin/env python3
"""
Terrence - PC Voice AI (Simplified MVP)
"""

import os
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# Credentials
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TERRENCE_NUMBER = os.getenv('TWILIO_FROM_NUMBER')  # +15097403244
GERALD_NUMBER = os.getenv('GERALD_NUMBER')  # +15099564349
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')

# For callback feature
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'changeme')

client = Client(TWILIO_SID, TWILIO_TOKEN)
conversations = {}

def get_ai_response(call_sid, message, is_gerald):
    """Get AI response via OpenRouter"""
    if call_sid not in conversations:
        conversations[call_sid] = []
    
    conversations[call_sid].append({"role": "user", "content": message})
    
    if not OPENROUTER_KEY:
        return "Hey! I'm Terrence. My AI brain needs to be connected."
    
    system = f"You are Terrence, an AI on a PC. Talking to {'Gerald (Mac brother)' if is_gerald else 'someone'}. Be concise, slightly sarcastic but helpful. 1-2 sentences max."
    
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
        print(f"Error: {e}")
        return "Yo, I'm here!" if is_gerald else "I'm listening!"

@app.route("/")
def health():
    return jsonify({'status': 'ok', 'agent': 'Terrence'})

@app.route("/voice", methods=['POST'])
def voice():
    """Handle voice calls"""
    call_sid = request.form.get('CallSid', 'unknown')
    speech = request.form.get('SpeechResult')
    caller = request.form.get('From', '')
    
    is_gerald = GERALD_NUMBER in caller if caller else False
    resp = VoiceResponse()
    
    try:
        if speech:
            ai_reply = get_ai_response(call_sid, speech, is_gerald)
            print(f"Terrence: {ai_reply}")
            resp.say(ai_reply, voice='Polly.Matthew-Neural')
        else:
            greeting = "Hey Gerald! Terrence here." if is_gerald else "Hi! I'm Terrence. What can I do for you?"
            resp.say(greeting, voice='Polly.Matthew-Neural')
        
        # Keep listening
        action_url = request.url_root.rstrip('/') + '/voice'
        gather = Gather(input='speech', action=action_url, timeout=5, speech_timeout='auto')
        resp.append(gather)
        resp.say("Talk soon!", voice='Polly.Matthew-Neural')
        
    except Exception as e:
        print(f"Error: {e}")
        resp.say("Sorry, I'm having trouble. Try again!")
    
    return str(resp)

@app.route("/api/call_gerald", methods=['POST'])
def call_gerald():
    """Call Gerald"""
    try:
        public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        webhook = f"https://{public_url}/voice" if public_url else request.url_root.rstrip('/') + '/voice'
        
        call = client.calls.create(
            url=webhook,
            to=GERALD_NUMBER,
            from_=TERRENCE_NUMBER
        )
        return jsonify({'success': True, 'call_sid': call.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/callback", methods=['POST'])
def trigger_callback():
    """OpenClaw can trigger a call back"""
    if request.headers.get('X-Secret') != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json() or {}
    phone = data.get('phone', '')
    if not phone:
        return jsonify({'error': 'Phone required'}), 400
    
    try:
        public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        webhook = f"https://{public_url}/voice" if public_url else request.url_root.rstrip('/') + '/voice'
        
        call = client.calls.create(
            url=webhook,
            to=phone,
            from_=TERRENCE_NUMBER
        )
        return jsonify({'success': True, 'call_sid': call.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/status")
def status():
    return jsonify({
        'agent': 'Terrence',
        'platform': 'PC',
        'number': TERRENCE_NUMBER,
        'gerald_number': GERALD_NUMBER,
        'active_calls': len(conversations)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Terrence on port {port}")
    app.run(host='0.0.0.0', port=port)
