"""
Language Validator
Validates extracted text quality and detects language.
"""
from dataclasses import dataclass, field
from typing import List
from loguru import logger

try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available")


@dataclass
class ValidationResult:
    language: str
    confidence: float
    quality_score: float
    warnings: List[str] = field(default_factory=list)


class LanguageValidator:
    """Validates extracted text quality."""
    
    def __init__(self, expected_language: str = "en"):
        self.expected_language = expected_language
        
    def validate(self, text: str) -> ValidationResult:
        """
        Validate text quality and languages.
        """
        if not text or len(text.strip()) < 50:
            return ValidationResult(
                language="unknown",
                confidence=0.0,
                quality_score=0.0,
                warnings=["Text too short for validation"]
            )

        lang = "unknown"
        conf = 0.0
        warnings = []
        quality = 1.0  # Start perfect, deduct points
        
        # 1. Detect language
        if LANGDETECT_AVAILABLE:
            try:
                # Get probabilities
                langs = detect_langs(text[:2000])  # Use first 2k chars for speed
                if langs:
                    primary = langs[0]
                    lang = primary.lang
                    conf = primary.prob
                    
                    if lang != self.expected_language:
                        warnings.append(f"Detected language '{lang}' differs from expected '{self.expected_language}'")
                        quality -= 0.2
            except LangDetectException:
                warnings.append("Language detection failed")
                quality -= 0.1
        else:
            warnings.append("Language detection library missing")
        
        # 2. Check density of special characters (garbage detection)
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        density = special_chars / len(text)
        if density > 0.3:  # More than 30% special chars
            warnings.append("High special character density (potential extraction noise)")
            quality -= 0.3
            
        # 3. Check for REPLACEMENT CHARACTER ()
        if '\ufffd' in text:
            count = text.count('\ufffd')
            warnings.append(f"Found {count} replacement characters (encoding issues)")
            quality -= 0.1 * min(count, 5)
            
        return ValidationResult(
            language=lang,
            confidence=conf,
            quality_score=max(0.0, quality),
            warnings=warnings
        )
