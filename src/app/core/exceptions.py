class RFPException(Exception):
    """Base exception for the RFP Agent application."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class RFPNotFoundException(RFPException):
    """Raised when a specific RFP document or record cannot be found."""
    pass

class AnalysisFailedException(RFPException):
    """Raised when the analysis or extraction process fails for a document."""
    pass

class DatabaseConnectionError(RFPException):
    """Raised when the application cannot connect to the database."""
    pass

class InvalidFileTypeError(RFPException):
    """Raised when an uploaded file type is not supported."""
    pass
