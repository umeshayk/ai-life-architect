from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Life Architect"
    database_url: str = "postgresql+psycopg2://postgres:root@localhost:5432/ai_life_architect"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "llama3.2"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    upload_dir: str = "uploads"
    cors_origins: list[str] | str = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
