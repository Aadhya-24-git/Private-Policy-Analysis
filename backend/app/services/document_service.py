import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    @staticmethod
    def create(db: Session, doc_in: DocumentCreate) -> Document:
        db_doc = Document(
            filename=doc_in.filename,
            source_type=doc_in.source_type,
            original_text=doc_in.original_text,
            status=doc_in.status,
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc

    @staticmethod
    def get(db: Session, doc_id: uuid.UUID) -> Optional[Document]:
        return db.get(Document, doc_id)

    @staticmethod
    def list(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None,
    ) -> List[Document]:
        stmt = select(Document).order_by(Document.upload_time.desc())
        if status:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(
        db: Session,
        doc_id: uuid.UUID,
        doc_update: DocumentUpdate,
    ) -> Optional[Document]:
        db_doc = db.get(Document, doc_id)
        if not db_doc:
            return None
        if doc_update.filename is not None:
            db_doc.filename = doc_update.filename
        if doc_update.status is not None:
            db_doc.status = doc_update.status
        db.commit()
        db.refresh(db_doc)
        return db_doc

    @staticmethod
    def delete(db: Session, doc_id: uuid.UUID) -> bool:
        db_doc = db.get(Document, doc_id)
        if not db_doc:
            return False
        db.delete(db_doc)
        db.commit()
        return True

    @staticmethod
    def count(db: Session) -> int:
        return db.scalar(select(func.count()).select_from(Document)) or 0
