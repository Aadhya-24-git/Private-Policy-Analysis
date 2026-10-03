import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.clause import Clause
from app.models.finding import Finding, RiskLevel
from app.schemas.finding import FindingCreate, FindingUpdate


class FindingService:
    @staticmethod
    def create(db: Session, finding_in: FindingCreate) -> Finding:
        db_finding = Finding(
            clause_id=finding_in.clause_id,
            category=finding_in.category,
            risk_level=finding_in.risk_level,
            explanation=finding_in.explanation,
            validated=finding_in.validated,
        )
        db.add(db_finding)
        db.commit()
        db.refresh(db_finding)
        return db_finding

    @staticmethod
    def bulk_create(db: Session, findings_in: List[FindingCreate]) -> List[Finding]:
        db_findings = [
            Finding(
                clause_id=f.clause_id,
                category=f.category,
                risk_level=f.risk_level,
                explanation=f.explanation,
                validated=f.validated,
            )
            for f in findings_in
        ]
        db.add_all(db_findings)
        db.commit()
        for f in db_findings:
            db.refresh(f)
        return db_findings

    @staticmethod
    def get(db: Session, finding_id: uuid.UUID) -> Optional[Finding]:
        return db.get(Finding, finding_id)

    @staticmethod
    def list_by_clause(db: Session, clause_id: uuid.UUID) -> List[Finding]:
        stmt = (
            select(Finding)
            .where(Finding.clause_id == clause_id)
            .order_by(Finding.created_at.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_by_document(
        db: Session,
        document_id: uuid.UUID,
        min_risk: Optional[RiskLevel] = None,
    ) -> List[Finding]:
        stmt = (
            select(Finding)
            .join(Clause, Finding.clause_id == Clause.clause_id)
            .where(Clause.document_id == document_id)
            .order_by(Finding.created_at.desc())
        )
        if min_risk:
            stmt = stmt.where(Finding.risk_level == min_risk)
        return list(db.scalars(stmt).all())

    @staticmethod
    def set_validated(db: Session, finding_id: uuid.UUID, validated: bool = True) -> Optional[Finding]:
        db_finding = db.get(Finding, finding_id)
        if not db_finding:
            return None
        db_finding.validated = validated
        db.commit()
        db.refresh(db_finding)
        return db_finding
