"""
Unified Document Parser (Entry Point)
Routes documents to appropriate parsers with comprehensive fallback chains.
"""
import os
from loguru import logger
from typing import Optional, List, Dict

from src.app.models.parsed_document import ParsedDocument
from src.app.parsers.docling_parser import DoclingParser
from src.app.parsers.pypdf_parser import PyPDFParser
from src.app.parsers.docx_parser import DocxParser
from src.app.parsers.text_normalizer import TextNormalizer
from src.app.parsers.language_validator import LanguageValidator


class UnifiedParser:
    """
    Main entry point for document parsing.
    Orchestrates parsing sequence: Docling -> Fallback -> Normalize -> Validate
    """
    
    def __init__(self):
        """Initialize parsers and validators."""
        self.docling_parser = DoclingParser()
        self.pdf_fallback = PyPDFParser()
        self.docx_fallback = DocxParser()
        
        self.normalizer = TextNormalizer()
        self.validator = LanguageValidator()
    
    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse any supported document with fallback chain.
        """
        logger.info(f"Parsing document: {file_path}")
        
        try:
            # Step 1: Try Primary Parser (Docling)
            try:
                document = self.docling_parser.parse(file_path)
            except Exception as e:
                logger.warning(f"Primary parser (Docling) failed: {e}. Attempting fallback...")
                document = self._fallback_parse(file_path)
            
            # Step 2: Normalize Text
            document.normalized_text = self.normalizer.normalize(document.raw_text)
            
            # Step 3: Validate Language & Quality
            validation_result = self.validator.validate(document.normalized_text)
            document.language = validation_result.language
            document.language_confidence = validation_result.confidence
            document.quality_score = validation_result.quality_score
            document.warnings.extend(validation_result.warnings)
            
            # Log results
            logger.info(f"Parsing complete. Method: {document.parse_method}, "
                        f"Words: {document.word_count}, Quality: {document.quality_score:.2f}")
            
            return document
            
        except Exception as e:
            logger.error(f"All parsing attempts failed for {file_path}: {e}")
            raise RuntimeError(f"Failed to parse document: {e}") from e

    def _fallback_parse(self, file_path: str) -> ParsedDocument:
        """Execute fallback parsing based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        raw_text = ""
        parser_name = "unknown"
        
        try:
            if ext == '.pdf':
                raw_text = self.pdf_fallback.parse(file_path)
                parser_name = "pypdf"
            elif ext in ['.docx', '.doc']:
                raw_text = self.docx_fallback.parse(file_path)
                parser_name = "python-docx"
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()
                parser_name = "text_io"
            else:
                raise ValueError(f"No fallback parser for extension: {ext}")
                
            return ParsedDocument(
                raw_text=raw_text,
                normalized_text=raw_text,
                word_count=len(raw_text.split()),
                page_count=0,  # Fallback often doesn't give page counts easily
                parser_used=parser_name,
                parse_method="fallback",
                metadata={"fallback_reason": "primary_failed"}
            )
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
            raise
