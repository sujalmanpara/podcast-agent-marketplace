# 🎬 Podcast Clip Agent - Marketplace Version

**AI-powered podcast → viral short-form clips**

Convert long-form podcasts into engaging short clips with AI-powered viral moment detection and auto-captions. Built for [Nextbase Agent Marketplace](https://agents.nextbase.solutions).

[![GitHub](https://img.shields.io/badge/GitHub-sujalmanpara-blue?logo=github)](https://github.com/sujalmanpara/podcast-agent-marketplace)
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## ✨ **Features**

- 📥 **YouTube Download** - Download any public YouTube video (yt-dlp)
- 🎤 **Auto Transcription** - OpenAI Whisper API with timestamps
- 🤖 **AI Viral Detection** - GPT-4o-mini analyzes transcript for shareable moments
- ✂️ **Smart Clipping** - FFmpeg creates 1-10 clips per video
- 📝 **Auto Captions** - AI-generated captions burned into video
- 📊 **Real-time Progress** - SSE streaming for live updates
- ⚡ **Stateless** - No database, no background jobs
- 💰 **Cost-effective** - ~$0.07 per 10-minute video

---

## 🚀 **Quick Start (Marketplace Integration)**

### **For Marketplace Owners (Dhruvit)**

```bash
# 1. Extract package
tar -xzf podcast-agent-marketplace.tar.gz

# 2. Copy to marketplace
cp -r podcast-agent-marketplace/podcast_clip_agent /path/to/marketplace/app/agents/

# 3. Install dependencies
pip install yt-dlp==2024.12.23 openai==1.0.0
apt-get install ffmpeg  # System package

# 4. Reload agents (hot reload, no restart!)
curl -X POST https://marketplacebackend-production-58c8.up.railway.app/admin/agents/reload \
  -H "X-Admin-Secret: YOUR_SECRET"

# 5. Verify
curl https://marketplacebackend-production-58c8.up.railway.app/marketplace/agents | \
  jq '.[] | select(.id=="podcast-clip-agent")'
```

**Integration time:** ~15 minutes

---

## 🎯 **Usage Examples**

### **Via OpenClaw**

```
Create 3 viral clips from https://youtube.com/watch?v=dQw4w9WgXcQ
```

```
Extract 5 clips from this podcast: https://youtube.com/watch?v=abc123
Make them vertical (9:16) with captions
Each clip should be 30-45 seconds
```

### **Via API**

```bash
curl -s -X POST https://marketplacebackend-production-58c8.up.railway.app/v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: sk-..." \
  -H "X-Key-OPENAI_WHISPER_KEY: sk-..." \
  -d '{
    "prompt": "Create clips from https://youtube.com/watch?v=abc123",
    "options": {
      "num_clips": 3,
      "aspect_ratio": "9:16",
      "add_captions": true
    }
  }'
```

---

## ⚙️ **Configuration Options**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `num_clips` | int | 3 | Number of clips to create (1-10) |
| `max_duration` | int | 60 | Max clip duration (seconds) |
| `min_duration` | int | 15 | Min clip duration (seconds) |
| `aspect_ratio` | string | "9:16" | "9:16" (vertical), "1:1" (square), "16:9" (horizontal) |
| `add_captions` | bool | true | Burn AI-generated captions into video |
| `virality_threshold` | float | 7.0 | Min virality score 1-10 |

---

## 📊 **How It Works**

```
1. Download video (yt-dlp)           → 1-2 min
2. Transcribe audio (Whisper API)    → 1-3 min
3. Detect viral moments (GPT-4o)     → 10-30 sec
4. Create clips (FFmpeg)             → 1-2 min
5. Add captions (FFmpeg)             → 30 sec - 1 min
                                     ────────────
                           TOTAL:    ~4-8 minutes
```

Real-time progress shown via SSE events at each step.

---

## 💰 **Cost (User Pays)**

**Agent execution:** FREE (marketplace handles compute)

**API calls:** User provides own keys
- **Whisper API**: ~$0.006 per minute of audio
  - 10-min video: ~$0.06
  - 30-min video: ~$0.18
- **GPT-4o-mini**: ~$0.0001 per request
  - Viral detection: ~$0.001

**Total per 10-min video:** ~$0.07

---

## 🔑 **Required API Keys**

- **OPENAI_API_KEY** - For viral moment detection (GPT-4o-mini)
- **OPENAI_WHISPER_KEY** - For transcription (can be same as above)

Get your key: https://platform.openai.com/api-keys

---

## ⚠️ **Limitations**

- **Video length**: Recommended < 20 minutes (longer may timeout)
- **Processing time**: ~4-8 minutes total
- **Timeout**: 300 seconds (5 minutes)
- **Clip storage**: Temporary (deleted after 1 hour)
- **Supported platforms**: YouTube (public videos only), direct video URLs

---

## 📂 **Architecture**

### **Files**

```
podcast_clip_agent/
├── manifest.json           # Marketplace metadata
├── executor.py             # Main entry point (async execute())
├── SKILL.md               # OpenClaw documentation
├── downloader.py          # yt-dlp wrapper
├── transcriber.py         # Whisper API wrapper
├── viral_detector.py      # LLM viral moment detection
├── clipper.py             # FFmpeg video cutting
├── caption_generator.py   # SRT generation + burning
└── README.md              # Integration guide
```

### **Pattern**

- ✅ **Stateless** - No database, no background jobs
- ✅ **SSE streaming** - Real-time progress updates
- ✅ **Single execution** - One request = one response
- ✅ **User provides everything** - API keys, options, video URL
- ✅ **Marketplace integration** - Follows Nextbase pattern exactly

---

## 🧪 **Testing**

### **Local Test**

```bash
# Start marketplace locally
cd /path/to/marketplace
python -m uvicorn app.main:app --port 8000

# Test agent
curl -X POST http://localhost:8000/v1/agents/podcast-clip-agent/execute \
  -H "X-User-LLM-Key: YOUR_KEY" \
  -H "X-Key-OPENAI_WHISPER_KEY: YOUR_KEY" \
  -d '{"prompt": "Create clips from https://youtube.com/watch?v=SHORT_VIDEO"}'
```

**Tip:** Test with a 2-5 minute video first!

---

## 🚢 **Deployment (Railway/Render)**

### **Dockerfile**

```dockerfile
# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
RUN pip install yt-dlp==2024.12.23 openai==1.0.0
```

### **requirements.txt**

```txt
yt-dlp==2024.12.23
openai==1.0.0
httpx>=0.24.0
```

---

## 🔄 **Converted from Standalone SaaS**

This agent was originally a standalone SaaS with:
- ❌ FastAPI app with 4 routes
- ❌ PostgreSQL database
- ❌ Celery + Redis background jobs
- ❌ Docker containers

**Now marketplace-ready with:**
- ✅ Single `execute()` function
- ✅ No database (stateless)
- ✅ SSE streaming (real-time updates)
- ✅ Python module (no Docker needed)

See [CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md) for details.

---

## 🐛 **Troubleshooting**

### **"Download failed"**
- Video may be private, age-restricted, or deleted
- Check YouTube URL is correct

### **"Whisper API timeout"**
- Video too long (try < 10 minutes)
- Network slow, try again

### **"No viral moments found"**
- Lower `virality_threshold` (try 6.0 or 5.0)
- Video content may not have clear viral moments

### **"Caption burning failed"**
- Non-fatal error, clips created without captions
- Check FFmpeg is installed

### **"Agent timeout"**
- Video too long (>20 minutes)
- Process shorter videos

---

## 📚 **Documentation**

- **[SKILL.md](podcast_clip_agent/SKILL.md)** - OpenClaw integration guide
- **[README.md](podcast_clip_agent/README.md)** - Marketplace integration (for Dhruvit)
- **[CONVERSION_SUMMARY.md](CONVERSION_SUMMARY.md)** - Architecture changes
- **[.env.example](.env.example)** - Environment variables template

---

## 🤝 **Related Projects**

- **[LinkedIn Agent](https://github.com/sujalmanpara/linkedin-agent-marketplace)** - LinkedIn automation agent (marketplace version)
- **[Podcast Clip Agent (SaaS)](https://github.com/sujalmanpara/podcast-clip-agent-backend)** - Original standalone version

---

## 📄 **License**

MIT License - see LICENSE file for details

---

## 👤 **Author**

**Sam (@sujalmanpara)**

- GitHub: [@sujalmanpara](https://github.com/sujalmanpara)
- Telegram: [@Sujal_manpara](https://t.me/Sujal_manpara)

---

## 🙏 **Acknowledgments**

- Built for [Nextbase Agent Marketplace](https://agents.nextbase.solutions)
- Architecture pattern by [Dhruvit](https://github.com/dhruvitnavadiya)
- Powered by OpenAI (Whisper + GPT-4o-mini)
- Video processing with FFmpeg & yt-dlp

---

**⭐ Star this repo if you find it useful!**
