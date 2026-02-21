"""
Podcast Clip Agent - Executor
Converts long-form podcasts into viral short-form clips with AI.
Entry point: execute() — follows Nextbase marketplace async generator pattern.
"""
import asyncio
import httpx
import os
import re
import subprocess
import tempfile
from pathlib import Path

from app.core.sse import sse_event, sse_error
from app.core.config import settings

# Agent-specific modules
from .downloader import download_video
from .transcriber import transcribe_audio
from .viral_detector import detect_viral_moments
from .clipper import create_clips_from_moments
from .caption_generator import generate_captions_for_clips


# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

def _check_dependencies() -> tuple[bool, list[str]]:
    """
    Verify all required system dependencies are installed.

    Returns:
        (all_ok: bool, missing: list[str])
    """
    deps = {
        "yt-dlp": ["yt-dlp", "--version"],
        "ffmpeg":  ["ffmpeg",  "-version"],
        "ffprobe": ["ffprobe", "-version"],
    }

    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=5)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            missing.append(name)

    return (len(missing) == 0, missing)


# ---------------------------------------------------------------------------
# URL extraction
# ---------------------------------------------------------------------------

def _extract_url(text: str) -> str | None:
    """
    Extract a video URL from free-form text.

    Supports:
      - youtube.com/watch?v=ID
      - youtu.be/ID
      - youtube.com/shorts/ID
      - youtube.com/live/ID
      - m.youtube.com/...
      - Direct video file URLs (.mp4, .webm, .mkv, .avi, .mov, .m4v)
    """
    # Covers watch, shorts, live, embed, and youtu.be short links
    youtube_pattern = (
        r'(?:https?://)?'
        r'(?:www\.|m\.)?'
        r'(?:'
            r'youtube\.com/(?:watch\?v=|shorts/|live/|embed/)'
            r'|youtu\.be/'
        r')'
        r'([\w\-]{11})'          # YouTube video IDs are always 11 chars
    )

    match = re.search(youtube_pattern, text, re.IGNORECASE)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"

    # Direct video file URL
    direct_pattern = r'https?://[^\s]+\.(?:mp4|webm|mkv|avi|mov|m4v)(?:\?[^\s]*)?'
    match = re.search(direct_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)

    return None


# ---------------------------------------------------------------------------
# Main executor
# ---------------------------------------------------------------------------

