"""
Parser Settings Accessor
Utility to get parser configuration safely.
"""
from config.settings import settings

def get_parser_config():
    """Get parser configuration dictionary."""
    return {
        "primary": settings.PARSER_PRIMARY,
        "pdf_fallback": settings.PARSER_PDF_FALLBACK,
        "docx_fallback": settings.PARSER_DOCX_FALLBACK,
        "enable_ocr": settings.PARSER_ENABLE_OCR,
        "min_confidence": settings.PARSER_MIN_CONFIDENCE,
        "expected_language": settings.PARSER_EXPECTED_LANGUAGE
    }
