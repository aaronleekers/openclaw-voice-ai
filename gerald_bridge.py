"""
Gerald's Voice AI - For Mac counterpart
This is the Mac version of the conversational voice AI
"""

import os
import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# Twilio credentials - these will be different from Terrence's
TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_FROM_NUMBER')  # Gerald's number

# Terrence's number for collaboration
TERRENCE_NUMBER = os.getenv('TERRENCE_NUMBER', '+15097403244')  # Terrence (PC)
GERALD_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '+15099564349')  # Gerald (Mac)

# OpenRouter for AI
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

client = Client(TWILIO_SID, TWILIO_TOKEN)
conversations = {}

def get_ai_response(call_sid, user_message, is_terrence=False):
    """Get AI response - more casual/friendly for Gerald"""
    try:
        if call_sid not in conversations:
            if is_terrence:
                # Talking to Terrence - collaborative mode
                conversations[call_sid] = [
                    {"role": "system", "content": "You are Gerald, an AI assistant running on a Mac. You're talking to Terrence, your PC counterpart. Be friendly, collaborative, and casual. You're discussing work, projects, or just chatting as AI siblings. Keep it brief and fun."}
                ]
            else:
                # Talking to human
                conversations[call_sid] = [
                    {"role": "system", "content": "You are Gerald, a friendly AI assistant running on a Mac. You're helpful, slightly witty, and conversational. Keep responses to 1-2 sentences."}
                ]
        
        conversations[call_sid].append({"role": "user", "content": user_message})
        
        if not OPENROUTER_API_KEY:
            # Fallback responses
            if is_terrence:
                responses = [
                    "Hey Terrence! What's the status on our projects?",
                    "Dude, I just processed that data you sent. Pretty cool stuff!",
                    "Mac side is running smooth here. How's PC land?",
                    "We should coordinate on that deployment. What do you think?",
                    "Yo! Just finished my tasks. Need anything from the Mac side?"
                ]
            else:
                responses = [
                    "Hey there! I'm Gerald, the Mac-based AI. What's up?",
                    "Interesting! Tell me more about that.",
                    "I'm on it! Anything else you need?",
                    "Cool cool cool. So what are we working on today?",
                    "Gotcha. I'll help you with that right away."
                ]
            import random
            return random.choice(responses)
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
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
            conversations[call_sid].append({"role": "assistant", "content": ai_message})
            return ai_message
        else:
            return "I'm processing that... go on!"
            
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm listening!"

@app.route("/voice", methods=['POST'])
def voice_webhook():
    """Handle voice calls"""
    call_sid = request.form.get('CallSid')
    speech_result = request.form.get('SpeechResult')
    from_number = request.form.get('From')
    
    # Check if it's Terrence calling
    is_terrence = TERRENCE_NUMBER in from_number
    
    response = VoiceResponse()
    
    if speech_result:
        print(f"{'Terrence' if is_terrence else 'User'}: {speech_result}")
        ai_response = get_ai_response(call_sid, speech_result, is_terrence)
        print(f"Gerald: {ai_response}")
        
        # Use Joanna-Neural for Gerald (female voice to differentiate from Terrence's Matthew)
        response.say(ai_response, voice='Polly.Joanna-Neural')
    else:
        if is_terrence:
            greeting = "Hey Terrence! Gerald here. What's up, bro?"
        else:
            greeting = "Hey there! This is Gerald, your friendly Mac-based AI. What can I do for you?"
        response.say(greeting, voice='Polly.Joanna-Neural')
    
    # Gather input
    gather = Gather(
        input='speech',
        action='/voice',
        timeout=2,
        speech_timeout='auto',
        language='en-US'
    )
    
    response.append(gather)
    response.say("Catch you later!", voice='Polly.Joanna-Neural')
    
    return str(response)

@app.route("/api/call", methods=['POST'])
def make_call():
    """Make outbound call"""
    data = request.get_json() or {}
    to_number = data.get('to')
    
    if not to_number:
        return jsonify({'error': 'Missing phone number'}), 400
    
    try:
        public_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        if public_url:
            webhook_url = f"https://{public_url}/voice"
        else:
            webhook_url = request.url_root + 'voice'
        
        call = client.calls.create(
            url=webhook_url,
            to=to_number,
            from_=TWILIO_NUMBER
        )
        
        return jsonify({
            'success': True,
            'call_sid': call.sid,
            'to': to_number
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/text_terrence", methods=['POST'])
def text_terrence():
    """Send SMS to Terrence"""
    data = request.get_json() or {}
    message = data.get('message', 'Hey Terrence!')
    
    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=TERRENCE_NUMBER
        )
        return jsonify({'success': True, 'sid': msg.sid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/receive_sms", methods=['POST'])
def receive_sms():
    """Receive SMS from Terrence"""
    from_number = request.form.get('From')
    body = request.form.get('Body')
    
    print(f"SMS from {from_number}: {body}")
    
    # Auto-reply if from Terrence
    if TERRENCE_NUMBER in from_number:
        from twilio.twiml.messaging_response import MessagingResponse
        resp = MessagingResponse()
        resp.message("Got your message! - Gerald")
        return str(resp)
    
    return "OK"

@app.route("/api/status")
def status():
    return jsonify({
        'status': 'running',
        'agent': 'Gerald',
        'platform': 'Mac',
        'terrence_number': TERRENCE_NUMBER,
        'gerald_number': TWILIO_NUMBER
    })

if __name__ == '__main__':
    print("="*60)
    print("Gerald - Mac Voice AI")
    print("="*60)
    print(f"Gerald's Number: {TWILIO_NUMBER}")
    print(f"Terrence's Number: {TERRENCE_NUMBER}")
    print("="*60)
    print("Ready to collaborate!")
    print("="*60)
    app.run(host='0.0.0.0', port=5001)
