import logging
import os
import sys
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0

    # Embedding
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Pipeline tuning
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    CHAT_HISTORY_TURNS: int = 10

    # Limits
    MAX_FILE_SIZE_MB: int = 20
    MAX_DOCS_PER_SESSION: int = 10

    # Storage
    VECTOR_STORE: str = "chromadb"
    VECTOR_STORE_PATH: str = "./data/chroma"
    UPLOADS_DIR: str = "./uploads"
    DATABASE_URL: str = "rag_chatbot.db"

    # Server
    LOG_LEVEL: str = "INFO"

    # ── Field validators ────────────────────────────────────────────────────

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        allowed = {"openai", "anthropic"}
        if v.lower() not in allowed:
            raise ValueError(
                f"LLM_PROVIDER must be one of {allowed!r}; got {v!r}"
            )
        return v.lower()

    @field_validator("VECTOR_STORE")
    @classmethod
    def validate_vector_store(cls, v: str) -> str:
        allowed = {"chromadb", "faiss"}
        if v.lower() not in allowed:
            raise ValueError(
                f"VECTOR_STORE must be one of {allowed!r}; got {v!r}"
            )
        return v.lower()

    @field_validator("TOP_K")
    @classmethod
    def clamp_top_k(cls, v: int) -> int:
        lo, hi = 1, 20
        if v < lo or v > hi:
            clamped = max(lo, min(hi, v))
            logging.warning(f"TOP_K={v} out of range [1, 20]; using {clamped}.")
            return clamped
        return v

    @field_validator("LLM_TEMPERATURE")
    @classmethod
    def clamp_temperature(cls, v: float) -> float:
        lo, hi = 0.0, 2.0
        if v < lo or v > hi:
            clamped = max(lo, min(hi, v))
            logging.warning(f"LLM_TEMPERATURE={v} out of range [0.0, 2.0]; using {clamped}.")
            return clamped
        return v

    @field_validator("MAX_FILE_SIZE_MB")
    @classmethod
    def clamp_file_size(cls, v: int) -> int:
        lo, hi = 1, 100
        if v < lo or v > hi:
            clamped = max(lo, min(hi, v))
            logging.warning(f"MAX_FILE_SIZE_MB={v} out of range [1, 100]; using {clamped}.")
            return clamped
        return v

    @field_validator("CHUNK_SIZE")
    @classmethod
    def clamp_chunk_size(cls, v: int) -> int:
        lo, hi = 100, 2000
        if v < lo or v > hi:
            clamped = max(lo, min(hi, v))
            logging.warning(f"CHUNK_SIZE={v} out of range [100, 2000]; using {clamped}.")
            return clamped
        return v

    # ── Model validators ────────────────────────────────────────────────────

    @model_validator(mode="after")
    def fix_chunk_overlap(self) -> "Settings":
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            corrected = self.CHUNK_SIZE // 10
            logging.warning(
                f"CHUNK_OVERLAP={self.CHUNK_OVERLAP} >= CHUNK_SIZE={self.CHUNK_SIZE}; "
                f"setting CHUNK_OVERLAP={corrected}."
            )
            self.CHUNK_OVERLAP = corrected
        return self

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return self

    @model_validator(mode="after")
    def validate_paths(self) -> "Settings":
        for path_attr in ("VECTOR_STORE_PATH", "UPLOADS_DIR"):
            path = getattr(self, path_attr)
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as exc:
                raise ValueError(
                    f"{path_attr}={path!r} cannot be created: {exc}"
                ) from exc
            if not os.access(path, os.W_OK):
                raise ValueError(
                    f"{path_attr}={path!r} is not writable"
                )
        return self


# ── Startup log ─────────────────────────────────────────────────────────────

def log_startup_config(settings: Settings) -> None:
    def redact(key: str) -> str:
        if not key or len(key) < 4:
            return "****"
        return f"...{key[-4:]}"

    logger = logging.getLogger("config")
    logger.info(
        f"[CONFIG] LLM Provider: {settings.LLM_PROVIDER} | "
        f"Model: {settings.LLM_MODEL} | "
        f"Embedding: {settings.EMBEDDING_MODEL}"
    )
    logger.info(
        f"[CONFIG] Chunk Size: {settings.CHUNK_SIZE} | "
        f"Overlap: {settings.CHUNK_OVERLAP} | "
        f"Top-k: {settings.TOP_K} | "
        f"Max Docs: {settings.MAX_DOCS_PER_SESSION} | "
        f"Max File MB: {settings.MAX_FILE_SIZE_MB}"
    )
    logger.info(
        f"[CONFIG] Vector Store: {settings.VECTOR_STORE} | "
        f"Storage: {settings.VECTOR_STORE_PATH}"
    )
    if settings.OPENAI_API_KEY:
        logger.info(f"[CONFIG] OpenAI API Key: {redact(settings.OPENAI_API_KEY)}")
    if settings.ANTHROPIC_API_KEY:
        logger.info(f"[CONFIG] Anthropic API Key: {redact(settings.ANTHROPIC_API_KEY)}")


# ── Settings singleton ───────────────────────────────────────────────────────

@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── Startup validation (module-level — fails fast before app creation) ───────

def _validate_settings_at_startup() -> None:
    """Run once at import time to catch fatal misconfigurations immediately."""
    try:
        get_settings()
    except Exception as e:
        # Pydantic ValidationError or any ValueError from validators
        from pydantic import ValidationError
        if isinstance(e, ValidationError):
            for err in e.errors():
                logging.critical(f"[CONFIG ERROR] {err['msg']}")
        else:
            logging.critical(f"[CONFIG ERROR] {e}")
        sys.exit(1)
