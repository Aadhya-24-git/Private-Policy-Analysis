import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.finding import RiskLevel


class FindingBase(BaseModel):
    category: str = Field(max_length=100, description="Risk classification category (e.g. auto_renewal, arbitration)")
    risk_level: RiskLevel = Field(description="Assessed severity level (low, medium, high, critical)")
    explanation: str = Field(min_length=1, description="Reasoning and neutral summary of risk")
    validated: bool = Field(default=False, description="Manual or algorithmic validation flag")


class FindingCreate(FindingBase):
    clause_id: uuid.UUID = Field(description="Parent clause UUID")


class FindingUpdate(BaseModel):
    category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    explanation: Optional[str] = None
    validated: Optional[bool] = None


class FindingResponse(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    finding_id: uuid.UUID
    clause_id: uuid.UUID
    created_at: datetime


class FindingWithSource(FindingResponse):
    """Finding augmented with the verbatim source clause and metadata."""
    clause_order: int
    clause_text: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None


class DocumentFindingsSummary(BaseModel):
    """Aggregate risk profile summary for an audited document."""
    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[FindingWithSource]
