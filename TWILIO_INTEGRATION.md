# 🎙️ Twilio + AI Voice Integration

Connect your AI voice system to Twilio phone calls!

---

## 🎯 What This Does

Instead of boring robot voices, your Twilio calls use **AI-generated speech** with:
- 🎭 **10 emotions** (excited, calm, professional, etc.)
- 🗣️ **Natural sounding voices** (not robotic)
- 💬 **Speech-to-text** (listen to callers)
- 🤖 **AI responses** (smart replies)

---

## 📱 Use Cases

1. **AI Phone Assistant**
   - Customer calls your Twilio number
   - AI answers with friendly voice
   - Understands speech, responds intelligently

2. **Outbound AI Calls**
   - Call customers with AI voice
   - Appointment reminders, surveys, sales
   - Sounds like a real person

3. **Voice Bot**
   - Interactive phone menu with AI
   - "Press 1 for sales, or just tell me what you need"

---

## 🚀 Quick Setup

### Step 1: Install Dependencies
```bash
cd /workspace/voice-ai
pip install twilio flask python-dotenv
```

### Step 2: Start the Server
```bash
python twilio_voice_server.py
```

### Step 3: Expose to Internet
Twilio needs a public URL to reach your server. Options:

**Option A: ngrok (easiest)**
```bash
# Install ngrok
# Run:
ngrok http 5001

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option B: RunPod/Vast.ai public IP**
If hosting on cloud GPU, use the provided public URL

### Step 4: Configure Twilio

1. Go to https://console.twilio.com
2. Click your **Phone Number**
3. Under **Voice & Fax**:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-ngrok-url/voice/webhook`
   - **HTTP Method**: POST
4. Click **Save**

---

## 📞 Making Calls

### Test Incoming Call
1. Call your Twilio number: `(509) 740-3244`
2. AI should answer with friendly voice!

### Make Outbound Call
```bash
curl -X POST http://localhost:5001/voice/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+15038535722",
    "message": "Hello! This is your AI assistant calling with exciting news!",
    "emotion": "excited"
  }'
```

Or use Python:
```python
import requests

response = requests.post('http://localhost:5001/voice/outbound', json={
    'to': '+15038535722',
    'message': 'Hey! Your AI voice system is working!',
    'emotion': 'friendly'
})

print(response.json())
```

---

## 🎭 Available Emotions

| Emotion | Voice Style | Best For |
|---------|-------------|----------|
| `default` | Natural male | General use |
| `excited` | Energetic | Sales, announcements |
| `friendly` | Warm | Customer service |
| `professional` | Business | Corporate calls |
| `calm` | Peaceful | Support, therapy |
| `serious` | Stern | Urgent matters |
| `sad` | Melancholy | Condolences |
| `narrator` | Storyteller | Audiobooks |

---

## 🔧 Advanced: Full AI Conversation

To have **real AI conversations**, integrate with your LLM:

```python
@app.route("/voice/ai-chat", methods=['POST'])
def ai_chat():
    response = VoiceResponse()
    
    # Get what user said
    user_speech = request.form.get('SpeechResult', '')
    
    # Send to your AI (OpenAI, Claude, local LLM)
    ai_response = your_ai_model.generate(user_speech)
    
    # Convert to speech with emotion detection
    emotion = detect_emotion(ai_response)  # Your function
    audio_file = generate_speech(ai_response, emotion)
    
    # Play to caller
    response.play(f"https://your-server.com/{audio_file}")
    
    # Keep listening
    gather = Gather(input='speech', action='/voice/ai-chat')
    response.append(gather)
    
    return str(response)
```

---

## 🌐 Public Hosting Options

Since your PC isn't publicly accessible, use:

### 1. ngrok (Testing)
```bash
ngrok http 5001
```
- Free tier: Random URLs, 40 connections/min
- Pro: $5/mo for reserved URLs

### 2. RunPod/Vast.ai (Production)
- Host the voice server on cloud GPU
- Get permanent public URL
- AI voice generation + Twilio in one place

### 3. VPS (Best)
- DigitalOcean, AWS, Linode
- $5-10/mo for small VPS
- Always online, custom domain

---

## 💰 Costs

**Twilio:**
- Incoming calls: ~$0.0085/min
- Outgoing calls: ~$0.013/min
- Phone number: $1/mo

**Voice AI:**
- Free (runs locally on your 5080 Ti)
- Or ~$0.35/hr on cloud GPU

**Total for heavy use:**
- 100 calls/month (5 min each): ~$7
- 1000 calls/month: ~$70

---

## 🚨 Troubleshooting

### "URL not accessible"
- Make sure you're using HTTPS (not HTTP)
- Check ngrok/cloud server is running
- Verify port 5001 is open

### "Voice not playing"
- Audio files must be publicly accessible URLs
- Use .mp3 format (16-bit, 8kHz or 16kHz)
- Check file permissions

### "Speech recognition not working"
- Enable speech in Gather: `input='speech'`
- Check Twilio speech recognition is enabled on your account
- Use supported languages: `language='en-US'`

---

## 🎉 Next Steps

1. **Test it**: Call your Twilio number
2. **Customize**: Change greetings, add more AI logic
3. **Scale**: Deploy to cloud for 24/7 availability
4. **Integrate**: Connect to your actual AI backend

---

**Ready to test?** 
1. Start the server
2. Run ngrok
3. Update Twilio webhook
4. Call your number! 📞

Need help with any step? 🤔
