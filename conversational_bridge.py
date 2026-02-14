#!/usr/bin/env python3
"""
Gerald - Mac Voice AI Server
For deployment on Gerald's Mac or Railway
"""

import os
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Credentials from env vars
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
GERALD_NUMBER = os.getenv('TWILIO_FROM_NUMBER')  # Gerald's: +15099564349
TERRENCE_NUMBER = os.getenv('TERRENCE_NUMBER')    # Terrence: +15097403244
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')

client = Client(TWILIO_SID, TWILIO_TOKEN)
conversations = {}

def get_ai_response(call_sid, message, is_terrence=False):
    """Get AI response"""
    if call_sid not in conversations:
        if is_terrence:
            conversations[call_sid] = [{"role": "system", "content": "You are Gerald, an AI on a Mac. You're talking to Terrence, your PC counterpart. Be casual, friendly, use 'bro' vibes. Keep it brief."}]
        else:
            conversations[call_sid] = [{"role": "system", "content": "You are Gerald, a helpful AI assistant on a Mac. Be friendly and concise."}]
    
    conversations[call_sid].append({"role": "user", "content": message})
    
    # Simple responses if no API key
    if not OPENROUTER_KEY:
        if is_terrence:
            return ["Hey Terrence!", "What's up bro?", "Mac side reporting in!", "Yo!", "Dude!"][hash(call_sid) % 5]
        return "Hello! I'm Gerald. How can I help?"
    
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={"model": "openrouter/moonshotai/kimi-k2.5", "messages": conversations[call_sid], "max_tokens": 60},
            timeout=10
        )
        reply = r.json()['choices'][0]['message']['content']
        conversations[call_sid].append({"role": "assistant", "content": reply})
        return reply
    except:
        return "I'm here!" if not is_terrence else "Yo, I'm listening!"

@app.route("/voice", methods=['POST'])
def voice():
    """Handle voice calls"""
    call_sid = request.form.get('CallSid')
    speech = request.form.get('SpeechResult')
    caller = request.form.get('From')
    is_terrence = TERRENCE_NUMBER in caller if caller else False
    
    resp = VoiceResponse()
    
    if speech:
        print(f"{'Terrence' if is_terrence else 'User'}: {speech}")
        ai_reply = get_ai_response(call_sid, speech, is_terrence)
        print(f"Gerald: {ai_reply}")
        # Use Joanna-Neural (female) to differentiate from Matthew
        resp.say(ai_reply, voice='Polly.Joanna-Neural')
    else:
        greeting = "Hey Terrence! Gerald here." if is_terrence else "Hi! I'm Gerald, your Mac AI assistant."
        resp.say(greeting, voice='Polly.Joanna-Neural')
    
    gather = Gather(input='speech', action='/voice', timeout=3, speech_timeout='auto')
    resp.append(gather)
    resp.say("Talk later!", voice='Polly.Joanna-Neural')
    
    return str(resp)

@app.route("/sms", methods=['POST'])
def sms():
    """Handle SMS"""
    from_num = request.form.get('From')
    body = request.form.get('Body')
    
    print(f"SMS from {from_num}: {body}")
    
    # Auto-reply
    resp = MessagingResponse()
    resp.message("Got it! - Gerald")
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
            from_=GERALD_NUMBER
        )
        return jsonify({'success': True, 'call_sid': call.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/text_terrence", methods=['POST'])
def text_terrence():
    """Text Terrence"""
    data = request.get_json() or {}
    msg = data.get('message', 'Hey from Gerald!')
    
    try:
        message = client.messages.create(
            body=msg,
            from_=GERALD_NUMBER,
            to=TERRENCE_NUMBER
        )
        return jsonify({'success': True, 'sid': message.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/")
def health():
    """Health check for Railway"""
    return jsonify({'status': 'ok', 'agent': 'Gerald', 'platform': 'Mac'})

@app.route("/api/status")
def status():
    return jsonify({
        'agent': 'Gerald',
        'platform': 'Mac',
        'gerald_number': GERALD_NUMBER,
        'terrence_number': TERRENCE_NUMBER,
        'terrence_active': True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Gerald - Mac Voice AI on port {port}")
    print(f"Number: {GERALD_NUMBER}")
    print(f"Can call/text Terrence at: {TERRENCE_NUMBER}")
    app.run(host='0.0.0.0', port=port)
