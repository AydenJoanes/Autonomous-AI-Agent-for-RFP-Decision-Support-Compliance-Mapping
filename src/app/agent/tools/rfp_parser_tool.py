"""
RFP Parser Tool - Agent tool for parsing RFP documents
"""

from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from loguru import logger
from src.app.parsers.unified_parser import UnifiedParser

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
            parser = UnifiedParser()
            document = parser.parse(file_path)
            
            logger.info(f"DEBUG: Parsed text length: {len(document.normalized_text) if document.normalized_text else 0}")
            logger.info(f"[TOOL] RFP Parser complete: {document.word_count} words")
            
            return document.normalized_text
            
        except Exception as e:
            logger.error(f"[TOOL] RFP Parser failed: {e}")
            return f"Error parsing RFP: {str(e)}"
