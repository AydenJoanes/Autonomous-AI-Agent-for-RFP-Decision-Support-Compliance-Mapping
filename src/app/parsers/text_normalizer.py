"""
Text Normalizer
Cleans and standardizes extracted text.
"""
import re
from loguru import logger

class TextNormalizer:
    """Cleans extracted text for LLM processing."""
    
    def normalize(self, text: str) -> str:
        """
        Normalize text by cleaning whitespace, fixing line breaks, etc.
        """
        if not text:
            return ""
            
        # 1. Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 2. Fix hyphenated words split across lines (e.g., "implemen-\ntation")
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        
        # 3. Remove excessive blank lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 4. Collapse multiple spaces (except newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 5. Remove control characters (except tabs and newlines)
        text = "".join(ch for ch in text if ch == '\n' or ch == '\t' or ch >= ' ')
        
        # 6. Basic markdown cleanup if needed (Docling output is MD)
        # (Optional specific markdown cleanup can go here)
        
        return text.strip()
