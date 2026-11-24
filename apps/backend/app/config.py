from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Server
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    backend_reload: bool = Field(default=False)

    # CORS
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    # Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="open_analyst")
    postgres_user: str = Field(default="open_analyst")
    postgres_password: str = Field(default="changeme")
    database_url: str = Field(default="")

    @computed_field
    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Upload limits
    max_upload_size_mb: int = Field(default=25)
    max_dataset_rows: int = Field(default=100_000)
    max_dataset_columns: int = Field(default=200)
    upload_dir: str = Field(default="uploads")

    # Preview limits
    preview_limit_default: int = Field(default=100)
    preview_limit_max: int = Field(default=500)

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
