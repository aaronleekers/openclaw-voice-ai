"""
Twilio Voice Caller with AI Voices
Usage: python caller.py <phone_number> <message> [emotion]
"""
import os
import sys
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

# Load credentials
load_dotenv()
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# Voice mapping for emotions
VOICES = {
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

def make_call(to_number, message, emotion='default'):
    """Make a call with specified emotion"""
    voice = VOICES.get(emotion, VOICES['default'])
    
    # Build TwiML
    twiml = VoiceResponse()
    twiml.say(message, voice=voice)
    
    # Make call
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=FROM_NUMBER
    )
    
    return call.sid

def main():
    if len(sys.argv) < 3:
        print("Usage: python caller.py <phone_number> <message> [emotion]")
        print("Example: python caller.py +12025551234 'Hello!' excited")
        sys.exit(1)
    
    to_number = sys.argv[1]
    message = sys.argv[2]
    emotion = sys.argv[3] if len(sys.argv) > 3 else 'default'
    
    print(f"Calling {to_number}...")
    print(f"Voice: {emotion}")
    print(f"Message: {message[:50]}...")
    
    try:
        call_sid = make_call(to_number, message, emotion)
        print(f"\n[OK] Call sent! SID: {call_sid}")
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == '__main__':
    main()
