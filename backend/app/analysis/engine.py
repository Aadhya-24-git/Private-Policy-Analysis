import logging
import uuid
from typing import List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from app.models.document import DocumentStatus
from app.models.finding import Finding
from app.schemas.finding import FindingCreate
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.services.finding_service import FindingService
from app.analysis.base import BaseRiskDetector, DetectionResult
from app.analysis.detectors import (
    AutoRenewalDetector,
    HiddenFeesDetector,
    ArbitrationDetector,
    DataSharingDetector,
    CancellationDetector,
    DataRetentionDetector,
    LiabilityDetector,
)
from app.rag.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class RiskAnalysisEngine:
    """
    Deterministic rule-based risk detection engine for policy clauses.
    Orchestrates the 7 specialized category detectors, enforces duplicate prevention,
    links findings directly to clause_id, and preserves verbatim source text.
    """

    def __init__(self, detectors: Optional[List[BaseRiskDetector]] = None):
        self.detectors: List[BaseRiskDetector] = detectors or [
            AutoRenewalDetector(),
            HiddenFeesDetector(),
            ArbitrationDetector(),
            DataSharingDetector(),
            CancellationDetector(),
            DataRetentionDetector(),
            LiabilityDetector(),
        ]

    def analyze_clause_text(self, clause_text: str) -> List[DetectionResult]:
        """
        Execute all registered detectors against a single clause text chunk.
        Returns a list of all identified risk findings for the clause.
        """
        results: List[DetectionResult] = []
        if not clause_text or not clause_text.strip():
            return results

        for detector in self.detectors:
            result = detector.detect(clause_text)
            if result:
                results.append(result)

        return results

    def analyze_document(
        self,
        db: Session,
        document_id: uuid.UUID,
    ) -> List[Finding]:
        """
        Analyze all clauses in a document:
        1. Validates document existence in PostgreSQL.
        2. Retrieves all segmented clauses for the document.
        3. Executes rule detectors against each clause.
        4. Prevents duplicate findings for the same (clause_id, category).
        5. Persists findings referencing the exact clause_id.
        6. Updates Document status to ANALYZED.
        """
        doc = DocumentService.get(db, document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")

        clauses = ClauseService.list_by_document(db, document_id)
        if not clauses:
            logger.info(f"Document '{document_id}' has 0 clauses to analyze.")
            return []

        # Retrieve existing findings to guarantee deduplication
        existing_findings = FindingService.list_by_document(db, document_id)
        existing_keys: Set[Tuple[uuid.UUID, str]] = {
            (f.clause_id, f.category) for f in existing_findings
        }

        new_findings_in: List[FindingCreate] = []

        for clause in clauses:
            detections = self.analyze_clause_text(clause.clause_text)
            for detection in detections:
                key = (clause.clause_id, detection.category)
                if key not in existing_keys:
                    new_findings_in.append(
                        FindingCreate(
                            clause_id=clause.clause_id,
                            category=detection.category,
                            risk_level=detection.risk_level,
                            explanation=detection.explanation,
                            validated=False,
                        )
                    )
                    existing_keys.add(key)

        if new_findings_in:
            logger.info(f"Persisting {len(new_findings_in)} new risk findings for document {document_id}")
            FindingService.bulk_create(db, new_findings_in)

        # Update document status to ANALYZED
        doc.status = DocumentStatus.ANALYZED
        db.commit()
        db.refresh(doc)

        return FindingService.list_by_document(db, document_id)


# Global default engine instance
default_risk_engine = RiskAnalysisEngine()
