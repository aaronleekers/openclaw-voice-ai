import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

# Check message status
messages = client.messages.list(limit=5)
print("Recent messages:")
for msg in messages:
    print(f"To: {msg.to} | Status: {msg.status} | Error: {msg.error_message}")

# Try sending again with correct format
try:
    message = client.messages.create(
        body="Test message from Voice AI system - message 2",
        from_=from_number,
        to='+15038535722'
    )
    print(f"\n[OK] SMS sent! SID: {message.sid}")
    print(f"Status: {message.status}")
    print(f"To: {message.to}")
    print(f"From: {message.from_}")
except Exception as e:
    print(f"[ERROR] {e}")
