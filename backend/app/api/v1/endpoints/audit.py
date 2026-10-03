import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.finding import RiskLevel
from app.schemas.finding import DocumentFindingsSummary, FindingWithSource
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.services.finding_service import FindingService
from app.analysis.engine import default_risk_engine
from app.rag.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_findings_summary(
    db: Session,
    document_id: uuid.UUID,
    min_risk: Optional[RiskLevel] = None,
) -> DocumentFindingsSummary:
    """Helper to assemble DocumentFindingsSummary with preserved clause sources."""
    findings = FindingService.list_by_document(db, document_id, min_risk=min_risk)

    findings_with_source = []
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    for f in findings:
        clause = f.clause or ClauseService.get(db, f.clause_id)
        findings_with_source.append(
            FindingWithSource(
                finding_id=f.finding_id,
                clause_id=f.clause_id,
                category=f.category,
                risk_level=f.risk_level,
                explanation=f.explanation,
                validated=f.validated,
                created_at=f.created_at,
                clause_order=clause.clause_order if clause else 0,
                clause_text=clause.clause_text if clause else "",
                section=clause.section if clause else None,
                page_number=clause.page_number if clause else None,
                paragraph_number=clause.paragraph_number if clause else None,
            )
        )
        if f.risk_level == RiskLevel.CRITICAL:
            critical_count += 1
        elif f.risk_level == RiskLevel.HIGH:
            high_count += 1
        elif f.risk_level == RiskLevel.MEDIUM:
            medium_count += 1
        elif f.risk_level == RiskLevel.LOW:
            low_count += 1

    return DocumentFindingsSummary(
        document_id=document_id,
        total_findings=len(findings_with_source),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        findings=findings_with_source,
    )


@router.post(
    "/documents/{document_id}/audit",
    response_model=DocumentFindingsSummary,
    status_code=status.HTTP_200_OK,
    summary="Execute automated risk detection rule engine on document",
    description=(
        "Scans all clauses in the document across 7 fine-print risk categories "
        "(auto-renewal, hidden fees, arbitration, data sharing, cancellation, "
        "data retention, liability). Persists new findings without duplicates."
    ),
)
def audit_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DocumentFindingsSummary:
    try:
        default_risk_engine.analyze_document(db, document_id)
        return _build_findings_summary(db, document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error auditing document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automated risk audit failed: {str(e)}",
        )


@router.get(
    "/documents/{document_id}/findings",
    response_model=DocumentFindingsSummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all risk findings with source clauses for a document",
    description="Fetches stored risk findings augmented with verbatim clause text and location metadata.",
)
def get_document_findings(
    document_id: uuid.UUID,
    risk_level: Optional[RiskLevel] = None,
    db: Session = Depends(get_db),
) -> DocumentFindingsSummary:
    doc = DocumentService.get(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return _build_findings_summary(db, document_id, min_risk=risk_level)
