from src.app.parsers.docling_parser import DoclingParser
from src.app.parsers.pypdf_parser import PyPDFParser
from src.app.parsers.docx_parser import DocxParser
from loguru import logger
import os

class DocumentParserFactory:
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        return os.path.splitext(file_path)[1].lower()

    @staticmethod
    def create_parser(file_path: str):
        """
        Returns the primary parser (DoclingParser).
        """
        ext = DocumentParserFactory.get_file_extension(file_path)
        logger.info(f"Selecting parser for {ext}")
        return DoclingParser()

    @staticmethod
    def parse_with_fallback(file_path: str) -> str:
        ext = DocumentParserFactory.get_file_extension(file_path)
        logger.info(f"Attempting parse with fallback chain for {file_path}")
        
        try:
            # Try primary
            primary = DoclingParser()
            markdown = primary.parse(file_path)
            logger.info("Primary parser success")
            return markdown
        except Exception as e:
            logger.warning(f"Docling failed: {e}")
            
            # Fallback logic
            fallback_error = None
            try:
                if ext == '.pdf':
                    fallback = PyPDFParser()
                    logger.info("Attempting fallback: PyPDFParser")
                    markdown = fallback.parse(file_path)
                    logger.info("Fallback parser success")
                    return markdown
                elif ext in ['.docx', '.doc']:
                    fallback = DocxParser()
                    logger.info("Attempting fallback: DocxParser")
                    markdown = fallback.parse(file_path)
                    logger.info("Fallback parser success")
                    return markdown
            except Exception as fb_e:
                fallback_error = fb_e
                logger.error(f"Fallback failed: {fb_e}")

            # If we reach here, either no fallback for this extension or fallback failed
            error_msg = f"All parsers failed for {file_path}. Primary error: {e}"
            if fallback_error:
                error_msg += f". Fallback error: {fallback_error}"
            
            logger.error(error_msg)
            raise RuntimeError(error_msg)
