"""
Viral Moment Detector - Uses LLM to find engaging clips
Analyzes transcript and identifies the most shareable moments
"""
import httpx
import json


async def detect_viral_moments(
    client: httpx.AsyncClient,
    api_key: str,
    transcript: dict,
    num_clips: int = 3,
    min_duration: int = 15,
    max_duration: int = 60,
    threshold: float = 7.0
) -> list:
    """
    Detect viral moments in transcript using LLM.
    
    Args:
        client: httpx.AsyncClient
        api_key: OpenAI API key
        transcript: {"text": "...", "segments": [{start, end, text}, ...]}
        num_clips: Number of clips to extract
        min_duration: Minimum clip duration (seconds)
        max_duration: Maximum clip duration (seconds)
        threshold: Minimum virality score 1-10
    
    Returns:
        [
            {
                "start_time": 45.2,
                "end_time": 68.5,
                "text": "Transcript of this segment...",
                "score": 8.5,
                "reason": "Hook: surprising fact about AI",
                "title": "AI Can Do WHAT?!"
            },
            ...
        ]
    """
    segments = transcript.get("segments", [])
    if not segments:
        raise ValueError("Transcript has no segments")
    
    # Build prompt for LLM
    system_prompt = f"""You are an expert video editor who identifies viral-worthy moments in podcasts.

Analyze the transcript and find the top {num_clips} most engaging clips for social media (TikTok/YouTube Shorts).

Look for:
- Surprising facts or revelations
- Emotional moments (funny, inspiring, shocking)
- Controversial or debate-worthy statements
- Actionable advice or tips
- Storytelling with clear beginning/middle/end

Each clip must be {min_duration}-{max_duration} seconds long.

Return JSON array (no markdown, just valid JSON):
[
  {{
    "start_time": 45.2,
    "end_time": 68.5,
    "text": "Exact transcript of this segment",
    "score": 8.5,
    "reason": "Why this is viral-worthy",
    "title": "Catchy title for the clip"
  }}
]

Only include clips with score >= {threshold}/10."""

    # Prepare transcript text with timestamps
    transcript_text = _format_transcript_for_llm(segments, max_chars=8000)
    
    user_prompt = f"""Transcript:\n\n{transcript_text}\n\nFind the top {num_clips} viral moments (JSON array only, no other text):"""
    
    # Call LLM
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=60
        )
        
        if response.status_code != 200:
            error_detail = response.text[:200]
            if response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key")
            else:
                raise RuntimeError(f"OpenAI API error ({response.status_code}): {error_detail}")
        
        data = response.json()
        result_text = data["choices"][0]["message"]["content"]
        
        # Parse JSON response
        moments = _parse_llm_response(result_text)
        
        # Filter by threshold
        moments = [m for m in moments if m.get("score", 0) >= threshold]
        
        # Limit to num_clips
        moments = moments[:num_clips]
        
        return moments
    
    except httpx.TimeoutException:
        raise RuntimeError("LLM timeout. Try a shorter transcript.")
    except Exception as e:
        raise RuntimeError(f"Viral detection error: {str(e)}")


def _format_transcript_for_llm(segments: list, max_chars: int = 8000) -> str:
    """Format transcript with timestamps for LLM analysis."""
    lines = []
    total_chars = 0
    
    for seg in segments:
        start = seg.get("start", 0)
        text = seg.get("text", "").strip()
        
        if not text:
            continue
        
        line = f"[{_format_time(start)}] {text}"
        
        if total_chars + len(line) > max_chars:
            break
        
        lines.append(line)
        total_chars += len(line)
    
    return "\n".join(lines)


def _format_time(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def _parse_llm_response(text: str) -> list:
    """Parse LLM JSON response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        # Extract JSON from code block
        lines = text.split("\n")
        json_lines = []
        in_code_block = False
        
        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block or not line.startswith("```"):
                json_lines.append(line)
        
        text = "\n".join(json_lines).strip()
    
    # Parse JSON
    try:
        moments = json.loads(text)
        if not isinstance(moments, list):
            raise ValueError("Response is not a JSON array")
        return moments
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {str(e)}")
