"""
Podcast Clip Agent - Executor
Converts long-form podcasts into viral short-form clips with AI.
"""
import httpx
import os
import tempfile
import re
import subprocess
import shutil
from pathlib import Path
from app.core.sse import sse_event, sse_error
from app.core.config import settings

# Import agent-specific modules
from .downloader import download_video
from .transcriber import transcribe_audio
from .viral_detector import detect_viral_moments
from .clipper import create_clips_from_moments
from .caption_generator import generate_captions_for_clips


def _check_dependencies() -> tuple[bool, list[str]]:
    """
    Verify all required system dependencies are installed.
    
    Returns:
        (success: bool, missing: list[str])
    """
    deps = {
        "yt-dlp": ["yt-dlp", "--version"],
        "ffmpeg": ["ffmpeg", "-version"],
        "ffprobe": ["ffprobe", "-version"]
    }
    
    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=5)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            missing.append(name)
    
    return (len(missing) == 0, missing)


async def execute(prompt: str, keys: dict, language: str = None, options: dict = None):
    """
    Main executor for Podcast Clip Agent.
    
    Args:
        prompt: User's request with video URL
            Examples:
            - "Create clips from https://youtube.com/watch?v=..."
            - "Generate viral clips from this podcast: [URL]"
            - "Extract 3 best moments from [URL]"
        
        keys: {
            "OPENAI_API_KEY": "sk-...",      # For viral moment detection
            "OPENAI_WHISPER_KEY": "sk-..."   # For transcription (can be same key)
        }
        
        language: "en", "es", etc. (for transcript language hint)
        
        options: {
            "num_clips": 3,                    # Number of clips to create (default: 3)
            "max_duration": 60,                # Max clip duration in seconds (default: 60)
            "min_duration": 15,                # Min clip duration in seconds (default: 15)
            "aspect_ratio": "9:16",            # "9:16" (vertical) or "1:1" (square)
            "add_captions": true,              # Add AI-generated captions (default: true)
            "virality_threshold": 7.0          # Min score 1-10 (default: 7.0)
        }
    
    Yields:
        SSE events with status updates and final clips
    """
    try:
        # Check system dependencies first
        deps_ok, missing_deps = _check_dependencies()
        if not deps_ok:
            yield sse_error(
                f"Missing required system dependencies: {', '.join(missing_deps)}. "
                f"Please contact the marketplace administrator to install these packages."
            )
            return
        
        # Extract API keys
        openai_api_key = keys.get("OPENAI_API_KEY")
        whisper_key = keys.get("OPENAI_WHISPER_KEY", openai_api_key)  # Fallback to same key
        
        if not openai_api_key:
            yield sse_error("OPENAI_API_KEY missing (required for viral moment detection)")
            return
        
        if not whisper_key:
            yield sse_error("OPENAI_WHISPER_KEY missing (required for transcription)")
            return
        
        # Extract and validate options
        opts = options or {}
        
        # Validate num_clips (1-10)
        num_clips = opts.get("num_clips", 3)
        num_clips = max(1, min(num_clips, 10))  # Clamp to valid range
        
        # Validate durations (10-180 seconds)
        max_duration = opts.get("max_duration", 60)
        max_duration = max(10, min(max_duration, 180))
        
        min_duration = opts.get("min_duration", 15)
        min_duration = max(5, min(min_duration, 120))
        
        # Ensure min < max
        if min_duration >= max_duration:
            yield sse_error(f"min_duration ({min_duration}s) must be less than max_duration ({max_duration}s)")
            return
        
        # Validate aspect ratio
        aspect_ratio = opts.get("aspect_ratio", "9:16")
        if aspect_ratio not in ["9:16", "1:1", "16:9"]:
            yield sse_error(f"Invalid aspect_ratio '{aspect_ratio}'. Must be '9:16', '1:1', or '16:9'")
            return
        
        add_captions = opts.get("add_captions", True)
        
        # Validate virality threshold (1.0-10.0)
        virality_threshold = opts.get("virality_threshold", 7.0)
        virality_threshold = max(1.0, min(virality_threshold, 10.0))
        
        # Extract video URL from prompt
        video_url = _extract_url(prompt)
        if not video_url:
            yield sse_error("No video URL found in prompt. Provide YouTube link or direct video URL.")
            return
        
        yield sse_event("status", f"🎬 Found video: {video_url}")
        
        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Step 1: Download video
            yield sse_event("status", "⬇️ Downloading video... (this may take 1-2 minutes)")
            
            async with httpx.AsyncClient(timeout=300) as client:
                try:
                    video_file = await download_video(client, video_url, str(temp_path))
                    yield sse_event("status", f"✅ Downloaded: {Path(video_file).name}")
                except Exception as e:
                    yield sse_error(f"Download failed: {str(e)}")
                    return
                
                # Step 2: Transcribe audio
                yield sse_event("status", "🎤 Transcribing audio with Whisper... (1-3 minutes)")
                
                try:
                    transcript = await transcribe_audio(
                        client,
                        whisper_key,
                        video_file,
                        language=language
                    )
                    word_count = len(transcript.get("text", "").split())
                    yield sse_event("status", f"✅ Transcription complete ({word_count} words)")
                except Exception as e:
                    yield sse_error(f"Transcription failed: {str(e)}")
                    return
                
                # Step 3: Detect viral moments with LLM
                yield sse_event("status", f"🤖 Analyzing transcript for top {num_clips} viral moments...")
                
                try:
                    viral_moments = await detect_viral_moments(
                        client,
                        openai_api_key,
                        transcript,
                        num_clips=num_clips,
                        min_duration=min_duration,
                        max_duration=max_duration,
                        threshold=virality_threshold
                    )
                    
                    if not viral_moments:
                        yield sse_error("No viral moments found. Try lowering virality_threshold or processing a different video.")
                        return
                    
                    yield sse_event("status", f"✅ Found {len(viral_moments)} viral moments")
                except Exception as e:
                    yield sse_error(f"Viral detection failed: {str(e)}")
                    return
                
                # Step 4: Create video clips
                yield sse_event("status", f"✂️ Creating {len(viral_moments)} video clips...")
                
                try:
                    clips = await create_clips_from_moments(
                        video_file,
                        viral_moments,
                        str(temp_path),
                        aspect_ratio=aspect_ratio
                    )
                    yield sse_event("status", f"✅ Created {len(clips)} clips")
                except Exception as e:
                    yield sse_error(f"Clip creation failed: {str(e)}")
                    return
                
                # Step 5: Add captions (optional)
                if add_captions:
                    yield sse_event("status", "📝 Generating AI captions for clips...")
                    
                    try:
                        clips_with_captions = await generate_captions_for_clips(
                            client,
                            openai_api_key,
                            clips,
                            transcript
                        )
                        clips = clips_with_captions
                        
                        # Report per-clip caption success
                        success_count = sum(1 for c in clips if c.get("has_captions", False))
                        if success_count == len(clips):
                            yield sse_event("status", f"✅ Captions added to all {len(clips)} clips")
                        else:
                            yield sse_event("status", f"✅ Captions added to {success_count}/{len(clips)} clips")
                    except Exception as e:
                        # Non-fatal, continue without captions
                        yield sse_event("status", f"⚠️ Caption generation failed, continuing without: {str(e)}")
                
                # Step 6: Return final result
                result = {
                    "success": True,
                    "video_url": video_url,
                    "num_clips": len(clips),
                    "clips": clips,
                    "message": f"✅ Successfully created {len(clips)} viral clips!",
                    "note": "Clips are temporary. Download them within 1 hour or they'll be deleted."
                }
                
                yield sse_event("result", result)
    
    except Exception as e:
        yield sse_error(f"Podcast clip agent error: {str(e)}")


def _extract_url(text: str) -> str:
    """Extract video URL from text."""
    # YouTube patterns
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w\-]+)',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    # Generic URL pattern (direct video file)
    url_pattern = r'https?://[^\s]+\.(?:mp4|webm|mkv|avi|mov|m4v)'
    match = re.search(url_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    
    return None
