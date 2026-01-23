"""
RFP Parser Tool - Agent tool for parsing RFP documents
"""

from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from loguru import logger
from src.app.parsers.document_parser_factory import DocumentParserFactory

class RFPParserInput(BaseModel):
    file_path: str = Field(..., description="Absolute path to the RFP file (PDF or DOCX)")

class RFPParserTool(BaseTool):
    name: str = "rfp_parser"
    description: str = "Parses RFP documents (PDF/DOCX) and converts to clean markdown text. Handles complex layouts and tables."
    args_schema: Type[BaseModel] = RFPParserInput

    def _run(self, file_path: str) -> str:
        """Execute the tool."""
        logger.info(f"[TOOL] RFP Parser started for {file_path}")
        
        try:
            text = DocumentParserFactory.parse_with_fallback(file_path)
            logger.info(f"DEBUG: Parsed text length: {len(text) if text else 0}")
            
            clean_text = text # DocumentParserFactory.clean_text(text) doesn't exist, just use text
            
            word_count = len(clean_text.split())
            logger.info(f"[TOOL] RFP Parser complete: {word_count} words")
            
            return clean_text
            
        except Exception as e:
            logger.error(f"[TOOL] RFP Parser failed: {e}")
            return f"Error parsing RFP: {str(e)}"
