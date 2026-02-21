"""
Multi-LLM Service - Universal LLM client for OpenAI, Anthropic, and Google
Provides unified interface for viral moment detection with best-in-class models.
"""
import httpx
import json


# Model configurations
DEFAULT_MODELS = {
    "openai": "gpt-4o",              # Better than gpt-4o-mini
    "anthropic": "claude-sonnet-4",  # Claude Sonnet 4
    "google": "gemini-2.0-flash-thinking-exp-1219"  # Gemini with thinking
}


async def call_llm(
    client: httpx.AsyncClient,
    provider: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    max_tokens: int = 16000,
    temperature: float = 0.3
) -> str:
    """
    Universal LLM caller supporting OpenAI, Anthropic, and Google.

    Args:
        client: httpx.AsyncClient
        provider: "openai", "anthropic", or "google"
        api_key: API key for the provider
        system_prompt: System instructions
        user_prompt: User message
        model: Model name (optional, uses DEFAULT_MODELS if not provided)
        max_tokens: Max response tokens
        temperature: Creativity (0.0-1.0)

    Returns:
        LLM response text

    Raises:
        RuntimeError: On API errors
    """
    provider = provider.lower()
    
    if not model:
        model = DEFAULT_MODELS.get(provider)
        if not model:
            raise RuntimeError(f"Unknown provider: {provider}. Use 'openai', 'anthropic', or 'google'")

    if provider == "openai":
        return await _call_openai(client, api_key, system_prompt, user_prompt, model, max_tokens, temperature)
    elif provider == "anthropic":
        return await _call_anthropic(client, api_key, system_prompt, user_prompt, model, max_tokens, temperature)
    elif provider == "google":
        return await _call_google(client, api_key, system_prompt, user_prompt, model, max_tokens, temperature)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")


async def _call_openai(
    client: httpx.AsyncClient,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    temperature: float
) -> str:
    """OpenAI API caller."""
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=90
        )

        if response.status_code != 200:
            error_detail = response.text[:200]
            if response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key")
            else:
                raise RuntimeError(f"OpenAI API error ({response.status_code}): {error_detail}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        raise RuntimeError("OpenAI API timeout")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {str(e)}")


async def _call_anthropic(
    client: httpx.AsyncClient,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    temperature: float
) -> str:
    """Anthropic (Claude) API caller."""
    try:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=90
        )

        if response.status_code != 200:
            error_detail = response.text[:200]
            if response.status_code == 401:
                raise RuntimeError("Invalid Anthropic API key")
            else:
                raise RuntimeError(f"Anthropic API error ({response.status_code}): {error_detail}")

        data = response.json()
        # Claude returns array of content blocks
        content = data["content"]
        if isinstance(content, list):
            return "".join([block.get("text", "") for block in content if block.get("type") == "text"])
        return str(content)

    except httpx.TimeoutException:
        raise RuntimeError("Anthropic API timeout")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Anthropic error: {str(e)}")


async def _call_google(
    client: httpx.AsyncClient,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    temperature: float
) -> str:
    """Google (Gemini) API caller."""
    try:
        # Gemini combines system + user into single prompt
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [
                    {"parts": [{"text": combined_prompt}]}
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            },
            timeout=90
        )

        if response.status_code != 200:
            error_detail = response.text[:200]
            if response.status_code == 401 or response.status_code == 403:
                raise RuntimeError("Invalid Google API key")
            else:
                raise RuntimeError(f"Google API error ({response.status_code}): {error_detail}")

        data = response.json()
        
        # Handle safety blocks
        if "candidates" not in data or not data["candidates"]:
            raise RuntimeError("Google API blocked the request (safety filters)")
        
        candidate = data["candidates"][0]
        if "content" not in candidate:
            raise RuntimeError("Google API returned no content")
        
        parts = candidate["content"].get("parts", [])
        return "".join([part.get("text", "") for part in parts])

    except httpx.TimeoutException:
        raise RuntimeError("Google API timeout")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Google error: {str(e)}")
