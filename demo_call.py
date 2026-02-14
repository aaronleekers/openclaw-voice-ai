#!/usr/bin/env python3
"""
Demo: Make a Twilio call with AI voice
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Initialize
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

print("🎙️  Twilio AI Voice Caller")
print("="*60)

def make_ai_call(to_number, message, emotion='default'):
    """Make a call with AI-generated voice"""
    
    # Map emotions to Twilio voices
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
    
    # Build TwiML
    from twilio.twiml.voice_response import VoiceResponse
    twiml = VoiceResponse()
    twiml.say(message, voice=voice)
    
    # Make call
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=from_number
    )
    
    return call.sid

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python demo_call.py <phone_number> <message> [emotion]")
        print("\nExample:")
        print('  python demo_call.py +15038535722 "Hello! This is your AI assistant!" excited')
        print("\nEmotions:")
        print("  default, excited, cheerful, friendly, calm")
        print("  professional, serious, sad, whisper, narrator")
        sys.exit(1)
    
    to_number = sys.argv[1]
    message = sys.argv[2]
    emotion = sys.argv[3] if len(sys.argv) > 3 else 'default'
    
    print(f"\n📞 Calling: {to_number}")
    print(f"🎭 Emotion: {emotion}")
    print(f"💬 Message: {message}")
    print()
    
    try:
        call_sid = make_ai_call(to_number, message, emotion)
        print(f"✅ Call sent!")
        print(f"📋 Call SID: {call_sid}")
        print(f"\n📱 Check your phone!")
    except Exception as e:
        print(f"❌ Error: {e}")

# Quick test function
def test_call():
    """Quick test call to your number"""
    return make_ai_call(
        '+15038535722',
        'Hello Aaron! This is a test of your AI voice system. It is working perfectly!',
        'excited'
    )
