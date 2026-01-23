"""
Parsed Document Model
Standardized output from all document parsers.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class ParsedDocument:
    """Standardized document parsing result."""
    
    # Core content (Required)
    raw_text: str
    normalized_text: str
    
    # Metrics (Required)
    word_count: int
    
    # Parser info (Required)
    parser_used: str  # "docling", "pypdf", "python-docx"
    
    # Parser info (Optional / with defaults)
    parse_method: str = "primary"  # "primary", "fallback", "emergency"
    parse_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Metrics (Optional / with defaults)
    page_count: int = 0
    char_count: int = 0
    
    # Quality metrics (Optional / with defaults)
    language: str = "unknown"
    language_confidence: float = 0.0
    quality_score: float = 0.0
    
    # Metadata (Optional / with defaults)
    metadata: Dict = field(default_factory=dict)
    
    # Optional structured data
    sections: Optional[List[Dict]] = None
    tables: Optional[List[Dict]] = None
    
    # Warnings/errors
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived metrics."""
        if not self.char_count:
            self.char_count = len(self.normalized_text)
        if not self.word_count:
            self.word_count = len(self.normalized_text.split())
    
    @property
    def is_high_quality(self) -> bool:
        """Check if parsing quality is acceptable."""
        return (
            self.quality_score >= 0.7 and
            self.language_confidence >= 0.8 and
            self.word_count > 10
        )
    
    @property
    def used_fallback(self) -> bool:
        """Check if fallback parser was used."""
        return self.parse_method in ["fallback", "emergency"]
