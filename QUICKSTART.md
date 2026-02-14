# OpenClaw Twilio Voice Bridge

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install flask twilio pyngrok requests
```

### 2. Run the Bridge
```bash
cd voice-ai
python twilio_bridge.py
```

You'll see output like:
```
============================================================
OpenClaw Twilio Bridge
============================================================
Public URL: https://abc123.ngrok-free.app
Set Twilio webhook to: https://abc123.ngrok-free.app/voice
============================================================
Twilio Number: +15097403244
API Key: openclaw-secret-123
============================================================
```

### 3. Configure Twilio Webhook
1. Go to https://console.twilio.com
2. Click your number: `(509) 740-3244`
3. Under **"A CALL COMES IN"**:
   - Select: **Webhook**
   - URL: `https://YOUR_NGROK_URL/voice`
   - Method: **POST**
4. Click **Save**

### 4. Test Incoming Calls
Call **(509) 740-3244** - you'll hear:
> "Hello! You've reached the OpenClaw voice service. How can I help you?"

### 5. Use from OpenClaw

```python
# In OpenClaw or Python:
import requests

API_URL = "https://abc123.ngrok-free.app"
API_KEY = "openclaw-secret-123"
headers = {"X-API-Key": API_KEY}

# Check status
r = requests.get(f"{API_URL}/api/status", headers=headers)
print(r.json())

# Make outbound call
r = requests.post(f"{API_URL}/api/call", headers=headers, json={
    "to": "+15551234567",
    "message": "Hello from OpenClaw!",
    "voice": "Polly.Matthew"
})
print(r.json())

# List calls
r = requests.get(f"{API_URL}/api/calls", headers=headers)
print(r.json())
```

---

## API Reference

### `GET /api/status`
Check service status.

### `POST /api/call`
Make outbound call.
```json
{
  "to": "+15551234567",
  "message": "Hello!",
  "voice": "Polly.Matthew",
  "gather": true
}
```

### `POST /api/speak`
Send TTS to active call.
```json
{
  "call_sid": "CAxxxxx",
  "message": "Follow up message",
  "voice": "Polly.Matthew"
}
```

### `POST /api/end`
Hang up call.
```json
{
  "call_sid": "CAxxxxx"
}
```

### `GET /api/calls`
List recent calls.

### `GET /api/call/<sid>`
Get specific call details.

---

## Voice Options

| Voice | Description |
|-------|-------------|
| `Polly.Matthew` | Male, professional |
| `Polly.Joanna` | Female, professional |
| `Polly.Kimberly` | Female, friendly |
| `Polly.Salli` | Female, calm |
| `Polly.Joey` | Male, casual |

---

## OpenClaw Integration

Save this as `~/.openclaw/skills/voice.py`:

```python
import requests
import os

BRIDGE_URL = os.getenv('VOICE_BRIDGE_URL', 'http://localhost:5001')
API_KEY = os.getenv('VOICE_API_KEY', 'openclaw-secret-123')

def voice_status():
    """Check voice service status"""
    r = requests.get(f"{BRIDGE_URL}/api/status", headers={'X-API-Key': API_KEY})
    return r.json()

def voice_call(phone, message, voice='Polly.Matthew'):
    """Make phone call"""
    r = requests.post(
        f"{BRIDGE_URL}/api/call",
        headers={'X-API-Key': API_KEY, 'Content-Type': 'application/json'},
        json={'to': phone, 'message': message, 'voice': voice}
    )
    return r.json()

def voice_list():
    """List recent calls"""
    r = requests.get(f"{BRIDGE_URL}/api/calls", headers={'X-API-Key': API_KEY})
    return r.json()
```

Then use in OpenClaw:
```
/voice_status
/voice_call +15551234567 "Hello from OpenClaw"
/voice_list
```

---

## Troubleshooting

**ngrok not working?**
```bash
# Sign up at ngrok.com for free
ngrok config add-authtoken YOUR_TOKEN
python twilio_bridge.py
```

**Port already in use?**
Change port in `twilio_bridge.py`:
```python
app.run(host='0.0.0.0', port=5002)  # Use different port
```

**Want to run without ngrok?**
Use Cloudflare Tunnel, localtunnel, or deploy to a server.

---

## Next: PersonaPlex

When you're ready to upgrade from Twilio voices to AI voices:

1. Deploy PersonaPlex on RunPod (see earlier docs)
2. Bridge will route calls to PersonaPlex for AI responses
3. Keep the same API - just swap voice engine
