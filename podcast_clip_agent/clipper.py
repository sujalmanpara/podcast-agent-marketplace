"""
Video Clipper - FFmpeg wrapper for creating clips
Cuts video segments and reformats for social media
"""
import subprocess
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
    Create video clips from viral moments.
    
    Args:
        video_path: Path to source video
        moments: List of moments from viral_detector
        output_dir: Directory to save clips
        aspect_ratio: "9:16" (vertical) or "1:1" (square)
    
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
    
    clips = []
    
    # Determine dimensions based on aspect ratio
    if aspect_ratio == "9:16":
        width, height = 1080, 1920  # Vertical (TikTok/Shorts)
    elif aspect_ratio == "1:1":
        width, height = 1080, 1080  # Square (Instagram)
    else:
        width, height = 1920, 1080  # Horizontal (default)
    
    for i, moment in enumerate(moments):
        clip_id = str(uuid.uuid4())[:8]
        output_file = output_path / f"clip_{i+1}_{clip_id}.mp4"
        
        start_time = moment.get("start_time", 0)
        end_time = moment.get("end_time", 0)
        duration = end_time - start_time
        
        if duration <= 0:
            continue
        
        try:
            # Extract and reformat clip
            _create_clip(
                video_path,
                str(output_file),
                start_time,
                duration,
                width,
                height
            )
            
            # Get file size
            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            
            clips.append({
                "clip_id": clip_id,
                "file_path": str(output_file),
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "title": moment.get("title", f"Clip {i+1}"),
                "score": moment.get("score", 0),
                "reason": moment.get("reason", ""),
                "text": moment.get("text", ""),
                "file_size_mb": round(file_size_mb, 2)
            })
        
        except Exception as e:
            # Log error but continue with other clips
            print(f"Failed to create clip {i+1}: {str(e)}")
            continue
    
    return clips


def _create_clip(
    input_video: str,
    output_file: str,
    start_time: float,
    duration: float,
    width: int,
    height: int
):
    """
    Create a single video clip using FFmpeg.
    
    Args:
        input_video: Source video path
        output_file: Output clip path
        start_time: Start time in seconds
        duration: Clip duration in seconds
        width: Output width
        height: Output height
    """
    # FFmpeg video filter for aspect ratio conversion
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),  # Start time
        "-i", input_video,
        "-t", str(duration),      # Duration
        "-vf", vf,                # Video filter (resize + pad)
        "-c:v", "libx264",        # Video codec
        "-preset", "fast",        # Encoding speed
        "-crf", "23",             # Quality (lower = better, 18-28 recommended)
        "-c:a", "aac",            # Audio codec
        "-b:a", "128k",           # Audio bitrate
        "-movflags", "+faststart", # Web optimization
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per clip
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            raise RuntimeError(f"FFmpeg clip creation failed: {error_msg}")
        
        if not os.path.exists(output_file):
            raise RuntimeError("FFmpeg completed but output file not created")
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Clip creation timeout (>2 minutes)")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not installed")
    except Exception as e:
        raise RuntimeError(f"Clip creation error: {str(e)}")
