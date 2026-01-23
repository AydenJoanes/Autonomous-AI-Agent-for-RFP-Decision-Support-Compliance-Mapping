
from pydantic import BaseModel
from typing import Optional

class RFPMetadata(BaseModel):
    """Metadata for an RFP document."""
    filename: str
    file_path: str
    file_size: int
    page_count: Optional[int] = None
    upload_date: Optional[str] = None
    content_type: Optional[str] = None
