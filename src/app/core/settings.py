import os
from typing import List, Literal, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl, ConfigDict, field_validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # --- Environment ---
    ENV: Literal["development", "staging", "production"] = "development"

    # --- Database ---
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # --- OpenAI Configuration ---
    OPENAI_API_KEY: str = Field(..., min_length=1, description="OpenAI API Key")
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- Application Settings ---
    MAX_UPLOAD_SIZE_MB: int = 25
    # Use Any to prevent pydantic from trying to parse comma-separated string as JSON list
    ALLOWED_EXTENSIONS: Any = ["pdf", "docx"]

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",") if ext.strip()]
        if isinstance(v, list):
            return v
        return ["pdf", "docx"]

    # --- Logging ---
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_DIR: str = "logs"
    LOG_RETENTION_DAYS: int = 30

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

# Singleton instance
settings = Settings()
