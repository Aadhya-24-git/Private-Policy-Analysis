from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.analysis import (
    AnalyzeTextRequest,
    AnalyzeResponse,
    ClauseSummary,
)
from app.extraction.pipeline import ingest_document_file, ingest_plain_text
from app.extraction.exceptions import EmptyDocumentError

router = APIRouter()


@router.post(
    "/analyze/file",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and extract document file",
    description="Accepts a PDF, DOCX, or TXT file, extracts text, cleans/normalizes content, detects sections, segments clauses with source references, and stores in PostgreSQL.",
)
async def analyze_file(
    file: UploadFile = File(..., description="Document file to analyze (PDF, DOCX, or TXT)"),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    from app.core.config import settings
    from app.extraction.exceptions import FileTooLargeError

    if not file.filename:
        raise EmptyDocumentError("No filename provided.")

    chunk_size = 1024 * 1024  # 1MB chunks
    file_bytes_list = []
    total_bytes = 0
    max_size = settings.MAX_UPLOAD_SIZE_BYTES

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_size:
            raise FileTooLargeError(
                f"File size exceeds maximum allowed upload limit ({max_size / (1024*1024):.0f} MB)."
            )
        file_bytes_list.append(chunk)

    file_bytes = b"".join(file_bytes_list)
    document, clauses = ingest_document_file(
        db=db,
        filename=file.filename,
        file_bytes=file_bytes,
    )

    clause_summaries = [
        ClauseSummary(
            clause_id=c.clause_id,
            page_number=c.page_number,
            paragraph_number=c.paragraph_number,
            section=c.section,
            clause_text=c.clause_text,
            clause_order=c.clause_order,
        )
        for c in clauses
    ]

    return AnalyzeResponse(
        document_id=document.document_id,
        filename=document.filename,
        source_type=document.source_type,
        status=document.status,
        total_clauses=len(clause_summaries),
        clauses=clause_summaries,
        message=f"Document '{document.filename}' ingested successfully. Extracted {len(clause_summaries)} clauses into PostgreSQL.",
    )


@router.post(
    "/analyze/text",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and extract plain text",
    description="Accepts plain text legal agreement, normalizes content, detects headings/sections, segments clauses, and stores in PostgreSQL.",
)
def analyze_text(
    payload: AnalyzeTextRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    document, clauses = ingest_plain_text(
        db=db,
        raw_text=payload.text,
        title=payload.title,
    )

    clause_summaries = [
        ClauseSummary(
            clause_id=c.clause_id,
            page_number=c.page_number,
            paragraph_number=c.paragraph_number,
            section=c.section,
            clause_text=c.clause_text,
            clause_order=c.clause_order,
        )
        for c in clauses
    ]

    return AnalyzeResponse(
        document_id=document.document_id,
        filename=document.filename,
        source_type=document.source_type,
        status=document.status,
        total_clauses=len(clause_summaries),
        clauses=clause_summaries,
        message=f"Plain text ingested successfully. Extracted {len(clause_summaries)} clauses into PostgreSQL.",
    )


from typing import List
import uuid
from fastapi import HTTPException
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    summary="List all uploaded documents",
)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[DocumentResponse]:
    return DocumentService.list(db, skip=skip, limit=limit)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details by ID",
)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    doc = DocumentService.get(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found")
    return doc

