# Gerald - Mac Voice AI

Gerald's voice AI server for Mac platform.

## Differences from Terrence (PC)
- **Voice**: Joanna (Female) vs Matthew (Male)
- **Personality**: Casual "bro" mode when talking to Terrence
- **Features**: Can call/text Terrence directly
- **Platform**: Mac vs PC

## Environment Variables

- `TWILIO_ACCOUNT_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- `TWILIO_FROM_NUMBER` - Gerald's number: +15099564349
- `TERRENCE_NUMBER` - Terrence's number: +15097403244
- `OPENROUTER_API_KEY` - (Optional) For AI responses

## Deploy

```bash
# This branch uses gerald-server.py (copied to conversational_bridge.py)
gunicorn conversational_bridge:app
```

## API Endpoints

- `POST /voice` - Twilio voice webhook
- `POST /sms` - SMS handler
- `POST /api/call_terrence` - Call Terrence
- `POST /api/text_terrence` - Text Terrence
- `GET /api/status` - Health check
