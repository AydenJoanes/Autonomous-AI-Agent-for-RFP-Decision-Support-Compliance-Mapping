"""
Base parser class for RFP documents
"""

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.rfp import RFPDocument


class BaseParser(ABC):
    """Abstract base class for RFP document parsers."""
    
    @abstractmethod
    def parse(self, file_path: Path) -> RFPDocument:
        """
        Parse an RFP document.
        
        Args:
            file_path: Path to the RFP document
            
        Returns:
            Parsed RFPDocument object
        """
        pass
    
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """
        Check if parser supports the given file format.
        
        Args:
            file_path: Path to the RFP document
            
        Returns:
            True if parser can handle the file format
        """
        pass
