from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int
    ingestion_status: str
    created_at: datetime