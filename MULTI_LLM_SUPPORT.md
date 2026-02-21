# 🤖 Multi-LLM Support - OpenAI, Anthropic, and Google

**Version:** 3.0.0  
**Date:** 2026-02-21  
**Upgrade:** Better models + provider flexibility

---

## 🎯 **What Changed**

### **Before (v2.0):**
- ❌ Only OpenAI GPT-4o-mini
- ❌ Hardcoded model
- ❌ No provider choice

### **After (v3.0):**
- ✅ **3 providers:** OpenAI, Anthropic, Google
- ✅ **Better default models:** GPT-4o, Claude Sonnet 4, Gemini 2.0
- ✅ **Custom model selection:** Override with any model
- ✅ **Backward compatible:** Still works with just OPENAI_API_KEY

---

## 🚀 **Supported LLM Providers**

### **1. OpenAI (Default)**

**Default model:** `gpt-4o` (better than gpt-4o-mini!)

**Other models:**
- `gpt-4o-mini` — Cheaper, faster
- `gpt-4-turbo` — More powerful
- `o1-preview` — Advanced reasoning

**API Key:** `OPENAI_API_KEY`

**Cost (viral detection):**
- gpt-4o-mini: ~$0.002/video
- gpt-4o: ~$0.01/video
- gpt-4-turbo: ~$0.015/video

---

### **2. Anthropic (Claude)**

**Default model:** `claude-sonnet-4`

**Other models:**
- `claude-sonnet-3-5` — Cheaper, still great
- `claude-opus-4` — Most powerful
- `claude-haiku-3-5` — Fastest

**API Key:** `ANTHROPIC_API_KEY`

**Cost (viral detection):**
- claude-sonnet-4: ~$0.015/video
- claude-opus-4: ~$0.075/video
- claude-haiku-3-5: ~$0.001/video

---

### **3. Google (Gemini)**

**Default model:** `gemini-2.0-flash-thinking-exp-1219` (with extended thinking!)

**Other models:**
- `gemini-2.0-flash-exp` — Fast, accurate
- `gemini-1.5-pro` — Older, stable
- `gemini-1.5-flash` — Budget option

**API Key:** `GOOGLE_API_KEY`

**Cost (viral detection):**
- gemini-2.0-flash-thinking: **FREE** (up to 60 req/min)
- gemini-2.0-flash: **FREE** (up to 60 req/min)
- gemini-1.5-pro: ~$0.007/video

**Note:** Gemini thinking models are experimental but excellent at finding viral moments!

---

## 📝 **How to Use**

### **Option 1: Default (OpenAI GPT-4o)**

**No changes needed!** Just provide `OPENAI_API_KEY`:

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-..."
  }
}
```

**Uses:** `openai` provider with `gpt-4o` model

---

### **Option 2: Switch Provider**

**Use Anthropic (Claude Sonnet 4):**

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-whisper-key",
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "LLM_PROVIDER": "anthropic"
  }
}
```

**Use Google (Gemini Thinking):**

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-whisper-key",
    "GOOGLE_API_KEY": "AIza...",
    "LLM_PROVIDER": "google"
  }
}
```

---

### **Option 3: Custom Model**

**Use GPT-4o-mini (cheaper):**

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-...",
    "OPENAI_API_KEY": "sk-...",
    "LLM_PROVIDER": "openai",
    "LLM_MODEL": "gpt-4o-mini"
  }
}
```

**Use Claude Opus 4 (most powerful):**

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-...",
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "LLM_PROVIDER": "anthropic",
    "LLM_MODEL": "claude-opus-4"
  }
}
```

**Use Gemini 2.0 Flash (FREE!):**

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-...",
    "GOOGLE_API_KEY": "AIza...",
    "LLM_PROVIDER": "google",
    "LLM_MODEL": "gemini-2.0-flash-exp"
  }
}
```

---

## 🎯 **Which Model to Choose?**

### **Best Overall: GPT-4o (OpenAI) - Default**
- ✅ Excellent at finding viral moments
- ✅ Great balance of speed/cost/quality
- ✅ Most reliable
- 💰 ~$0.01/video

### **Best Value: Gemini 2.0 Thinking (Google)**
- ✅ **FREE** (up to 60 videos/min!)
- ✅ Extended thinking for better analysis
- ✅ Experimental but impressive
- ⚠️ Slightly slower (thinking time)

### **Best Quality: Claude Opus 4 (Anthropic)**
- ✅ Most nuanced understanding
- ✅ Best at detecting subtle viral potential
- ✅ Great for long-form content
- 💰 ~$0.075/video (expensive)

