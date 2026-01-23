"""
Configuration management for RFP Bid Agent
"""

import os
from typing import List, Literal, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


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
    ALLOWED_EXTENSIONS: Any = ["pdf", "docx"]
    
    # --- Parser Configuration ---
    PARSER_PRIMARY: str = "docling"
    PARSER_PDF_FALLBACK: str = "pypdf"
    PARSER_DOCX_FALLBACK: str = "python-docx"
    PARSER_ENABLE_OCR: bool = True
    PARSER_MIN_CONFIDENCE: float = 0.7
    PARSER_EXPECTED_LANGUAGE: str = "en"

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

    # --- Paths ---
    KNOWLEDGE_BASE_PATH: str = "./data/knowledge_base"
    SAMPLE_RFPS_PATH: str = "./data/sample_rfps"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


# Singleton instance
settings = Settings()
