# 🚀 RunPod Deployment Guide

Deploy your Voice AI + Twilio integration to RunPod cloud GPU!

---

## 📋 What You'll Get

✅ **Always-online voice AI server**
✅ **Public URL** (no ngrok needed)
✅ **Twilio webhook endpoint**
✅ **PersonaPlex 7B ready** (when you want it)
✅ **Fast GPU inference** on A40/RTX 3090

---

## 💰 Cost

| GPU | VRAM | Price/hr | Monthly (24/7) |
|-----|------|----------|----------------|
| **RTX 3090** | 24GB | **$0.25** | ~$180 |
| **A40** | 48GB | **$0.35** | ~$252 |
| **A100** | 80GB | **$1.19** | ~$857 |

**Recommended:** A40 for best balance of price/performance

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Files

Upload these files to your RunPod instance:
- `Dockerfile.runpod`
- `runpod_server.py`
- `requirements.txt` (if needed)
- `.env` file with your Twilio credentials

### Step 2: Create RunPod Pod

1. Go to https://runpod.io
2. **Pods** → **Deploy**
3. **Select GPU:** A40 (48GB) or RTX 3090 (24GB)
4. **Image:** `pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime`
5. **Disk:** 50 GB
6. **Container Disk:** 20 GB
7. **Expose Ports:** `5001` (HTTP), `8000` (optional)
8. **Environment Variables:**
   ```
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_FROM_NUMBER=+15097403244
   ```
9. Click **Deploy**

### Step 3: Install & Run

Once pod is running (green status):

```bash
# SSH into pod or use Jupyter terminal

# Clone your code
git clone https://github.com/yourusername/voice-ai.git
cd voice-ai

# Or just create files directly:
# (Paste runpod_server.py content)

# Install dependencies
pip install flask flask-cors twilio python-dotenv edge-tts

# Run server
python runpod_server.py
```

### Step 4: Get Public URL

RunPod provides a public proxy URL:

```
https://[pod-id]-5001.proxy.runpod.net
```

Find it in your pod's **Connect** tab.

### Step 5: Configure Twilio

1. Go to https://console.twilio.com
2. Click your phone number: **+1 (509) 740-3244**
3. **Voice & Fax** section:
   - **A CALL COMES IN:** Webhook
   - **URL:** `https://[pod-id]-5001.proxy.runpod.net/voice/webhook`
   - **HTTP Method:** POST
4. Click **Save**

---

## 🧪 Test It

### Test Incoming Call
1. Call: **(509) 740-3244**
2. AI should answer!

### Test Outbound Call
```bash
curl -X POST https://[pod-id]-5001.proxy.runpod.net/call \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+15038535722",
    "message": "Hello from RunPod cloud!",
    "emotion": "excited"
  }'
```

---

## 🔧 Auto-Start on Boot

Create a startup script:

```bash
# Create service
cat > /etc/systemd/system/voice-ai.service << 'EOF'
[Unit]
Description=Voice AI Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/voice-ai
ExecStart=/usr/bin/python3 runpod_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl enable voice-ai
systemctl start voice-ai
```

---

## 📊 Monitoring

Check server status:
```bash
# View logs
tail -f /var/log/voice-ai.log

# Check if running
curl https://[pod-id]-5001.proxy.runpod.net/health
```

---

## 🎯 Next: Add PersonaPlex 7B

Once basic server is running, add speech-to-speech:

```bash
# In RunPod terminal:
pip install transformers accelerate

# Download PersonaPlex
huggingface-cli download nvidia/PersonaPlex-7B-v1 --local-dir ./personaplex

# Update runpod_server.py to use it for TTS
```

---

## 💡 Tips

1. **Use Network Volumes** for persistent storage ($0.07/GB/mo)
2. **Auto-shutdown** after idle (save money)
3. **Spot instances** for 50% discount (may interrupt)
4. **Save your pod as template** for quick redeploy

---

## 🆘 Troubleshooting

### "Connection refused"
- Check server is running: `python runpod_server.py`
- Verify port 5001 is exposed in pod settings

### "Twilio errors"
- Check env vars are set correctly
- Verify phone number is active
- Check Twilio logs in console

### "Out of memory"
- Use A40 (48GB) instead of 3090 (24GB)
- Enable 8-bit quantization
- Reduce batch size

---

## 🎉 Success!

Your AI voice server is now:
- ☁️ Running in the cloud 24/7
- 📞 Connected to Twilio
- 🌐 Accessible worldwide
- 🚀 Ready to scale

**Cost:** ~$0.35/hr = **~$250/month** for always-on A40

**Or:** Start/stop as needed = **$5-50/month** for light use

---

**Ready to deploy?** Create the RunPod pod now! 🚀