### **Best Speed: Claude Haiku (Anthropic)**
- ✅ Fastest responses
- ✅ Still good quality
- ✅ Great for bulk processing
- 💰 ~$0.001/video (cheapest paid option)

---

## 📊 **Performance Comparison**

| Provider | Model | Speed | Quality | Cost/video | FREE? |
|----------|-------|-------|---------|------------|-------|
| OpenAI | gpt-4o (default) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $0.01 | ❌ |
| OpenAI | gpt-4o-mini | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | $0.002 | ❌ |
| Anthropic | claude-sonnet-4 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $0.015 | ❌ |
| Anthropic | claude-opus-4 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $0.075 | ❌ |
| Anthropic | claude-haiku-3-5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.001 | ❌ |
| Google | gemini-2.0-flash-thinking | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | FREE | ✅ |
| Google | gemini-2.0-flash | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | FREE | ✅ |

---

## 🔧 **Technical Details**

### **New Files:**
- `llm_service.py` — Unified LLM client (OpenAI, Anthropic, Google)

### **Updated Files:**
- `executor.py` — Provider selection logic
- `viral_detector.py` — Uses llm_service instead of direct OpenAI
- `caption_generator.py` — Added provider/model params (future use)
- `manifest.json` — Optional env vars for multi-provider support

### **Backward Compatibility:**
✅ Old configs still work (defaults to OpenAI GPT-4o)  
✅ No breaking changes

---

## 🎓 **Example Usage**

### **Default (OpenAI GPT-4o):**

```bash
curl -X POST .../v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: sk-whisper-key" \
  -d '{
    "prompt": "Create 3 clips from https://youtu.be/abc123"
  }'
```

### **With Gemini (FREE!):**

```bash
curl -X POST .../v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: sk-whisper-key" \
  -d '{
    "prompt": "Create 3 clips from https://youtu.be/abc123",
    "keys": {
      "OPENAI_WHISPER_KEY": "sk-...",
      "GOOGLE_API_KEY": "AIza...",
      "LLM_PROVIDER": "google"
    }
  }'
```

### **With Claude Opus (Best Quality):**

```bash
curl -X POST .../v1/agents/podcast-clip-agent/execute \
  -H "Content-Type: application/json" \
  -H "X-User-LLM-Key: sk-whisper-key" \
  -d '{
    "prompt": "Create 3 clips from https://youtu.be/abc123",
    "keys": {
      "OPENAI_WHISPER_KEY": "sk-...",
      "ANTHROPIC_API_KEY": "sk-ant-...",
      "LLM_PROVIDER": "anthropic",
      "LLM_MODEL": "claude-opus-4"
    }
  }'
```

---

## 🐛 **Troubleshooting**

### **Error: "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"**

**Solution:** Provide the correct API key for the provider:

```json
{
  "keys": {
    "OPENAI_WHISPER_KEY": "sk-...",
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "LLM_PROVIDER": "anthropic"
  }
}
```

### **Error: "Invalid LLM_PROVIDER"**

**Solution:** Use only: `openai`, `anthropic`, or `google`

### **Error: "Google API blocked the request (safety filters)"**

**Solution:** 
- Gemini has strict safety filters
- Try a different video
- Or switch to OpenAI/Anthropic

---

## 🚀 **Benefits**

✅ **Better default model:** GPT-4o instead of GPT-4o-mini  
✅ **Provider choice:** Pick based on cost/quality/speed  
✅ **FREE option:** Gemini 2.0 (60 req/min)  
✅ **Custom models:** Override with any model  
✅ **Future-proof:** Easy to add new providers  

---

## 📦 **Deployment**

**Commit:** TBD  
**Version:** 3.0.0  
**Backward Compatible:** ✅ Yes  

**To deploy:**
1. Push to GitHub
2. Reload marketplace
3. Test with each provider
4. Update user docs

---

## 🎯 **Recommended Config**

**For most users (best balance):**
```json
{
  "LLM_PROVIDER": "openai"
}
```
Uses GPT-4o (default), ~$0.01/video

**For free tier:**
```json
{
  "LLM_PROVIDER": "google"
}
```
Uses Gemini 2.0 Thinking, FREE!

**For best quality:**
```json
{
  "LLM_PROVIDER": "anthropic",
  "LLM_MODEL": "claude-opus-4"
}
```
Uses Claude Opus 4, ~$0.075/video

---

**Status:** ✅ Ready to test & deploy!
