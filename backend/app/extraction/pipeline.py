import os
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.document import Document, SourceType, DocumentStatus
from app.models.clause import Clause
from app.schemas.document import DocumentCreate
from app.schemas.clause import ClauseCreate
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
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

# 25 MB max upload size
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


def ingest_document_file(
    db: Session,
    filename: str,
    file_bytes: bytes,
) -> Tuple[Document, List[Clause]]:
    """
    Unified ingestion pipeline for file uploads (PDF, DOCX, TXT):
    1. Validates file size (limit: 25 MB).
    2. Determines format from filename extension and validates format.
    3. Executes extraction, cleaning, normalization, section detection, and clause segmentation.
    4. Persists the Document and all associated Clauses to PostgreSQL.
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"File size ({len(file_bytes) / (1024*1024):.2f} MB) exceeds maximum allowed upload limit (25 MB)."
        )

    _, ext = os.path.splitext(filename.lower())
    if not ext:
        raise UnsupportedFileTypeError(
            "File has no extension. Supported formats are: .pdf, .docx, and .txt."
        )

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

    # 1. Create Document record in PostgreSQL
    doc_in = DocumentCreate(
        filename=filename,
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

    doc_in = DocumentCreate(
        filename=title or "Direct Text Submission",
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
