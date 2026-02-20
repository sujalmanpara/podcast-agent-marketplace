"""Mock LLM module for local testing"""
import httpx
import json


async def call_llm(
    client: httpx.AsyncClient,
    api_key: str,
    system: str,
    user: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    provider: str = "openai"
) -> str:
    """Mock LLM call - actually calls OpenAI API"""
    
    if provider == "openai":
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        print(f"\n🤖 Calling OpenAI {model}...")
        print(f"   System: {system[:100]}...")
        print(f"   User: {user[:100]}...")
        
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        print(f"   Response: {content[:200]}...")
        
        return content
    
    else:
        raise NotImplementedError(f"Provider {provider} not implemented in mock")
