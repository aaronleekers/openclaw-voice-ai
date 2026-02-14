import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

# Text the user
message = client.messages.create(
    body="🎙️ Hey! This is your AI Voice system testing SMS. Your Twilio + Voice AI setup is working! Call me at (509) 740-3244",
    from_=from_number,
    to='+15038535722'
)

print(f"[OK] SMS sent! SID: {message.sid}")
print(f"Status: {message.status}")
