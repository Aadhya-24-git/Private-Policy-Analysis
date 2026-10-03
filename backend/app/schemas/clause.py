import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ClauseBase(BaseModel):
    page_number: Optional[int] = Field(default=None, description="Page number where clause appears")
    paragraph_number: Optional[int] = Field(default=None, description="Paragraph number on page/section")
    section: Optional[str] = Field(default=None, max_length=255, description="Document section header")
    clause_text: str = Field(min_length=1, description="Raw clause or paragraph text")
    clause_order: int = Field(ge=0, description="Sequential position index within document")


class ClauseCreate(ClauseBase):
    document_id: uuid.UUID = Field(description="Parent document UUID")
    embedding: Optional[List[float]] = Field(default=None, description="Optional pgvector 1536-dim vector")


class ClauseUpdate(BaseModel):
    clause_text: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    embedding: Optional[List[float]] = None


class ClauseResponse(ClauseBase):
    model_config = ConfigDict(from_attributes=True)

    clause_id: uuid.UUID
    document_id: uuid.UUID
    embedding: Optional[List[float]] = None
