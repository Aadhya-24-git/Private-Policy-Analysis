import os
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document, SourceType, DocumentStatus
from app.models.clause import Clause
from app.schemas.document import DocumentCreate
from app.schemas.clause import ClauseCreate
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.core.config import settings
from app.core.security import sanitize_filename, validate_file_content
from app.extraction.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.extraction.extractors import (
    extract_from_pdf,
    extract_from_docx,
    extract_from_txt,
    extract_from_plain_text,
)

# Configurable max upload size (default 25 MB)
MAX_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_BYTES


def ingest_document_file(
    db: Session,
    filename: str,
    file_bytes: bytes,
) -> Tuple[Document, List[Clause]]:
    """
    Unified ingestion pipeline for file uploads (PDF, DOCX, TXT):
    1. Sanitizes filename against directory traversal, control chars, and illegal sequences.
    2. Validates file size, MIME signatures, and executable byte headers.
    3. Determines format from validated filename extension.
    4. Executes extraction, cleaning, normalization, section detection, and clause segmentation.
    5. Persists the Document and all associated Clauses to PostgreSQL.
    """
    # 1. Sanitize filename & prevent path traversal
    safe_filename = sanitize_filename(filename)

    # 2. Validate file size and content integrity
    validate_file_content(safe_filename, file_bytes, max_size_bytes=MAX_FILE_SIZE_BYTES)

    _, ext = os.path.splitext(safe_filename.lower())

    if ext == ".pdf":
        source_type = SourceType.PDF
        normalized_text, extracted_clauses = extract_from_pdf(file_bytes)
    elif ext == ".docx":
        source_type = SourceType.DOCX
        normalized_text, extracted_clauses = extract_from_docx(file_bytes)
    elif ext == ".txt":
        source_type = SourceType.TXT
        normalized_text, extracted_clauses = extract_from_txt(file_bytes)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported formats are: .pdf, .docx, and .txt."
        )

    # 3. Create Document record in PostgreSQL with sanitized filename
    doc_in = DocumentCreate(
        filename=safe_filename,
        source_type=source_type,
        original_text=normalized_text,
        status=DocumentStatus.INDEXED,
    )
    document = DocumentService.create(db, doc_in)

    # 2. Bulk create Clause records in PostgreSQL
    clauses_in = [
        ClauseCreate(
            document_id=document.document_id,
            page_number=c.page_number,
            paragraph_number=c.paragraph_number,
            section=c.section,
            clause_text=c.clause_text,
            clause_order=c.clause_order,
            embedding=None,  # No embeddings generated in Phase 2
        )
        for c in extracted_clauses
    ]
    clauses = ClauseService.bulk_create(db, clauses_in)

    return document, clauses


def ingest_plain_text(
    db: Session,
    raw_text: str,
    title: Optional[str] = None,
) -> Tuple[Document, List[Clause]]:
    """
    Ingestion pipeline for direct plain-text submissions:
    1. Validates text payload.
    2. Executes extraction, cleaning, normalization, section detection, and clause segmentation.
    3. Persists Document (source_type='text') and Clauses to PostgreSQL.
    """
    normalized_text, extracted_clauses = extract_from_plain_text(raw_text)

    safe_title = "Direct Text Submission"
    if title and title.strip():
        # Strip control characters and cap length
        safe_title = "".join(c for c in title if ord(c) >= 32).strip()
        safe_title = safe_title[:200] if safe_title else "Direct Text Submission"

    doc_in = DocumentCreate(
        filename=safe_title,
        source_type=SourceType.TEXT,
        original_text=normalized_text,
        status=DocumentStatus.INDEXED,
    )
    document = DocumentService.create(db, doc_in)

    clauses_in = [
        ClauseCreate(
            document_id=document.document_id,
            page_number=c.page_number,
            paragraph_number=c.paragraph_number,
            section=c.section,
            clause_text=c.clause_text,
            clause_order=c.clause_order,
            embedding=None,
        )
        for c in extracted_clauses
    ]
    clauses = ClauseService.bulk_create(db, clauses_in)

    return document, clauses
