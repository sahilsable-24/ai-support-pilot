import json
import httpx
from groq import Groq
from app.core.config import settings


class LLMError(Exception):
    pass


def _generate_ollama(prompt: str, system: str | None, timeout: float) -> str:
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    try:
        response = httpx.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except httpx.ConnectError:
        raise LLMError(f"Could not connect to Ollama at {settings.ollama_base_url}. Is it running?")
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
        response = client.chat.completions.create(model=settings.groq_model, messages=messages)
    except Exception as e:
        raise LLMError(f"Groq request failed: {e}")
    return response.choices[0].message.content


def generate(prompt: str, system: str | None = None, timeout: float = 120.0) -> str:
    if settings.llm_provider == "groq":
        return _generate_groq(prompt, system, timeout)
    return _generate_ollama(prompt, system, timeout)


def _generate_ollama_stream(prompt: str, system: str | None, timeout: float):
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": True}
    if system:
        payload["system"] = system
    try:
        with httpx.stream("POST", url, json=payload, timeout=timeout) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("response"):
                    yield chunk["response"]
                if chunk.get("done"):
                    break
    except httpx.ConnectError:
        raise LLMError(f"Could not connect to Ollama at {settings.ollama_base_url}. Is it running?")
    except httpx.TimeoutException:
        raise LLMError(f"Ollama did not respond within {timeout} seconds.")
    except httpx.HTTPStatusError as e:
        raise LLMError(f"Ollama returned {e.response.status_code}: {e.response.text}")


def _generate_groq_stream(prompt: str, system: str | None, timeout: float):
    if not settings.groq_api_key:
        raise LLMError("GROQ_API_KEY is not set.")
    client = Groq(api_key=settings.groq_api_key, timeout=timeout)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        stream = client.chat.completions.create(model=settings.groq_model, messages=messages, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        raise LLMError(f"Groq request failed: {e}")


def generate_stream(prompt: str, system: str | None = None, timeout: float = 120.0):
    if settings.llm_provider == "groq":
        yield from _generate_groq_stream(prompt, system, timeout)
    else:
        yield from _generate_ollama_stream(prompt, system, timeout)