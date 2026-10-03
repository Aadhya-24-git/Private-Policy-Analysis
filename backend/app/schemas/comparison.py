import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ClauseSourceInfo(BaseModel):
    """Source reference and verbatim text for a policy clause."""
    model_config = ConfigDict(from_attributes=True)

    clause_id: uuid.UUID
    clause_order: int
    section: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    clause_text: str


class ModifiedClauseComparison(BaseModel):
    """A matched clause pair exhibiting meaningful textual or semantic modifications."""
    model_config = ConfigDict(from_attributes=True)

    old_clause: ClauseSourceInfo
    new_clause: ClauseSourceInfo
    similarity_score: float = Field(ge=0.0, le=1.0)
    change_type: str = "modified"
    explanation: Optional[str] = None


class AddedClauseComparison(BaseModel):
    """A newly introduced clause appearing in the new policy with no old counterpart."""
    model_config = ConfigDict(from_attributes=True)

    new_clause: ClauseSourceInfo
    change_type: str = "added"
    explanation: Optional[str] = None


class RemovedClauseComparison(BaseModel):
    """An omitted clause appearing in the old policy that was excised from the new policy."""
    model_config = ConfigDict(from_attributes=True)

    old_clause: ClauseSourceInfo
    change_type: str = "removed"
    explanation: Optional[str] = None


class PolicyCompareRequest(BaseModel):
    """Payload to compare two stored policy documents."""
    old_document_id: uuid.UUID = Field(description="UUID of the baseline/previous policy document")
    new_document_id: uuid.UUID = Field(description="UUID of the revised/current policy document")
    explain_changes: bool = Field(default=True, description="Whether to generate neutral AI explanations for changes")


class PolicyCompareSummary(BaseModel):
    """High-level metrics summary of the comparative analysis."""
    total_old_clauses: int
    total_new_clauses: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    overview: str


class PolicyCompareResponse(BaseModel):
    """Complete comparative audit report between two policy versions."""
    model_config = ConfigDict(from_attributes=True)

    old_document_id: uuid.UUID
    new_document_id: uuid.UUID
    old_document_name: str
    new_document_name: str
    summary: PolicyCompareSummary
    modified_clauses: List[ModifiedClauseComparison]
    added_clauses: List[AddedClauseComparison]
    removed_clauses: List[RemovedClauseComparison]
    unchanged_count: int
