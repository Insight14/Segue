import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime: str = Field(default="application/pdf", max_length=100)


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    upload_url: str
    s3_key: str


class DocumentProcessResponse(BaseModel):
    document_id: uuid.UUID
    status: str = "parsing"
    message: str = "Document queued for processing"


class DocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    mime: str
    status: str
    parsed_text: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
