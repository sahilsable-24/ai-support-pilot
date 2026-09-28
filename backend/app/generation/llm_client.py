import httpx
from app.core.config import settings


class LLMError(Exception):
    pass


def generate(prompt: str, system:str | None = None,timeout: float = 120.0) -> str:
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