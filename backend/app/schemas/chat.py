import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentAskRequest(BaseModel):
    """Payload for asking a question about a specific document."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question or inquiry concerning the legal document",
        examples=["Does this service sell my personal data to third parties?"],
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of most relevant clauses to retrieve for context",
    )


class ChatQuestionRequest(DocumentAskRequest):
    """Payload when document_id is passed in the request body."""
    document_id: uuid.UUID = Field(
        ...,
        description="UUID of the ingested document to query",
    )


class RetrievedClauseSource(BaseModel):
    """Source reference and content for a retrieved clause."""
    model_config = ConfigDict(from_attributes=True)

    clause_id: uuid.UUID
    clause_order: int
    section: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    clause_text: str


class DocumentAskResponse(BaseModel):
    """Complete response for document-grounded legal Q&A."""
    model_config = ConfigDict(from_attributes=True)

    chat_id: uuid.UUID
    document_id: uuid.UUID
    question: str
    answer: str
    sources: List[RetrievedClauseSource]
    provider: str
    model: str
    created_at: datetime
