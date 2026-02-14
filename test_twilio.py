import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_FROM_NUMBER')

print(f"Account SID: {account_sid[:20]}...")
print(f"From Number: {from_number}")

# Initialize client
client = Client(account_sid, auth_token)

# Test: Get account info
try:
    account = client.api.accounts(account_sid).fetch()
    print(f"\n[OK] Account Status: {account.status}")
    print(f"[OK] Account Name: {account.friendly_name}")
    print("\nTwilio is connected and ready!")
    
    # List recent calls
    print("\nRecent Calls:")
    calls = client.calls.list(limit=5)
    for call in calls:
        print(f"  {call.to} - {call.status} - {call.date_created}")
        
except Exception as e:
    print(f"[ERROR] {e}")
