import httpx
from groq import Groq
from app.core.config import settings


class LLMError(Exception):
    pass


def _generate_ollama(prompt: str, system: str | None, timeout: float) -> str:
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        response = httpx.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except httpx.ConnectError:
        raise LLMError(
            f"Could not connect to Ollama at {settings.ollama_base_url}. Is it running?"
        )
    except httpx.TimeoutException:
        raise LLMError(f"Ollama did not respond within {timeout} seconds.")
    except httpx.HTTPStatusError as e:
        raise LLMError(f"Ollama returned {e.response.status_code}: {e.response.text}")

    return response.json()["response"]


def _generate_groq(prompt: str, system: str | None, timeout: float) -> str:
    if not settings.groq_api_key:
        raise LLMError("GROQ_API_KEY is not set.")

    client = Groq(api_key=settings.groq_api_key, timeout=timeout)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
        )
    except Exception as e:
        raise LLMError(f"Groq request failed: {e}")

    return response.choices[0].message.content


def generate(prompt: str, system: str | None = None, timeout: float = 120.0) -> str:
    if settings.llm_provider == "groq":
        return _generate_groq(prompt, system, timeout)
    return _generate_ollama(prompt, system, timeout)