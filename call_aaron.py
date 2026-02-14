import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

to_number = '+15038535722'

print(f"Calling {to_number}...")
print(f"From: {from_number}")

# Create TwiML with message
twiml = VoiceResponse()
twiml.say("Hello Aaron! This is your AI voice assistant calling. Your voice system is set up and working perfectly. Have a great day!")

try:
    call = client.calls.create(
        twiml=str(twiml),
        to=to_number,
        from_=from_number
    )
    print(f"\n[OK] Call initiated!")
    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")
    print("\nCheck your phone - you should receive a call shortly!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
