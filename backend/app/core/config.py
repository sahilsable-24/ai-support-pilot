from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    evidence_threshold: float = -9.5
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_provider: str = "local"
    gemini_api_key: str | None = None
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dim: int = 768
    rerank_enabled: bool = True
    hybrid_evidence_threshold: float = 0.3

settings = Settings()