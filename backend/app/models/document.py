import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SourceType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    TEXT = "text"
    WEB = "web"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    upload_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    original_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status_enum", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    clauses: Mapped[List["Clause"]] = relationship(
        "Clause",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Clause.clause_order",
    )
    chat_history: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ChatHistory.created_at",
    )

    __table_args__ = (
        Index("ix_documents_upload_time_status", "upload_time", "status"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.document_id} filename='{self.filename}' source='{self.source_type}' status='{self.status}'>"
