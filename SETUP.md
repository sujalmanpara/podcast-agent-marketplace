# 🚀 Podcast Clip Agent - Setup Guide

## Step 1: Get Your OpenAI API Key

### **Option 1: Use Single API Key (Recommended)**

1. Go to: https://platform.openai.com/api-keys
2. Sign in (or create account)
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-proj-...`)
5. Use this key for BOTH `OPENAI_API_KEY` and `OPENAI_WHISPER_KEY`

**Why?** Simpler setup, both GPT-4o-mini and Whisper use the same billing.

---

### **Option 2: Use Separate Keys (Optional)**

If you want separate billing tracking:
1. Create two API keys in OpenAI dashboard
2. One for GPT-4o-mini (viral detection)
3. One for Whisper (transcription)

---

## Step 2: Configure Environment Variables

### **For Marketplace Integration (Dhruvit):**

Users will provide API keys via headers:
```bash
curl -X POST .../execute \
  -H "X-User-LLM-Key: sk-proj-..." \
  -H "X-Key-OPENAI_WHISPER_KEY: sk-proj-..."
```

No `.env` file needed! Marketplace handles this.

---

### **For Local Testing:**

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file:**
   ```bash
   nano .env
   ```

3. **Fill in your API keys:**
   ```bash
   # Required
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   OPENAI_WHISPER_KEY=sk-proj-your-actual-key-here
   ```

4. **Save and close**

---

## Step 3: Verify Dependencies

The agent checks these automatically at startup:

```bash
# Check if dependencies are installed
yt-dlp --version
ffmpeg -version
ffprobe -version
```

**If missing, install:**

### **Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
pip install yt-dlp
```

### **macOS:**
```bash
brew install ffmpeg
pip install yt-dlp
```

### **Docker:**
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install yt-dlp
```

---

## Step 4: Test Locally (Optional)

### **Quick Test Script:**

Create `test_agent.sh`:

```bash
#!/bin/bash

# Load environment variables
export $(cat .env | xargs)

# Test with a short video (2-3 minutes recommended)
curl -X POST http://localhost:8000/v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: $OPENAI_API_KEY" \
  -H "X-Key-OPENAI_WHISPER_KEY: $OPENAI_WHISPER_KEY" \
  -d '{
    "prompt": "Create 2 clips from https://youtube.com/watch?v=dQw4w9WgXcQ",
    "options": {
      "num_clips": 2,
      "aspect_ratio": "9:16",
      "add_captions": true
    }
  }'
```

**Run:**
```bash
chmod +x test_agent.sh
./test_agent.sh
```

---

## Step 5: Verify Configuration

### **Check API Key Format:**

OpenAI keys should start with `sk-proj-` (new format) or `sk-` (old format).

**Valid:**
- `sk-proj-abc123def456...`
- `sk-abc123def456...`

**Invalid:**
- `your-api-key-here` ❌
- Empty string ❌
- Spaces or quotes ❌

---

### **Check Permissions:**

```bash
# Make sure .env is not committed to git
cat .gitignore | grep .env

# Should show:
# .env
```

---

## ⚙️ Configuration Options

When calling the agent, you can pass these options:

```json
{
  "prompt": "Create clips from https://youtube.com/watch?v=...",
  "options": {
    "num_clips": 3,           // 1-10 (validated)
    "max_duration": 60,       // 10-180 seconds (validated)
    "min_duration": 15,       // 5-120 seconds (validated)
    "aspect_ratio": "9:16",   // "9:16", "1:1", or "16:9" (validated)
    "add_captions": true,     // true/false
    "virality_threshold": 7.0 // 1.0-10.0 (validated)
  }
}
```

**All values are validated!** Invalid values will be clamped or rejected with clear errors.

---

## 💰 Cost Calculator

### **Per Video Cost:**

```
10-minute video:
├── Whisper: ~$0.06 (10 min × $0.006/min)
├── GPT-4o-mini: ~$0.001 (viral detection)
└── TOTAL: ~$0.07

20-minute video:
├── Whisper: ~$0.12 (20 min × $0.006/min)
├── GPT-4o-mini: ~$0.001 (viral detection)
└── TOTAL: ~$0.13

30-minute video (may timeout):
├── Whisper: ~$0.18
├── GPT-4o-mini: ~$0.001
└── TOTAL: ~$0.19
```

**Recommendation:** Process videos < 20 minutes to avoid timeouts.

---

## 🔒 Security Best Practices

### **DO:**
✅ Keep `.env` file private (never commit to Git)  
✅ Use separate API keys for dev/production  
✅ Set spending limits in OpenAI dashboard  
✅ Rotate API keys regularly  
✅ Use environment variables (not hardcoded keys)  

### **DON'T:**
❌ Share API keys with anyone  
❌ Commit `.env` to GitHub  
❌ Use production keys in logs  
❌ Store keys in plain text files  
❌ Use same key across multiple projects  

---

## 🧪 Testing Checklist

Before deploying:

- [ ] API key is valid (test with `curl`)
- [ ] FFmpeg is installed (`ffmpeg -version`)
- [ ] yt-dlp is installed (`yt-dlp --version`)
- [ ] Test with 2-3 minute video (fast)
- [ ] Test with 10 minute video (typical)
- [ ] Test with invalid URL (should error gracefully)
- [ ] Test with private video (should error gracefully)
- [ ] Test timeout (20+ minute video)
- [ ] Verify clips are created in temp directory
- [ ] Verify captions are burned into video

---

## 🐛 Troubleshooting

### **"OPENAI_API_KEY missing"**
→ Check `.env` file has the key  
→ No spaces, no quotes around the value  
→ Key starts with `sk-proj-` or `sk-`

### **"Missing required system dependencies: ffmpeg, yt-dlp"**
→ Install FFmpeg: `apt-get install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)  
→ Install yt-dlp: `pip install yt-dlp`

### **"Download failed"**
→ Video may be private, age-restricted, or deleted  
→ Check YouTube URL is correct and public  
→ Try a different video

### **"Whisper API timeout"**
→ Video too long (try < 10 minutes)  
→ Audio file > 25MB (compress or use shorter video)  
→ Network slow, try again

### **"No viral moments found"**
→ Lower `virality_threshold` (try 6.0 or 5.0)  
→ Video content may not have clear viral moments  
→ Try a different video (interviews, podcasts work best)

### **"Caption burning failed"**
→ Non-fatal error, clips created without captions  
→ Check FFmpeg is installed correctly  
→ File permissions issue (temp directory)

### **"Agent timeout"**
→ Video too long (>20 minutes)  
→ Process shorter videos  
→ Or ask Dhruvit to increase timeout (current: 300s)

---

## 📞 Support

**Author:** Sam (@sujalmanpara)  
**GitHub:** https://github.com/sujalmanpara/podcast-agent-marketplace  
**Telegram:** @Sujal_manpara  

---

## ✅ Quick Start Summary

```bash
# 1. Get API key
open https://platform.openai.com/api-keys

# 2. Create .env file
cp .env.example .env
nano .env  # Add your key

# 3. Install dependencies
pip install yt-dlp
apt-get install ffmpeg  # or brew install ffmpeg

# 4. Test
./test_agent.sh

# 5. Deploy to marketplace
# (Dhruvit handles this)
```

**You're ready to go!** 🚀
