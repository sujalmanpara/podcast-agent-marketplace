"""
Audio Transcriber - OpenAI Whisper API wrapper
Transcribes video/audio to text with timestamps
"""
import httpx
import subprocess
import os
from pathlib import Path


async def transcribe_audio(
    client: httpx.AsyncClient,
    api_key: str,
    video_path: str,
    language: str = None
) -> dict:
    """
    Transcribe video/audio using OpenAI Whisper API.
    
    Args:
        client: httpx.AsyncClient
        api_key: OpenAI API key
        video_path: Path to video/audio file
        language: Language code (e.g., "en", "es") - optional
    
    Returns:
        {
            "text": "Full transcript...",
            "segments": [
                {"start": 0.0, "end": 5.2, "text": "Hello..."},
                ...
            ]
        }
    
    Raises:
        RuntimeError: If transcription fails
    """
    # Extract audio from video (Whisper API has 25MB limit)
    audio_file = await _extract_audio(video_path)
    
    try:
        # Prepare multipart upload
        with open(audio_file, "rb") as f:
            files = {
                "file": (Path(audio_file).name, f, "audio/mpeg"),
                "model": (None, "whisper-1"),
                "response_format": (None, "verbose_json"),  # Includes timestamps
            }
            
            if language:
                files["language"] = (None, language)
            
            # Call Whisper API
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                timeout=180  # 3 minute timeout
            )
        
        if response.status_code != 200:
            error_detail = response.text[:200]
            if response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key for Whisper")
            elif response.status_code == 413:
                raise RuntimeError("Audio file too large (>25MB). Try a shorter video.")
            else:
                raise RuntimeError(f"Whisper API error ({response.status_code}): {error_detail}")
        
        data = response.json()
        
        # Format response
        return {
            "text": data.get("text", ""),
            "segments": data.get("segments", []),
            "language": data.get("language", language or "en")
        }
    
    except httpx.TimeoutException:
        raise RuntimeError("Whisper API timeout. Video may be too long (try <10 minutes).")
    except Exception as e:
        raise RuntimeError(f"Transcription error: {str(e)}")
    finally:
        # Clean up temp audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)


async def _extract_audio(video_path: str) -> str:
    """
    Extract audio from video as MP3 (for Whisper API).
    
    Args:
        video_path: Path to video file
    
    Returns:
        Path to extracted audio file
    """
    audio_path = str(Path(video_path).with_suffix(".mp3"))
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",  # No video
        "-acodec", "libmp3lame",
        "-b:a", "128k",  # Compress to reduce file size
        "-ar", "16000",  # 16kHz sample rate (Whisper recommends)
        audio_path
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
            raise RuntimeError(f"Audio extraction failed: {error_msg}")
        
        if not os.path.exists(audio_path):
            raise RuntimeError("FFmpeg completed but audio file not created")
        
        return audio_path
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Audio extraction timeout (>2 minutes)")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not installed. Install it to process videos.")
    except Exception as e:
        raise RuntimeError(f"Audio extraction error: {str(e)}")
