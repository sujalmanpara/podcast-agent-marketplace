"""
Viral Moment Detector - Uses GPT-4o-mini to find the most engaging clips.
Analyzes transcript segments and returns ranked, shareable moments.
"""
import httpx
import json
import re


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

    # Expanded to 50 000 chars — gpt-4o-mini has a 128k context window
    transcript_text = _format_transcript_for_llm(segments, max_chars=50_000)

    user_prompt = (
        f"Transcript:\n\n{transcript_text}\n\n"
        f"Find the top {num_clips} viral moments (JSON array only, no other text):"
    )

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

        moments = _parse_llm_response(result_text)

        # Apply virality threshold and cap at requested count
        moments = [m for m in moments if m.get("score", 0) >= threshold]
        moments = moments[:num_clips]

        return moments

    except httpx.TimeoutException:
        raise RuntimeError("LLM timeout. Try a shorter transcript.")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Viral detection error: {str(e)}")


def _format_transcript_for_llm(segments: list, max_chars: int = 50_000) -> str:
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
    """
    Parse LLM JSON response, handling markdown code blocks and mixed content.
    Tries direct parse → strip code fence → regex array extraction.
    """
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block or not line.startswith("```"):
                inner.append(line)
        text = "\n".join(inner).strip()

    # Attempt 1: direct parse
    try:
        moments = json.loads(text)
        if isinstance(moments, list):
            return moments
        raise ValueError("Response is not a JSON array")
    except json.JSONDecodeError:
        pass

    # Attempt 2: extract first [...] array from mixed text
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            moments = json.loads(json_match.group(0))
            if isinstance(moments, list):
                return moments
        except json.JSONDecodeError:
            pass

    # Give up with a helpful error
    preview = text[:200] + "..." if len(text) > 200 else text
    raise RuntimeError(
        f"LLM returned invalid JSON. Response preview: {preview}\n\n"
        f"Expected JSON array format: [{{'start_time': ..., 'end_time': ..., ...}}]"
    )
