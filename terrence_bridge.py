"""
OpenClaw Conversational Voice AI
Uses ChatGPT for responses and Twilio for voice
"""

import os
import json
import time
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from functools import wraps

# Start ngrok only if not on Railway
public_url = None
if not os.getenv('RAILWAY_ENVIRONMENT'):
    try:
        from pyngrok import ngrok
        tunnel = ngrok.connect(5001, "http")
        public_url = tunnel.public_url
        print(f"\nPublic URL: {public_url}")
        print(f"Webhook: {public_url}/voice\n")
    except Exception as e:
        print(f"ngrok error: {e}")
        public_url = None
else:
    # On Railway, use the provided domain
    public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if public_url:
        public_url = f"https://{public_url}"
        print(f"\nRailway URL: {public_url}")
        print(f"Webhook: {public_url}/voice\n")

app = Flask(__name__)

# Twilio credentials
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID', 'YOUR_TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER', 'YOUR_TWILIO_NUMBER')

# OpenRouter API for AI responses  
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

# Initialize Twilio
client = Client(TWILIO_SID, TWILIO_TOKEN)

# Store conversation history
conversations = {}

def get_ai_response(call_sid, user_message):
    """Get AI response from OpenRouter"""
    try:
        # Initialize conversation history for this call
        if call_sid not in conversations:
            conversations[call_sid] = [
                {"role": "system", "content": "You are OpenClaw, Aaron's friendly AI assistant. Keep responses brief (1-2 sentences), conversational, warm and natural. You're having a phone call with Aaron. Be personable, use casual language, and show personality."}
            ]
        
        # Add user message
        conversations[call_sid].append({"role": "user", "content": user_message})
        
        # If no API key, use simple responses
        if not OPENROUTER_API_KEY:
            responses = [
                "That's really interesting! Tell me more about that.",
                "I see what you mean. What do you think about it?",
                "Hmm, that's a good point. Go on...",
                "Yeah, I feel you on that. What else is on your mind?",
                "Totally! So what are you up to today?"
            ]
            import random
            return random.choice(responses)
        
        # Call OpenRouter API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://openclaw.local",
                "X-Title": "OpenClaw Voice"
            },
            json={
                "model": "openrouter/moonshotai/kimi-k2.5",
                "messages": conversations[call_sid],
                "max_tokens": 80,
                "temperature": 0.8
            },
            timeout=10
        )
        
        if response.status_code == 200:
            ai_message = response.json()['choices'][0]['message']['content']
            # Add AI response to history
            conversations[call_sid].append({"role": "assistant", "content": ai_message})
            return ai_message
        else:
            return "That's interesting! Keep talking..."
            
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm listening... what else?"

@app.route("/voice", methods=['POST'])
def voice_webhook():
    """Handle incoming calls and conversation"""
    call_sid = request.form.get('CallSid')
    speech_result = request.form.get('SpeechResult')
    
    response = VoiceResponse()
    
    if speech_result:
        # User said something - get AI response
        print(f"User: {speech_result}")
        ai_response = get_ai_response(call_sid, speech_result)
        print(f"AI: {ai_response}")
        
        # Use neural voice for more natural sound
        response.say(ai_response, voice='Polly.Matthew-Neural')
    else:
        # Initial greeting or no input
        greeting = "Hey Aaron! This is OpenClaw. I can actually have a real conversation now. What's on your mind?"
        response.say(greeting, voice='Polly.Matthew-Neural')
    
    # Gather next input with better settings
    gather = Gather(
        input='speech',
        action='/voice',
        timeout=2,
        speech_timeout='auto',
        language='en-US',
        hints='yes,no,maybe,hello,hey,what,how,why,when,where,who,goodbye,bye,stop,thanks,thank you'
    )
    
    response.append(gather)
    
    # If no input, end gracefully
    response.say("It was great talking to you! Call me back anytime.", voice='Polly.Matthew-Neural')
    
    return str(response)

@app.route("/api/call", methods=['POST'])
def make_call():
    """Make an outbound call"""
    data = request.get_json() or {}
    to_number = data.get('to')
    
    if not to_number:
        return jsonify({'error': 'Missing phone number'}), 400
    
    try:
        call = client.calls.create(
            url=public_url + '/voice' if public_url else request.url_root + 'voice',
            to=to_number,
            from_=TWILIO_NUMBER
        )
        
        return jsonify({
            'success': True,
            'call_sid': call.sid,
            'to': to_number,
            'status': call.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/end", methods=['POST'])
def end_call():
    """End a call"""
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    
    if call_sid:
        client.calls(call_sid).update(status='completed')
        if call_sid in conversations:
            del conversations[call_sid]
    
    return jsonify({'success': True})

if __name__ == '__main__':
    print("="*60)
    print("OpenClaw Conversational Voice AI")
    print("="*60)
    print(f"Twilio Number: {TWILIO_NUMBER}")
    print("="*60)
    print("Features:")
    print("  - Two-way conversation")
    print("  - AI-powered responses") 
    print("  - Neural voice (natural sounding)")
    print("  - Conversation memory")
    print("="*60)
    app.run(host='0.0.0.0', port=5001)

