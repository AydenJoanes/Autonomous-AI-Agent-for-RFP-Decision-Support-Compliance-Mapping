from abc import ABC, abstractmethod
import os

class BaseParser(ABC):
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse the file and return markdown content."""
        pass

    @abstractmethod
    def supports_format(self, file_path: str) -> bool:
        """Check if the file format is supported."""
        pass

    def validate_file(self, file_path: str):
        """
        Validate file exists, is readable, and is within size limits.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")
            
        # Check if readable
        try:
            with open(file_path, 'rb') as f:
                pass
        except IOError:
            raise PermissionError(f"File is not readable: {file_path}")

        # Check file size < 10MB (10 * 1024 * 1024 bytes)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:
            raise ValueError(f"File size exceeds 10MB limit: {file_size} bytes")