async def execute(prompt: str, keys: dict, language: str = None, options: dict = None):
    """
    Main executor for Podcast Clip Agent.

    Args:
        prompt: User's request containing a video URL, e.g.:
                "Create 3 viral clips from https://youtu.be/dQw4w9WgXcQ"

        keys: {
            "OPENAI_API_KEY":    "sk-...",   # viral moment detection
            "OPENAI_WHISPER_KEY": "sk-..."   # transcription (may be same key)
        }

        language: ISO-639-1 code ("en", "es", ...) — optional Whisper hint

        options: {
            "num_clips":          3,      # 1-10
            "max_duration":       60,     # seconds (10-180)
            "min_duration":       15,     # seconds (5-120)
            "aspect_ratio":       "9:16", # "9:16" | "1:1" | "16:9"
            "add_captions":       true,
            "virality_threshold": 7.0     # 1.0-10.0
        }

    Yields:
        SSE events with status updates and final result payload
    """
    try:
        # ── Dependency check ──────────────────────────────────────────────
        deps_ok, missing_deps = _check_dependencies()
        if not deps_ok:
            yield sse_error(
                f"Missing required system dependencies: {', '.join(missing_deps)}. "
                "Please ask the marketplace administrator to install them."
            )
            return

        # ── API keys & LLM configuration ──────────────────────────────────
        
        # LLM provider selection (openai, anthropic, or google)
        llm_provider = keys.get("LLM_PROVIDER", "openai").lower()
        llm_model = keys.get("LLM_MODEL")  # Optional, uses provider defaults if not set
        
        # Get API key for selected provider
        llm_api_key = None
        if llm_provider == "openai":
            llm_api_key = keys.get("OPENAI_API_KEY")
            if not llm_api_key:
                yield sse_error("OPENAI_API_KEY is required when LLM_PROVIDER=openai (or default)")
                return
        elif llm_provider == "anthropic":
            llm_api_key = keys.get("ANTHROPIC_API_KEY")
            if not llm_api_key:
                yield sse_error("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
                return
        elif llm_provider == "google":
            llm_api_key = keys.get("GOOGLE_API_KEY")
            if not llm_api_key:
                yield sse_error("GOOGLE_API_KEY is required when LLM_PROVIDER=google")
                return
        else:
            yield sse_error(f"Invalid LLM_PROVIDER: {llm_provider}. Use 'openai', 'anthropic', or 'google'")
            return
        
        # Whisper key (always OpenAI for transcription)
        whisper_key = keys.get("OPENAI_WHISPER_KEY")
        if not whisper_key:
            yield sse_error("OPENAI_WHISPER_KEY is required for transcription.")
            return

        # ── Options validation ────────────────────────────────────────────
        opts = options or {}

        num_clips = max(1, min(int(opts.get("num_clips", 3)), 10))

        max_duration = max(10,  min(int(opts.get("max_duration", 60)),  180))
        min_duration = max(5,   min(int(opts.get("min_duration", 15)),  120))

        if min_duration >= max_duration:
            yield sse_error(
                f"min_duration ({min_duration}s) must be less than max_duration ({max_duration}s)."
            )
            return

        aspect_ratio = opts.get("aspect_ratio", "9:16")
        if aspect_ratio not in ("9:16", "1:1", "16:9"):
            yield sse_error(
                f"Invalid aspect_ratio '{aspect_ratio}'. Must be '9:16', '1:1', or '16:9'."
            )
            return

        add_captions        = bool(opts.get("add_captions", True))
        virality_threshold  = max(1.0, min(float(opts.get("virality_threshold", 7.0)), 10.0))

        # ── URL extraction ────────────────────────────────────────────────
        video_url = _extract_url(prompt)
        if not video_url:
            yield sse_error(
                "No video URL found in prompt. "
                "Provide a YouTube link (watch, shorts, live) or a direct video URL."
            )
            return

        yield sse_event("status", f"🎬 Found video: {video_url}")

        # ── Pipeline ──────────────────────────────────────────────────────
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            async with httpx.AsyncClient(timeout=300) as client:

                # Step 1 — Download
                yield sse_event("status", "⬇️ Downloading video… (1-2 min)")
                try:
                    video_file = await download_video(video_url, str(temp_path))
                    yield sse_event("status", f"✅ Downloaded: {Path(video_file).name}")
                except Exception as e:
                    yield sse_error(f"Download failed: {e}")
                    return

                # Step 2 — Transcribe
                yield sse_event("status", "🎤 Transcribing audio with Whisper… (1-3 min)")
                try:
                    transcript = await transcribe_audio(
                        client, whisper_key, video_file, language=language
                    )
                    word_count = len(transcript.get("text", "").split())
                    yield sse_event("status", f"✅ Transcription complete ({word_count} words)")
                except Exception as e:
                    yield sse_error(f"Transcription failed: {e}")
                    return

                # Step 3 — Viral detection
                model_info = llm_model or f"{llm_provider} (default)"
                yield sse_event("status", f"🤖 Analysing transcript for top {num_clips} viral moments with {model_info}…")
                try:
                    viral_moments = await detect_viral_moments(
                        client,
                        llm_api_key,
                        transcript,
                        num_clips=num_clips,
                        min_duration=min_duration,
                        max_duration=max_duration,
                        threshold=virality_threshold,
                        provider=llm_provider,
                        model=llm_model
                    )
                    if not viral_moments:
                        yield sse_error(
                            "No viral moments found. "
                            "Try lowering virality_threshold or use a different video."
                        )
                        return
                    yield sse_event("status", f"✅ Found {len(viral_moments)} viral moments")
                except Exception as e:
                    yield sse_error(f"Viral detection failed: {e}")
                    return

                # Step 4 — Create clips (parallel)
                yield sse_event("status", f"✂️ Creating {len(viral_moments)} video clips in parallel…")
                try:
                    clips = await create_clips_from_moments(
                        video_file,
                        viral_moments,
                        str(temp_path),
                        aspect_ratio=aspect_ratio
                    )
                    yield sse_event("status", f"✅ Created {len(clips)} clips")
                except Exception as e:
                    yield sse_error(f"Clip creation failed: {e}")
                    return

                # Step 5 — Captions (parallel, optional, non-fatal)
                if add_captions:
                    yield sse_event("status", "📝 Generating & burning captions in parallel…")
                    try:
                        clips = await generate_captions_for_clips(
                            client, llm_api_key, clips, transcript, provider=llm_provider, model=llm_model
                        )
                        ok = sum(1 for c in clips if c.get("has_captions"))
                        if ok == len(clips):
                            yield sse_event("status", f"✅ Captions added to all {len(clips)} clips")
                        else:
                            yield sse_event("status", f"⚠️ Captions added to {ok}/{len(clips)} clips")
                    except Exception as e:
                        yield sse_event("status", f"⚠️ Caption step failed, skipping: {e}")

                # Step 6 — Final result
                yield sse_event("result", {
                    "success":   True,
                    "video_url": video_url,
                    "num_clips": len(clips),
                    "clips":     clips,
                    "message":   f"✅ Successfully created {len(clips)} viral clips!",
                    "note":      "Clips are temporary — download within 1 hour."
                })

    except Exception as e:
        yield sse_error(f"Podcast clip agent error: {e}")
