"""
Configuration management for RFP Bid Agent
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    openai_api_key: Optional[str] = None
    azure_api_key: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    
    # Database
    database_url: str = "sqlite:///./data/rfp_agent.db"
    
    # Model Configuration
    model_name: str = "gpt-4"
    temperature: float = 0.7
    
    # Paths
    knowledge_base_path: str = "./data/knowledge_base"
    sample_rfps_path: str = "./data/sample_rfps"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
