# Podcast Clip Generator for Nextbase Marketplace

AI-powered podcast → viral short-form clips. Automatic transcription, viral moment detection, and caption generation.

---

## 📦 **Installation (for Dhruvit)**

### **Step 1: Copy to Marketplace**

```bash
cp -r podcast_clip_agent /path/to/marketplace/app/agents/
```

### **Step 2: Install Dependencies**

Add to `requirements.txt`:

```txt
yt-dlp==2024.12.23
openai==1.0.0
```

Install system dependencies:

```bash
# FFmpeg (required for video processing)
apt-get install ffmpeg  # Debian/Ubuntu
brew install ffmpeg     # macOS

# yt-dlp (Python package, already in requirements.txt)
pip install yt-dlp openai
```

### **Step 3: Reload Agents**

```bash
curl -s -X POST https://marketplacebackend-production-58c8.up.railway.app/admin/agents/reload \
  -H "X-Admin-Secret: YOUR_ADMIN_SECRET"
```

---

## ✅ **Verification**

```bash
curl https://marketplacebackend-production-58c8.up.railway.app/marketplace/agents | \
  jq '.[] | select(.id=="podcast-clip-agent")'
```

Expected output:

```json
{
  "id": "podcast-clip-agent",
  "name": "Podcast Clip Generator",
  "description": "Convert long-form podcasts into viral short-form clips...",
  "version": "2.0.0",
  "enabled": true
}
```

---

## 🧪 **Test the Agent**

```bash
curl -X POST http://localhost:8000/v1/agents/podcast-clip-agent/execute \
  -H "X-User-LLM-Key: YOUR_OPENAI_KEY" \
  -H "X-Key-OPENAI_WHISPER_KEY: YOUR_OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create clips from https://youtube.com/watch?v=dQw4w9WgXcQ",
    "options": {"num_clips": 2, "aspect_ratio": "9:16"}
  }'
```

---

## 📂 **File Structure**

```
podcast_clip_agent/
├── manifest.json           # Agent metadata
├── executor.py             # Main entry point
├── SKILL.md               # OpenClaw documentation
├── downloader.py          # yt-dlp wrapper
├── transcriber.py         # Whisper API wrapper
├── viral_detector.py      # LLM-powered moment detection
├── clipper.py             # FFmpeg video cutting
├── caption_generator.py   # SRT generation + burning
└── README.md              # This file
```

---

## 🎯 **Features**

✅ Download from YouTube or direct video URLs  
✅ Automatic transcription with Whisper API  
✅ AI-powered viral moment detection (GPT-4o-mini)  
✅ Create 1-10 clips per video  
✅ Multiple aspect ratios (9:16, 1:1, 16:9)  
✅ AI-generated captions (burned into video)  
✅ SSE progress updates  
✅ Stateless (no database)  

---

## ⚠️ **Important Notes**

### **Timeout Warning**
- **Default timeout:** 300s (5 minutes)
- **Recommended video length:** < 20 minutes
- **Longer videos may timeout** during transcription/processing

### **Temporary Storage**
- Clips are stored in `/tmp/` (deleted after 1 hour)
- Users should download clips immediately
- For production, consider cloud storage (S3, R2, etc.)

### **Cost (User Pays)**
- Whisper API: ~$0.006/min (~$0.06 for 10-min video)
- GPT-4o-mini: ~$0.001 per analysis
- **Total:** ~$0.07 per 10-minute video

---

## 🔧 **Dependencies**

**Python packages:**
- `yt-dlp` - YouTube/video downloads
- `openai` - Whisper + GPT API
- `httpx` - HTTP client (already in marketplace)

**System packages:**
- `ffmpeg` - Video processing (cutting, formatting, captions)

**Installation (Railway/Render):**

```dockerfile
# Dockerfile
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install yt-dlp==2024.12.23 openai==1.0.0
```

---

## 📊 **Workflow**

```
1. Download video (yt-dlp)           → 1-2 min
2. Transcribe audio (Whisper API)    → 1-3 min
3. Detect viral moments (GPT-4o)     → 10-30 sec
4. Create clips (FFmpeg)             → 1-2 min
5. Add captions (FFmpeg)             → 30 sec - 1 min
                                     ────────────
                           TOTAL:    ~4-8 minutes
```

**Progress shown via SSE events at each step**

---

## 🐛 **Known Issues & Solutions**

**Issue:** FFmpeg subtitle burn error  
**Solution:** Already fixed (path escaping) ✅

**Issue:** Timeout on long videos  
**Solution:** Recommend < 20 min videos, or increase timeout in manifest

**Issue:** yt-dlp download fails  
**Cause:** Private/age-restricted video  
**Solution:** Return user-friendly error

**Issue:** No viral moments found  
**Solution:** Lower `virality_threshold` or try different video

---

## 🚀 **Production Deployment**

### **Railway Build Command**

```bash
pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg
```

### **Environment Variables**

None required (marketplace handles user keys)

### **Storage (Future Enhancement)**

For persistent clip storage, add S3/R2:

```python
# In clipper.py, after creating clip:
clip_url = await upload_to_s3(clip_file)
clip["public_url"] = clip_url
```

---

## 📞 **Support**

**Author:** Sam (@sujalmanpara)  
**GitHub:** https://github.com/sujalmanpara/podcast-clip-agent-backend  
**Telegram:** @Sujal_manpara  

---

## ✅ **Integration Checklist for Dhruvit**

- [ ] Copy `podcast_clip_agent/` to `app/agents/`
- [ ] Add `yt-dlp==2024.12.23 openai==1.0.0` to `requirements.txt`
- [ ] Install FFmpeg in Docker/Railway build
- [ ] Test with short video (<5 min)
- [ ] Verify SSE events stream correctly
- [ ] Test timeout handling (try 30-min video)
- [ ] Deploy to production
- [ ] Update marketplace UI

---

**Ready to ship!** 🎉
