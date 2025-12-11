from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL_NAME: str = "qwen3:8b"
    OLLAMA_EMBED_MODEL_NAME: str = "embeddinggemma"

    # Qdrant
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str | None = None

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Paths (inside container)
    JSON_INPUT_DIR: str = "/app/results/recognition_json"
    CHUNKS_DIR: str = "/app/chunks"

    # Collections
    QDRANT_COLLECTION_CLS: str = "cls_ogata"
    QDRANT_COLLECTION_DS: str = "ds_ogata"
    QDRANT_COLLECTION_NL: str = "nl_khalil"

    # Chunking
    MAX_TOKENS_PER_CHUNK: int = 512
    PAGES_PER_CHUNK: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
