from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Life Architect API"
    app_env: str
    app_host: str = "0.0.0.0"
    app_port: int = 8004
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    enable_docs: bool = True
    database_url: str
    redis_url: str
    cors_allowed_origins: str
    ollama_base_url: AnyHttpUrl
    ollama_model: str
    worker_enabled: bool = True
    worker_queue: str = "default"
    request_timeout_seconds: int = 15

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(sorted(allowed))}")
        return value

    def get_cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
