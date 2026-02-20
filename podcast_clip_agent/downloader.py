"""
Video Downloader - yt-dlp wrapper
Downloads from YouTube or direct video URLs
"""
import httpx
import subprocess
import os
from pathlib import Path


async def download_video(client: httpx.AsyncClient, url: str, output_dir: str) -> str:
    """
    Download video from URL using yt-dlp.
    
    Args:
        client: httpx.AsyncClient (unused, for consistency)
        url: YouTube URL or direct video URL
        output_dir: Directory to save downloaded video
    
    Returns:
        Path to downloaded video file
    
    Raises:
        RuntimeError: If download fails
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Output template
    output_template = str(output_path / "video.%(ext)s")
    
    # yt-dlp command
    cmd = [
        "yt-dlp",
        "--format", "best[ext=mp4]/best",  # Prefer MP4
        "--output", output_template,
        "--no-playlist",                   # Single video only
        "--quiet",                         # Suppress output
        "--no-warnings",
        url
    ]
    
    try:
        # Run yt-dlp
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            raise RuntimeError(f"yt-dlp failed: {error_msg}")
        
        # Find downloaded file
        video_files = list(output_path.glob("video.*"))
        if not video_files:
            raise RuntimeError("yt-dlp completed but no video file found")
        
        return str(video_files[0])
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Download timeout (>3 minutes). Video may be too large or network is slow.")
    except FileNotFoundError:
        raise RuntimeError("yt-dlp not installed. Install with: pip install yt-dlp")
    except Exception as e:
        raise RuntimeError(f"Download error: {str(e)}")


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Duration in seconds
    """
    import json
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Failed to get video duration: {str(e)}")
