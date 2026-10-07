import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.clause import Clause
from app.schemas.clause import ClauseCreate, ClauseUpdate


class ClauseService:
    @staticmethod
    def create(db: Session, clause_in: ClauseCreate) -> Clause:
        db_clause = Clause(
            document_id=clause_in.document_id,
            page_number=clause_in.page_number,
            paragraph_number=clause_in.paragraph_number,
            section=clause_in.section,
            clause_text=clause_in.clause_text,
            clause_order=clause_in.clause_order,
            embedding=clause_in.embedding,
        )
        try:
            db.add(db_clause)
            db.commit()
            db.refresh(db_clause)
            return db_clause
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def bulk_create(db: Session, clauses_in: List[ClauseCreate]) -> List[Clause]:
        db_clauses = [
            Clause(
                document_id=c.document_id,
                page_number=c.page_number,
                paragraph_number=c.paragraph_number,
                section=c.section,
                clause_text=c.clause_text,
                clause_order=c.clause_order,
                embedding=c.embedding,
            )
            for c in clauses_in
        ]
        try:
            db.add_all(db_clauses)
            db.commit()
            for c in db_clauses:
                db.refresh(c)
            return db_clauses
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get(db: Session, clause_id: uuid.UUID) -> Optional[Clause]:
        return db.get(Clause, clause_id)

    @staticmethod
    def list_by_document(db: Session, document_id: uuid.UUID) -> List[Clause]:
        stmt = (
            select(Clause)
            .where(Clause.document_id == document_id)
            .order_by(Clause.clause_order.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def search_similar(
        db: Session,
        query_vector: List[float],
        limit: int = 5,
        document_id: Optional[uuid.UUID] = None,
    ) -> List[Clause]:
        """
        Cosine similarity search using pgvector's cosine_distance operator (<=>).
        """
        stmt = select(Clause).where(Clause.embedding.is_not(None))
        if document_id:
            stmt = stmt.where(Clause.document_id == document_id)
        stmt = stmt.order_by(Clause.embedding.cosine_distance(query_vector)).limit(limit)
        return list(db.scalars(stmt).all())
