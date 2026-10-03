import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.document import SourceType, DocumentStatus


class DocumentBase(BaseModel):
    filename: Optional[str] = Field(default=None, max_length=255, description="Filename if uploaded from file")
    source_type: SourceType = Field(description="Format of the uploaded document (pdf, docx, txt, text, web)")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Current processing status")


class DocumentCreate(BaseModel):
    filename: Optional[str] = Field(default=None, max_length=255)
    source_type: SourceType
    original_text: str = Field(min_length=1, description="Raw text content extracted from or provided in document")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)


class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    upload_time: datetime
    original_text: str
    clause_count: Optional[int] = None
