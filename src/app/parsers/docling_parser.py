"""
Docling-based primary document parser.
Supports PDF, DOCX, and other formats with high fidelity.
"""
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    DOCLING_AVAILABLE = True
except ImportError as e:
    DOCLING_AVAILABLE = False
    logger.warning(f"Docling not available: {e}")

from src.app.parsers.base_parser import BaseParser
from src.app.models.parsed_document import ParsedDocument


class DoclingParser(BaseParser):
    """Primary parser using Docling for high-quality extraction."""
    
    def __init__(self):
        """Initialize Docling converter with PDF and DOCX support."""
        if not DOCLING_AVAILABLE:
            self.converter = None
            return
            
        # Configure pipeline options for PDF
        pdf_options = PdfPipelineOptions(
            do_ocr=True,
            do_table_structure=True
        )
        
        # Initialize converter (handles DOCX automatically in v2.x)
        self.converter = DocumentConverter(
            format_options={
                "pdf": pdf_options
            }
        )

    def supports_format(self, file_path: str) -> bool:
        """Check if file format is supported."""
        if not DOCLING_AVAILABLE:
            return False
            
        ext = file_path.lower().split('.')[-1]
        return ext in ['pdf', 'docx', 'doc', 'pptx', 'html', 'md']

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse document using Docling.
        
        Returns:
            ParsedDocument: Structured parsing result
            
        Raises:
            ImportError: If Docling is not installed
            RuntimeError: If parsing fails
        """
        if not DOCLING_AVAILABLE:
            raise ImportError("Docling not installed")
            
        try:
            logger.info(f"Parsing with Docling: {file_path}")
            start_time = datetime.utcnow()
            
            # Convert document
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Extract text
            raw_text = doc.export_to_markdown()  # Markdown preserves structure better
            
            # Extract metadata
            metadata = {
                "filename": file_path.split('\\')[-1],
                "title": doc.name,
                "page_count": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "origin": doc.origin,
                "creation_time": datetime.utcnow().isoformat()
            }
            
            # Create ParsedDocument (normalization and validation happen later)
            parsed_doc = ParsedDocument(
                raw_text=raw_text,
                normalized_text=raw_text,  # Will be updated by normalizer
                word_count=len(raw_text.split()),
                page_count=metadata["page_count"],
                parser_used="docling",
                parse_method="primary",
                metadata=metadata
            )
            
            logger.info(f"Docling success: {parsed_doc.word_count} words")
            return parsed_doc
            
        except Exception as e:
            logger.error(f"Docling parsing failed: {e}")
            raise RuntimeError(f"Docling failed to parse {file_path}: {e}") from e
