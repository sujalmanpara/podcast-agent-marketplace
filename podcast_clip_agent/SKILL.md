# Podcast Clip Generator

Convert long-form podcasts into viral short-form clips with AI-powered scene detection and captions.

> **Marketplace agent by Sam (@sujalmanpara).** Logic runs on Nextbase servers. Your API keys are used in-memory only and never stored.

## When to Use

- User wants to create short clips from a podcast/video
- User mentions "viral clips", "extract moments", "clip this video"
- User provides a YouTube URL or video link
- User wants to repurpose long-form content for TikTok/YouTube Shorts/Instagram

## Setup

Set these environment variables:

- **OPENAI_API_KEY** - For AI viral moment detection (GPT-4o-mini)
- **OPENAI_WHISPER_KEY** - For audio transcription (Whisper API, can be same as above)

## How to Execute

```bash
curl -s -X POST https://marketplacebackend-production-58c8.up.railway.app/v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: YOUR_OPENAI_KEY" \
  -H "X-Key-OPENAI_WHISPER_KEY: YOUR_OPENAI_KEY" \
  -d '{
    "prompt": "Create 3 viral clips from https://youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "en",
    "options": {
      "num_clips": 3,
      "aspect_ratio": "9:16",
      "add_captions": true
    }
  }'
```

## Usage Examples

**Simple:**
```
Create clips from https://youtube.com/watch?v=abc123
```

**With options:**
```
Extract 5 viral moments from this podcast: https://youtube.com/watch?v=xyz
Make them vertical (9:16) with captions
```

**Custom settings:**
```
Generate 3 clips from https://youtube.com/watch?v=abc
Each clip should be 30-45 seconds
Only clips with virality score above 8
Square format for Instagram
```

## Response (SSE Stream)

The agent streams events as it works:

| Event | Meaning |
|-------|---------|
| `event: status` | Progress update — display to user |
| `event: result` | Final clips data — return as answer |
| `event: error` | Something went wrong |

**Example stream:**

```
event: status
data: {"message": "🎬 Found video: https://youtube.com/watch?v=..."}

event: status
data: {"message": "⬇️ Downloading video... (this may take 1-2 minutes)"}

event: status
data: {"message": "✅ Downloaded: video.mp4"}

event: status
data: {"message": "🎤 Transcribing audio with Whisper... (1-3 minutes)"}

event: status
data: {"message": "✅ Transcription complete (1,234 words)"}

event: status
data: {"message": "🤖 Analyzing transcript for top 3 viral moments..."}

event: status
data: {"message": "✅ Found 3 viral moments"}

event: status
data: {"message": "✂️ Creating 3 video clips..."}

event: status
data: {"message": "✅ Created 3 clips"}

event: status
data: {"message": "📝 Generating AI captions for clips..."}

event: status
data: {"message": "✅ Captions added to all clips"}

event: result
data: {
  "success": true,
  "num_clips": 3,
  "clips": [
    {
      "clip_id": "a1b2c3d4",
      "title": "AI Can Do WHAT?!",
      "score": 8.5,
      "duration": 23.3,
      "file_path": "/tmp/clip_1_a1b2c3d4.mp4",
      "file_size_mb": 12.5,
      "has_captions": true
    },
    ...
  ],
  "message": "✅ Successfully created 3 viral clips!",
  "note": "Clips are temporary. Download them within 1 hour or they'll be deleted."
}
```

## Options

Pass these in the `options` field:

- **num_clips** - Number of clips to create (default: 3, max: 10)
- **max_duration** - Max clip duration in seconds (default: 60)
- **min_duration** - Min clip duration in seconds (default: 15)
- **aspect_ratio** - `"9:16"` (vertical), `"1:1"` (square), or `"16:9"` (horizontal, default: `"9:16"`)
- **add_captions** - Add AI-generated captions (default: `true`)
- **virality_threshold** - Min virality score 1-10 (default: `7.0`)

## Limitations

- **Video length**: Recommended < 20 minutes (longer videos may timeout)
- **File size**: YouTube downloads max ~500MB
- **Processing time**: ~3-8 minutes total (download + transcribe + clip)
- **Timeout**: Agent has 5-minute timeout (300s)
- **Clip storage**: Temporary (deleted after 1 hour)

## Supported Platforms

- ✅ YouTube (any public video)
- ✅ Direct video URLs (.mp4, .webm, .mkv, .avi, .mov)
- ❌ Private/unlisted videos
- ❌ Live streams
- ❌ Age-restricted content (without auth)

## Cost

**Agent execution:** FREE (marketplace handles compute)  
**API calls:** User pays (uses their own keys)

- **Whisper API**: ~$0.006 per minute of audio
  - 10-min video: ~$0.06
- **GPT-4o-mini**: ~$0.0001 per request
  - Viral detection: ~$0.001
  - Total per 10-min video: **~$0.07**

## Troubleshooting

**"Download failed"**
- Video may be private, age-restricted, or deleted
- Check YouTube URL is correct
- Try a different video

**"Whisper API timeout"**
- Video too long (try < 10 minutes)
- Network slow, try again

**"No viral moments found"**
- Lower `virality_threshold` (try 6.0 or 5.0)
- Video content may not have clear viral moments
- Try a different video

**"Caption burning failed"**
- Non-fatal error, clips created without captions
- Check FFmpeg is installed

**"Agent timeout"**
- Video too long (>20 minutes)
- Process shorter videos

## Dependencies (for Dhruvit)

```bash
pip install yt-dlp openai httpx
# FFmpeg required (system package)
apt-get install ffmpeg  # Debian/Ubuntu
brew install ffmpeg     # macOS
```

## Author

Sam (@sujalmanpara)  
GitHub: https://github.com/sujalmanpara/podcast-clip-agent-backend  
Telegram: @Sujal_manpara
