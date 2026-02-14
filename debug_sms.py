import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_FROM_NUMBER')

to_number = '+15038535722'

print(f"From: {from_number}")
print(f"To: {to_number}")
print()

# Check if number is verified
print("Checking verified numbers...")
try:
    outgoing_caller_ids = client.outgoing_caller_ids.list()
    print(f"Verified outgoing numbers: {[n.phone_number for n in outgoing_caller_ids]}")
except Exception as e:
    print(f"Could not check: {e}")

# Try sending
print("\nSending SMS...")
try:
    message = client.messages.create(
        body="Hello from your AI Voice system! This is a test message.",
        from_=from_number,
        to=to_number,
        status_callback='http://requestbin.net/r/1jz8k0y1'  # Optional: track delivery
    )
    print(f"[OK] Message SID: {message.sid}")
    print(f"Status: {message.status}")
    print(f"Direction: {message.direction}")
    
    # Wait a moment and check status
    import time
    time.sleep(2)
    
    updated = client.messages(message.sid).fetch()
    print(f"\nUpdated Status: {updated.status}")
    if updated.error_message:
        print(f"Error: {updated.error_message}")
    if updated.error_code:
        print(f"Error Code: {updated.error_code}")
        
except Exception as e:
    print(f"[ERROR] {e}")
