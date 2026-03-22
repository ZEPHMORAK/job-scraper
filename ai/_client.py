"""
ai/_client.py — Direct OpenAI API client using httpx (no pydantic_core needed).
Replaces the official openai SDK to avoid the pydantic-core dependency.
"""
import httpx
import json
import config

OPENAI_BASE = "https://api.openai.com/v1"


def chat(messages: list[dict], model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 500) -> str:
    """
    Call the OpenAI Chat Completions API.
    Returns the assistant message content as a string.
    Raises on HTTP errors or API errors.
    """
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{OPENAI_BASE}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        error_body = ""
        try:
            error_body = e.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise RuntimeError(f"OpenAI API error {e.response.status_code}: {error_body}") from e
    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {e}") from e
