import os
import sys
import subprocess
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say
from dotenv import load_dotenv

load_dotenv()

# Initialize Twilio
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

def generate_voice(text, emotion='default'):
    """Generate voice audio using Edge-TTS"""
    voices = {
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
    
    voice = voices.get(emotion, voices['default'])
    output_file = f"call_audio_{emotion}.mp3"
    
    cmd = ['edge-tts', '--voice', voice, '--text', text, '--write-media', output_file]
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr.decode()}")
        return None
    
    return output_file

def make_call_with_ai_voice(to_number, text, emotion='default'):
    """Make a call with AI-generated voice using Twilio's built-in voices"""
    
    # Map emotions to Twilio voices
    voice_mapping = {
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
    
    voice = voice_mapping.get(emotion, 'Polly.Matthew')
    
    # Create TwiML
    twiml = VoiceResponse()
    twiml.say(text, voice=voice)
    
    # Make call
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=from_number
    )
    
    return call.sid

def make_simple_call(to_number, message):
    """Make a simple call with text-to-speech"""
    print(f"Calling {to_number}...")
    print(f"Message: {message}")
    
    call_sid = make_call_with_ai_voice(to_number, message)
    
    print(f"\n[OK] Call initiated!")
    print(f"Call SID: {call_sid}")
    print(f"Check your phone!")
    
    return call_sid

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python make_call.py <phone_number> <message> [emotion]")
        print("Example: python make_call.py +12025551234 'Hello! This is your AI assistant.' friendly")
        print("\nEmotions: default, excited, cheerful, friendly, calm, professional, serious, sad, whisper, narrator")
        sys.exit(1)
    
    to_number = sys.argv[1]
    message = sys.argv[2]
    emotion = sys.argv[3] if len(sys.argv) > 3 else 'default'
    
    make_simple_call(to_number, message, emotion)
