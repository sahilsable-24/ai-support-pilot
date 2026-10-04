import httpx
from app.core.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed_local(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(texts).tolist()


def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_embedding_model}:batchEmbedContents"
    headers = {"x-goog-api-key": settings.gemini_api_key, "Content-Type": "application/json"}
    payload = {
        "requests": [
            {
                "model": f"models/{settings.gemini_embedding_model}",
                "content": {"parts": [{"text": text}]},
                "taskType": task_type,
                "outputDimensionality": settings.gemini_embedding_dim,
            }
            for text in texts
        ]
    }

    response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()
    data = response.json()

    return [item["values"] for item in data["embeddings"]]


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if settings.embedding_provider == "gemini":
        return _embed_gemini(texts, task_type)
    return _embed_local(texts)


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    return embed_texts([text], task_type=task_type)[0]