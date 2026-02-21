"""
Video Downloader - yt-dlp wrapper
Downloads from YouTube or direct video URLs (fully async, non-blocking).
"""
import asyncio
import json
import os
from pathlib import Path


async def download_video(url: str, output_dir: str) -> str:
    """
    Download video from URL using yt-dlp (async, non-blocking).

    Args:
        url: YouTube URL or direct video URL
        output_dir: Directory to save downloaded video

    Returns:
        Path to downloaded video file

    Raises:
        RuntimeError: If download fails
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_template = str(output_path / "video.%(ext)s")

    cmd = [
        "python", "-m", "yt_dlp",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--extractor-args", "youtube:player_client=android",
        "--output", output_template,
        "--no-playlist",
        url
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise RuntimeError("Download timeout (>3 minutes). Video may be too large or network is slow.")

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")[:500] if stderr else "Unknown error"
            raise RuntimeError(f"yt-dlp failed: {error_msg}")

        # Find downloaded file
        video_files = list(output_path.glob("video.*"))
        if not video_files:
            raise RuntimeError("yt-dlp completed but no video file found")

        return str(video_files[0])

    except FileNotFoundError:
        raise RuntimeError("yt-dlp not installed. Install with: pip install yt-dlp")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Download error: {str(e)}")


async def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe (async).

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
        info = json.loads(stdout.decode("utf-8"))
        return float(info["format"]["duration"])
    except asyncio.TimeoutError:
        raise RuntimeError("ffprobe timed out getting video duration")
    except Exception as e:
        raise RuntimeError(f"Failed to get video duration: {str(e)}")
