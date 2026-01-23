"""
LLM Configuration
Configuration settings for all LLM integration points.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class LLMConfig(BaseSettings):
    """Configuration for LLM services."""
    
    # API Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    
    # Model Selection
    llm_extraction_model: str = Field(default="gpt-4o", alias="LLM_EXTRACTION_MODEL")
    llm_routing_model: str = Field(default="gpt-4o-mini", alias="LLM_ROUTING_MODEL")
    llm_synthesis_model: str = Field(default="gpt-4o", alias="LLM_SYNTHESIS_MODEL")
    llm_validation_model: str = Field(default="gpt-4o-mini", alias="LLM_VALIDATION_MODEL")
    llm_relevance_model: str = Field(default="gpt-4o-mini", alias="LLM_RELEVANCE_MODEL")
    llm_justification_model: str = Field(default="gpt-4o", alias="LLM_JUSTIFICATION_MODEL")
    llm_reflection_model: str = Field(default="gpt-4o-mini", alias="LLM_REFLECTION_MODEL")
    
    # Feature Flags
    enable_llm_extraction: bool = Field(default=True, alias="ENABLE_LLM_EXTRACTION")
    enable_llm_validation: bool = Field(default=True, alias="ENABLE_LLM_VALIDATION")
    enable_llm_routing: bool = Field(default=True, alias="ENABLE_LLM_ROUTING")
    enable_llm_synthesis: bool = Field(default=True, alias="ENABLE_LLM_SYNTHESIS")
    enable_llm_relevance: bool = Field(default=True, alias="ENABLE_LLM_RELEVANCE")
    enable_llm_justification: bool = Field(default=True, alias="ENABLE_LLM_JUSTIFICATION")
    enable_llm_reflection: bool = Field(default=True, alias="ENABLE_LLM_REFLECTION")
    
    # Timeouts (seconds)
    extraction_timeout: int = Field(default=60, alias="EXTRACTION_TIMEOUT")
    routing_timeout: int = Field(default=30, alias="ROUTING_TIMEOUT")
    synthesis_timeout: int = Field(default=45, alias="SYNTHESIS_TIMEOUT")
    validation_timeout: int = Field(default=30, alias="VALIDATION_TIMEOUT")
    relevance_timeout: int = Field(default=20, alias="RELEVANCE_TIMEOUT")
    justification_timeout: int = Field(default=30, alias="JUSTIFICATION_TIMEOUT")
    reflection_timeout: int = Field(default=25, alias="REFLECTION_TIMEOUT")
    
    # Batch Sizes
    max_requirements_per_batch: int = Field(default=15, alias="MAX_REQUIREMENTS_PER_BATCH")
    max_projects_for_relevance: int = Field(default=10, alias="MAX_PROJECTS_FOR_RELEVANCE")
    
    # Thresholds
    relevance_threshold: float = Field(default=0.5, alias="RELEVANCE_THRESHOLD")
    validation_confidence_threshold: float = Field(default=0.7, alias="VALIDATION_CONFIDENCE_THRESHOLD")
    routing_confidence_threshold: float = Field(default=0.8, alias="ROUTING_CONFIDENCE_THRESHOLD")
    
    # Chunking Configuration
    max_chunk_size_tokens: int = Field(default=6000, alias="MAX_CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=200, alias="CHUNK_OVERLAP_TOKENS")
    
    # Temperature Settings (0.0 = deterministic)
    extraction_temperature: float = Field(default=0.0, alias="EXTRACTION_TEMPERATURE")
    routing_temperature: float = Field(default=0.0, alias="ROUTING_TEMPERATURE")
    synthesis_temperature: float = Field(default=0.0, alias="SYNTHESIS_TEMPERATURE")
    validation_temperature: float = Field(default=0.0, alias="VALIDATION_TEMPERATURE")
    relevance_temperature: float = Field(default=0.0, alias="RELEVANCE_TEMPERATURE")
    justification_temperature: float = Field(default=0.3, alias="JUSTIFICATION_TEMPERATURE")
    reflection_temperature: float = Field(default=0.2, alias="REFLECTION_TEMPERATURE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global configuration instance
_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """
    Get global LLM configuration instance.
    
    Returns:
        LLM configuration singleton
    """
    global _llm_config
    
    if _llm_config is None:
        _llm_config = LLMConfig()
    
    return _llm_config
