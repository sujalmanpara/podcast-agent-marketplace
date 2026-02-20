"""
Caption Generator - Creates word-level captions for clips
Uses transcript timestamps to generate SRT files and burns them into video
"""
import httpx
import subprocess
import os
from pathlib import Path


async def generate_captions_for_clips(
    client: httpx.AsyncClient,
    api_key: str,
    clips: list,
    transcript: dict
) -> list:
    """
    Generate and burn captions into video clips.
    
    Args:
        client: httpx.AsyncClient
        api_key: OpenAI API key (unused for now, for future AI caption styling)
        clips: List of clip dictionaries
        transcript: Full transcript with segments
    
    Returns:
        Updated clips list with caption_file paths
    """
    segments = transcript.get("segments", [])
    
    for clip in clips:
        try:
            # Extract relevant transcript segments for this clip
            clip_segments = _extract_clip_segments(
                segments,
                clip["start_time"],
                clip["end_time"]
            )
            
            if not clip_segments:
                continue
            
            # Generate SRT file
            srt_file = str(Path(clip["file_path"]).with_suffix(".srt"))
            _create_srt_file(clip_segments, srt_file, clip["start_time"])
            
            # Burn captions into video
            output_file = str(Path(clip["file_path"]).with_stem(
                Path(clip["file_path"]).stem + "_captions"
            ))
            
            _burn_captions(clip["file_path"], srt_file, output_file)
            
            # Replace original with captioned version
            os.remove(clip["file_path"])
            os.rename(output_file, clip["file_path"])
            
            # Clean up SRT file
            if os.path.exists(srt_file):
                os.remove(srt_file)
            
            clip["has_captions"] = True
        
        except Exception as e:
            # Non-fatal, continue without captions
            clip["has_captions"] = False
            clip["caption_error"] = str(e)
    
    return clips


def _extract_clip_segments(segments: list, start_time: float, end_time: float) -> list:
    """Extract transcript segments that fall within clip timeframe."""
    clip_segments = []
    
    for seg in segments:
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        
        # Check if segment overlaps with clip
        if seg_end >= start_time and seg_start <= end_time:
            # Adjust timestamps relative to clip start
            clip_segments.append({
                "start": max(0, seg_start - start_time),
                "end": min(end_time - start_time, seg_end - start_time),
                "text": seg.get("text", "").strip()
            })
    
    return clip_segments


def _create_srt_file(segments: list, output_path: str, offset: float = 0):
    """
    Create SRT subtitle file from segments.
    
    Args:
        segments: List of {start, end, text}
        output_path: Path to output .srt file
        offset: Time offset (for adjusting to clip start)
    """
    lines = []
    
    for i, seg in enumerate(segments, 1):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        
        if not text:
            continue
        
        # SRT format
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}")
        lines.append(text)
        lines.append("")  # Blank line between subtitles
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _burn_captions(video_file: str, srt_file: str, output_file: str):
    """
    Burn SRT captions into video using FFmpeg.
    
    Args:
        video_file: Input video path
        srt_file: SRT subtitle file path
        output_file: Output video path with captions
    """
    # Escape SRT path for FFmpeg (handle spaces and special chars)
    escaped_srt = srt_file.replace('\\', '/').replace(':', '\\:').replace("'", "'\\\\\\''")
    
    # Subtitle style (white text, black outline, bottom-center)
    style = (
        "FontSize=24,PrimaryColour=&Hffffff,"
        "OutlineColour=&H000000,BorderStyle=3,Outline=2,"
        "Shadow=0,MarginV=40,Alignment=2"
    )
    
    vf = f"subtitles='{escaped_srt}':force_style='{style}'"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", vf,
        "-c:a", "copy",  # Copy audio (no re-encoding)
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            raise RuntimeError(f"Caption burning failed: {error_msg}")
        
        if not os.path.exists(output_file):
            raise RuntimeError("FFmpeg completed but output file not created")
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Caption burning timeout")
    except Exception as e:
        raise RuntimeError(f"Caption burning error: {str(e)}")
