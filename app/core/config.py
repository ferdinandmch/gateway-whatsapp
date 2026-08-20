from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_PORT: int = 8000
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    HTTP_TIMEOUT: int = 30
    N8N_FORWARD_TIMEOUT: int = 5

    DATABASE_URL: str
    REDIS_URL: str
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str
    WEBHOOK_SECRET: str
    API_KEY_SALT: str
    ADMIN_TOKEN: str
    N8N_DEFAULT_WEBHOOK_URL: str
    WEBHOOK_BASE_URL: str = "http://host.docker.internal:8000"

    @field_validator("APP_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("APP_PORT must be between 1 and 65535")
        return v

    @field_validator("HTTP_TIMEOUT")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("HTTP_TIMEOUT must be positive")
        return v

    @field_validator("N8N_FORWARD_TIMEOUT")
    @classmethod
    def validate_n8n_forward_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("N8N_FORWARD_TIMEOUT must be positive")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must start with postgresql+asyncpg://")
        return v


_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
