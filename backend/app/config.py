from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Required
    OPENAI_API_KEY: str = ""

    # LLM settings
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0

    # Embedding settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Pipeline tuning
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    CHAT_HISTORY_TURNS: int = 10
    MAX_FILE_SIZE_MB: int = 20
    MAX_DOCS_PER_SESSION: int = 10

    # Storage paths
    UPLOADS_DIR: str = "uploads"
    VECTOR_STORE_PATH: str = "chroma_db"
    DATABASE_URL: str = "rag_chatbot.db"

    # Server
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
