import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.document import SourceType, DocumentStatus


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=1, description="Raw terms of service, privacy policy, or contract text")
    title: Optional[str] = Field(default=None, max_length=255, description="Optional title or identifier")


class ClauseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clause_id: uuid.UUID
    page_number: Optional[int] = Field(description="1-based page number for PDF, NULL for non-page docs")
    paragraph_number: Optional[int] = Field(description="1-based paragraph number for DOCX/TXT/text")
    section: Optional[str] = Field(description="Detected section or heading title if available")
    clause_text: str = Field(description="Original unedited text of the clause")
    clause_order: int = Field(description="0-based sequential ordering index")


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    filename: Optional[str]
    source_type: SourceType
    status: DocumentStatus
    total_clauses: int
    clauses: List[ClauseSummary]
    message: str = "Document successfully ingested, normalized, segmented, and stored in PostgreSQL."
