"""
Helper utility functions
"""


def normalize_text(text: str) -> str:
    """
    Normalize text content.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # TODO: Implement text normalization
    return text.strip()


def extract_file_extension(file_path: str) -> str:
    """
    Extract file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension
    """
    return file_path.split('.')[-1].lower()
