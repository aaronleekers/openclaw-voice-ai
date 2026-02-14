import os
import uuid
import subprocess
from flask import Flask, request, send_file, jsonify
from twilio.twiml.voice_response import VoiceResponse, Play, Gather, Say
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Twilio client (for outbound calls)
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# Voice mapping
VOICES = {
    'default': 'en-US-GuyNeural',
    'excited': 'en-US-GuyNeural',
    'cheerful': 'en-US-AnaNeural',
    'friendly': 'en-US-AnaNeural',
    'calm': 'en-US-JennyNeural',
    'professional': 'en-US-SteffanNeural',
    'serious': 'en-US-SteffanNeural',
    'sad': 'en-GB-RyanNeural',
    'whisper': 'en-US-JennyNeural',
    'narrator': 'en-GB-SoniaNeural'
}

def generate_speech(text, emotion='default'):
    """Generate AI voice audio"""
    voice = VOICES.get(emotion, VOICES['default'])
    filename = f"audio_{uuid.uuid4()}.mp3"
    
    cmd = ['edge-tts', '--voice', voice, '--text', text, '--write-media', filename]
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        return filename
    return None

@app.route("/voice/answer", methods=['POST'])
def answer_call():
    """Handle incoming calls with AI voice"""
    response = VoiceResponse()
    
    # Generate greeting
    greeting = "Hello! You've reached the AI assistant. How can I help you today?"
    audio_file = generate_speech(greeting, 'friendly')
    
    if audio_file:
        # For production, you'd host this file publicly
        # For now, use Twilio's built-in with similar voice
        response.say(greeting, voice='Polly.Matthew')
    else:
        response.say(greeting, voice='Polly.Matthew')
    
    # Gather speech input
    gather = Gather(
        input='speech',
        action='/voice/respond',
        language='en-US',
        speech_timeout='auto'
    )
    gather.say("Please tell me what you need after the beep.", voice='Polly.Matthew')
    response.append(gather)
    
    # If no input, repeat
    response.redirect('/voice/answer')
    
    return str(response)

@app.route("/voice/respond", methods=['POST'])
def respond_to_speech():
    """Process speech input and respond with AI"""
    response = VoiceResponse()
    
    # Get what the user said
    speech_result = request.form.get('SpeechResult', '')
    
    if speech_result:
        # Here you could use a real AI to generate response
        # For now, echo back with confirmation
        ai_response = f"You said: {speech_result}. I'm processing your request."
        
        # Generate AI voice (or use Twilio's built-in)
        response.say(ai_response, voice='Polly.Matthew')
        
        # Continue conversation
        gather = Gather(
            input='speech',
            action='/voice/respond',
            language='en-US',
            speech_timeout='auto'
        )
        gather.say("Anything else?", voice='Polly.Matthew')
        response.append(gather)
    else:
        response.say("I didn't catch that. Could you please repeat?", voice='Polly.Matthew')
        response.redirect('/voice/answer')
    
    return str(response)

@app.route("/voice/outbound", methods=['POST'])
def make_outbound_call():
    """Make outbound call with AI voice"""
    data = request.get_json()
    to_number = data.get('to')
    message = data.get('message', 'Hello! This is your AI assistant calling.')
    emotion = data.get('emotion', 'default')
    
    if not to_number:
        return jsonify({'error': 'No phone number provided'}), 400
    
    # For outbound, we need to generate audio and host it
    # Or use Twilio's say with similar voice
    
    # Create TwiML
    twiml = VoiceResponse()
    
    # Map emotion to Twilio voice
    voice_map = {
        'default': 'Polly.Matthew',
        'excited': 'Polly.Joanna',
        'cheerful': 'Polly.Kendra',
        'friendly': 'Polly.Kimberly',
        'calm': 'Polly.Salli',
        'professional': 'Polly.Joey',
        'serious': 'Polly.Justin',
        'sad': 'Polly.Emma',
        'whisper': 'Polly.Ivy',
        'narrator': 'Polly.Brian'
    }
    
    voice = voice_map.get(emotion, 'Polly.Matthew')
    twiml.say(message, voice=voice)
    
    # Make call
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=FROM_NUMBER
    )
    
    return jsonify({
        'call_sid': call.sid,
        'status': call.status,
        'message': message
    })

@app.route("/voice/webhook", methods=['POST'])
def voice_webhook():
    """Generic webhook for voice calls"""
    response = VoiceResponse()
    
    # Get call info
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"Call from {from_number} to {to_number} (SID: {call_sid})")
    
    # AI greeting
    response.say(
        "Hello! I'm your AI voice assistant. I can speak in different emotions and styles. Try asking me something!",
        voice='Polly.Matthew'
    )
    
    # Gather input
    gather = Gather(
        input='speech dtmf',
        action='/voice/handle-input',
        timeout=5,
        speech_timeout='auto'
    )
    gather.say("Press 1 for professional mode, 2 for casual mode, or just speak.", voice='Polly.Matthew')
    response.append(gather)
    
    return str(response)

@app.route("/voice/handle-input", methods=['POST'])
def handle_input():
    """Handle user input (speech or DTMF)"""
    response = VoiceResponse()
    
    digits = request.form.get('Digits')
    speech = request.form.get('SpeechResult')
    
    if digits == '1':
        response.say("Switching to professional mode.", voice='Polly.Joey')
        response.say("Good afternoon. How may I assist you professionally today?", voice='Polly.Joey')
    elif digits == '2':
        response.say("Switching to casual mode, dude!", voice='Polly.Matthew')
    elif speech:
        response.say(f"You said: {speech}. That's interesting!", voice='Polly.Matthew')
    else:
        response.say("I didn't understand. Let me try again.", voice='Polly.Matthew')
        response.redirect('/voice/webhook')
    
    # Continue gathering
    gather = Gather(input='speech', action='/voice/handle-input', timeout=5)
    gather.say("What else?", voice='Polly.Matthew')
    response.append(gather)
    
    return str(response)

@app.route("/status", methods=['POST'])
def status_callback():
    """Track call status"""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"Call {call_sid} status: {call_status}")
    
    return '', 200

if __name__ == '__main__':
    print("Twilio Voice AI Server")
    print(f"Number: {FROM_NUMBER}")
    print("Webhook URL: https://your-domain.com/voice/webhook")
    print("="*60)
    
    # For production, use proper WSGI server
    app.run(host='0.0.0.0', port=5001, debug=False)
