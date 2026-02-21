"""
Caption Generator - Creates word-level captions for clips.
Generates SRT files from transcript timestamps and burns them into video.
FFmpeg calls are async and captions are burned in parallel.
"""
import asyncio
import httpx
import os
import sys
from pathlib import Path


async def generate_captions_for_clips(
    client: httpx.AsyncClient,
    api_key: str,
    clips: list,
    transcript: dict,
    provider: str = "openai",
    model: str = None
) -> list:
    """
    Generate and burn captions into video clips (in parallel).

    Args:
        client: httpx.AsyncClient (reserved for future AI caption styling)
        api_key: LLM API key (reserved for future use)
        clips: List of clip dictionaries
        transcript: Full transcript with segments
        provider: LLM provider (reserved for future use)
        model: LLM model (reserved for future use)
        clips: List of clip dictionaries
        transcript: Full transcript with segments

    Returns:
        Updated clips list with has_captions flag
    """
    segments = transcript.get("segments", [])

    async def _process_clip(clip: dict) -> dict:
        try:
            clip_segments = _extract_clip_segments(
                segments,
                clip["start_time"],
                clip["end_time"]
            )

            if not clip_segments:
                clip["has_captions"] = False
                return clip

            # Write SRT alongside the clip
            srt_file = str(Path(clip["file_path"]).with_suffix(".srt"))
            _create_srt_file(clip_segments, srt_file)

            # Output captioned file
            captioned_file = str(
                Path(clip["file_path"]).with_stem(
                    Path(clip["file_path"]).stem + "_captions"
                )
            )

            await _burn_captions_async(clip["file_path"], srt_file, captioned_file)

            # Swap original with captioned version
            os.remove(clip["file_path"])
            os.rename(captioned_file, clip["file_path"])

            # Clean up SRT
            if os.path.exists(srt_file):
                os.remove(srt_file)

            clip["has_captions"] = True

        except Exception as e:
            clip["has_captions"] = False
            clip["caption_error"] = str(e)

        return clip

    # Process all clips in parallel
    updated = await asyncio.gather(*[_process_clip(clip) for clip in clips])
    return list(updated)


def _extract_clip_segments(segments: list, start_time: float, end_time: float) -> list:
    """Extract transcript segments that overlap with the clip's timeframe."""
    clip_segments = []

    for seg in segments:
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)

        # Include segment if it overlaps with the clip window
        if seg_end >= start_time and seg_start <= end_time:
            clip_segments.append({
                "start": max(0.0, seg_start - start_time),
                "end": min(end_time - start_time, seg_end - start_time),
                "text": seg.get("text", "").strip()
            })

    return clip_segments


def _create_srt_file(segments: list, output_path: str):
    """
    Write an SRT subtitle file from clip-relative segments.

    Args:
        segments: List of {start, end, text} (times relative to clip start)
        output_path: Output .srt file path
    """
    lines = []

    for i, seg in enumerate(segments, 1):
        text = seg["text"]
        if not text:
            continue

        lines.append(str(i))
        lines.append(f"{_srt_timestamp(seg['start'])} --> {_srt_timestamp(seg['end'])}")
        lines.append(text)
        lines.append("")  # Blank line separator

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


async def _burn_captions_async(video_file: str, srt_file: str, output_file: str):
    """
    Burn SRT captions into video using FFmpeg (async, non-blocking).
    Handles Windows and Linux path separators correctly.

    Args:
        video_file: Input video path
        srt_file: SRT subtitle file path
        output_file: Output video path with burned-in captions
    """
    abs_srt = os.path.abspath(srt_file)

    # FFmpeg subtitles filter requires forward slashes and escaped colons on Windows
    if sys.platform == "win32":
        # Convert  C:\path\to\file.srt  →  C\:/path/to/file.srt
        abs_srt_ffmpeg = abs_srt.replace("\\", "/").replace(":", "\\:")
    else:
        # On Linux/macOS, just escape colons and spaces
        abs_srt_ffmpeg = abs_srt.replace(":", "\\:").replace(" ", "\\ ")

    style = (
        "FontSize=8,PrimaryColour=&Hffffff,"
        "OutlineColour=&H000000,BorderStyle=3,Outline=2,"
        "Shadow=0,MarginV=20,Alignment=2"
    )

    vf = f"subtitles='{abs_srt_ffmpeg}':force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", vf,
        "-c:v", "libx264",      # Re-encode to burn in subtitles
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",         # Copy audio unchanged
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
            raise RuntimeError("Caption burning timeout (>2 minutes)")

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")[:500] if stderr else "Unknown error"
            raise RuntimeError(f"Caption burning failed: {error_msg}")

        if not os.path.exists(output_file):
            raise RuntimeError("FFmpeg completed but captioned file not created")

    except FileNotFoundError:
        raise RuntimeError("FFmpeg not installed")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Caption burning error: {str(e)}")
