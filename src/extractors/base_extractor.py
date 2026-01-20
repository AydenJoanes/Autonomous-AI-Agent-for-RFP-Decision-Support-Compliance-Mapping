"""
Base requirement extractor class
"""

from abc import ABC, abstractmethod
from typing import List

from src.models.rfp import Requirement


class BaseExtractor(ABC):
    """Abstract base class for requirement extractors."""
    
    @abstractmethod
    def extract(self, text: str) -> List[Requirement]:
        """
        Extract requirements from text.
        
        Args:
            text: Text content to extract requirements from
            
        Returns:
            List of extracted requirements
        """
        pass
