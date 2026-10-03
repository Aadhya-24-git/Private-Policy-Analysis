import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database.base import Base


class Clause(Base):
    __tablename__ = "clauses"

    clause_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    paragraph_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    section: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    clause_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    clause_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="clauses",
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="clause",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_clauses_doc_order", "document_id", "clause_order"),
    )

    def __repr__(self) -> str:
        return f"<Clause id={self.clause_id} doc={self.document_id} order={self.clause_order}>"
