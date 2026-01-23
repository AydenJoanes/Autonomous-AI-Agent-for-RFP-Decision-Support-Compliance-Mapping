from src.app.parsers.base_parser import BaseParser
import pypdf
from loguru import logger
import os

class PyPDFParser(BaseParser):
    
    def supports_format(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext == '.pdf'

    def parse(self, file_path: str) -> str:
        logger.info(f"Using PyPDF fallback parser for {file_path}")
        self.validate_file(file_path)
        
        try:
            text_content = []
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    try:
                        text_content.append(page.extract_text())
                    except Exception as page_e:
                        logger.warning(f"Failed to extract text from page {i}: {page_e}")
                        text_content.append("") # Empty string for failed page
            
            # Join pages with newlines
            full_text = "\n\n".join(text_content)
            
            # Basic markdown formatting - treating it as plain text mostly, 
            # maybe just ensuring paragraphs are separated.
            return full_text
            
        except Exception as e:
            logger.error(f"PyPDF parsing failed for {file_path}: {e}")
            raise RuntimeError(f"PyPDF failed to parse {file_path}: {str(e)}") from e
