from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="DocuMind AI API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    postgres_user: str = Field(default="documind", alias="POSTGRES_USER")
    postgres_password: str = Field(default="documind", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="documind", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: str = Field(
        default="postgresql+psycopg://documind:documind@localhost:5432/documind",
        alias="DATABASE_URL",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    storage_dir: str = Field(default="./data/uploads", alias="STORAGE_DIR")
    max_upload_size_bytes: int = Field(default=10_485_760, alias="MAX_UPLOAD_SIZE_BYTES")
    allowed_upload_content_types: str = Field(
        default="application/pdf,text/plain", alias="ALLOWED_UPLOAD_CONTENT_TYPES"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
