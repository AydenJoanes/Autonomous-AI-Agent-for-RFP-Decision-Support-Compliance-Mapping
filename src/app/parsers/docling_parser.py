from src.app.parsers.base_parser import BaseParser
from docling.document_converter import DocumentConverter
from loguru import logger
import os

class DoclingParser(BaseParser):
    
    def supports_format(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.pdf', '.docx', '.doc']

    def parse(self, file_path: str) -> str:
        logger.info(f"Starting Docling parse for {file_path}")
        
        try:
            self.validate_file(file_path)
            
            # Initialize Docling converter
            # Default behavior preserves table structures and converts to markdown
            converter = DocumentConverter()
            
            result = converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()
            
            # Clean excessive whitespace
            # Simple cleanup: replace multiple newlines with max 2, strip
            cleaned_content = "\n".join([line.rstrip() for line in markdown_content.splitlines()])
            while "\n\n\n" in cleaned_content:
                cleaned_content = cleaned_content.replace("\n\n\n", "\n\n")
            cleaned_content = cleaned_content.strip()
            
            word_count = len(cleaned_content.split())
            logger.info(f"Docling parse complete: {word_count} words")
            
            return cleaned_content

        except Exception as e:
            logger.exception(f"Error parsing file {file_path}")
            raise RuntimeError(f"Failed to parse {file_path}: {str(e)}") from e
