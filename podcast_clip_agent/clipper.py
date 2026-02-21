"""
Video Clipper - FFmpeg wrapper for creating clips
Cuts video segments and reformats for social media.
All FFmpeg calls are async and clips are created in parallel.
"""
import asyncio
import os
from pathlib import Path
import uuid


async def create_clips_from_moments(
    video_path: str,
    moments: list,
    output_dir: str,
    aspect_ratio: str = "9:16"
) -> list:
    """
    Create video clips from viral moments in parallel.

    Args:
        video_path: Path to source video
        moments: List of moments from viral_detector
        output_dir: Directory to save clips
        aspect_ratio: "9:16" (vertical), "1:1" (square), or "16:9" (horizontal)

    Returns:
        [
            {
                "clip_id": "abc123",
                "file_path": "/path/to/clip.mp4",
                "start_time": 45.2,
                "end_time": 68.5,
                "duration": 23.3,
                "title": "AI Can Do WHAT?!",
                "score": 8.5,
                "file_size_mb": 12.5
            },
            ...
        ]
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Determine dimensions based on aspect ratio
    dimensions = {
        "9:16": (1080, 1920),  # Vertical (TikTok / YouTube Shorts)
        "1:1":  (1080, 1080),  # Square (Instagram)
        "16:9": (1920, 1080),  # Horizontal (YouTube)
    }
    width, height = dimensions.get(aspect_ratio, (1080, 1920))

    # Build tasks for valid moments only
    tasks = []
    meta = []
    for i, moment in enumerate(moments):
        start_time = moment.get("start_time", 0)
        end_time = moment.get("end_time", 0)
        duration = end_time - start_time
        if duration <= 0:
            print(f"⚠️  Skipping clip {i + 1}: invalid duration ({start_time:.1f}s → {end_time:.1f}s)")
            continue

        clip_id = str(uuid.uuid4())[:8]
        output_file = str(output_path / f"clip_{i + 1}_{clip_id}.mp4")

        tasks.append(_create_clip_async(video_path, output_file, start_time, duration, width, height))
        meta.append((clip_id, output_file, moment, i))

    # Run all clip creations in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    clips = []
    for result, (clip_id, output_file, moment, i) in zip(results, meta):
        if isinstance(result, Exception):
            print(f"Failed to create clip {i + 1}: {result}")
            continue

        if not os.path.exists(output_file):
            continue

        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        clips.append({
            "clip_id": clip_id,
            "file_path": output_file,
            "start_time": moment.get("start_time", 0),
            "end_time": moment.get("end_time", 0),
            "duration": moment.get("end_time", 0) - moment.get("start_time", 0),
            "title": moment.get("title", f"Clip {i + 1}"),
            "score": moment.get("score", 0),
            "reason": moment.get("reason", ""),
            "text": moment.get("text", ""),
            "file_size_mb": round(file_size_mb, 2)
        })

    return clips


async def _create_clip_async(
    input_video: str,
    output_file: str,
    start_time: float,
    duration: float,
    width: int,
    height: int
):
    """
    Create a single video clip using FFmpeg (async, non-blocking).

    Args:
        input_video: Source video path
        output_file: Output clip path
        start_time: Start time in seconds
        duration: Clip duration in seconds
        width: Output width
        height: Output height
    """
    # Scale + letterbox/pillarbox to target aspect ratio with black padding
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),    # Seek before input (fast)
        "-i", input_video,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",              # Quality: 18=best, 28=smallest
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart", # Web-optimized (moov atom at front)
        output_file
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise RuntimeError("Clip creation timeout (>2 minutes)")

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")[:500] if stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg clip creation failed: {error_msg}")

        if not os.path.exists(output_file):
            raise RuntimeError("FFmpeg completed but output file not created")

    except FileNotFoundError:
        raise RuntimeError("FFmpeg not installed")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Clip creation error: {str(e)}")
