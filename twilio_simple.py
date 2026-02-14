"""
Simple Twilio Voice AI Integration
Makes calls using AI-generated voices instead of default Twilio voices
"""
import os
import subprocess
import uuid
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Play
from flask import Flask, request, send_file
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

app = Flask(__name__)

def generate_ai_voice(text, emotion='default'):
    """Generate AI voice and return URL to audio file"""
    voices = {
        'default': 'en-US-GuyNeural',
        'excited': 'en-US-GuyNeural',
        'friendly': 'en-US-AnaNeural',
        'calm': 'en-US-JennyNeural',
        'professional': 'en-US-SteffanNeural'
    }
    
    voice = voices.get(emotion, voices['default'])
    filename = f"call_{uuid.uuid4()}.mp3"
    
    # Generate with Edge-TTS
    cmd = ['edge-tts', '--voice', voice, '--text', text, '--write-media', f"static/{filename}"]
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        return f"https://your-server.com/static/{filename}"
    return None

@app.route("/call/<phone_number>")
def make_ai_call(phone_number):
    """Make a call with AI voice"""
    
    # Generate AI audio
    message = "Hello! This is your AI assistant calling. How can I help you today?"
    audio_url = generate_ai_voice(message, 'friendly')
    
    # Create TwiML that plays the AI audio
    twiml = VoiceResponse()
    
    if audio_url:
        twiml.play(audio_url)
    else:
        # Fallback to Twilio's built-in voice
        twiml.say(message, voice='Polly.Matthew')
    
    # Make the call
    call = client.calls.create(
        twiml=str(twiml),
        to=f"+{phone_number}",
        from_=FROM_NUMBER
    )
    
    return f"Calling +{phone_number}... Call SID: {call.sid}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
