# OpenClaw Voice AI

Conversational voice AI using Twilio and OpenRouter.

## Quick Start

```bash
pip install -r requirements.txt
python conversational_bridge.py
```

## Environment Variables

- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `TWILIO_FROM_NUMBER` - Your Twilio phone number
- `OPENROUTER_API_KEY` - (Optional) For AI responses

## Deploy to Railway

```bash
railway login
railway init
railway up
```

## API Endpoints

- `POST /api/call` - Make outbound call
- `POST /voice` - Twilio webhook for voice
- `GET /api/status` - Health check
