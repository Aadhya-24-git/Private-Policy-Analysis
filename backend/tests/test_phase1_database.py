import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from pgvector.sqlalchemy import Vector
from app.database.base import Base
from app.models.document import Document, SourceType, DocumentStatus
from app.models.clause import Clause
from app.models.finding import Finding, RiskLevel
from app.models.chat_history import ChatHistory
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.schemas.clause import ClauseCreate
from app.schemas.finding import FindingCreate
from app.schemas.chat_history import ChatHistoryCreate
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.services.finding_service import FindingService
from app.services.chat_service import ChatHistoryService


def test_tables_metadata():
    """Verify all 4 required tables and relationships are registered in SQLAlchemy metadata."""
    tables = Base.metadata.tables
    assert "documents" in tables
    assert "clauses" in tables
    assert "findings" in tables
    assert "chat_history" in tables

    # 1. documents table validation
    doc_cols = tables["documents"].columns
    assert "document_id" in doc_cols
    assert "filename" in doc_cols
    assert "source_type" in doc_cols
    assert "upload_time" in doc_cols
    assert "original_text" in doc_cols
    assert "status" in doc_cols
    assert doc_cols["document_id"].primary_key

    # 2. clauses table validation
    clause_cols = tables["clauses"].columns
    assert "clause_id" in clause_cols
    assert "document_id" in clause_cols
    assert "page_number" in clause_cols
    assert "paragraph_number" in clause_cols
    assert "section" in clause_cols
    assert "clause_text" in clause_cols
    assert "clause_order" in clause_cols
    assert "embedding" in clause_cols
    assert isinstance(clause_cols["embedding"].type, Vector)
    assert clause_cols["embedding"].type.dim == 1536

    # 3. findings table validation
    finding_cols = tables["findings"].columns
    assert "finding_id" in finding_cols
    assert "clause_id" in finding_cols
    assert "category" in finding_cols
    assert "risk_level" in finding_cols
    assert "explanation" in finding_cols
    assert "validated" in finding_cols
    assert "created_at" in finding_cols

    # 4. chat_history table validation
    chat_cols = tables["chat_history"].columns
    assert "chat_id" in chat_cols
    assert "document_id" in chat_cols
    assert "question" in chat_cols
    assert "answer" in chat_cols
    assert "created_at" in chat_cols


def test_foreign_key_constraints():
    """Verify cascade delete rules and foreign key definitions."""
    tables = Base.metadata.tables

    # clauses -> documents
    clause_fks = list(tables["clauses"].foreign_keys)
    assert any(fk.column.table.name == "documents" and fk.ondelete == "CASCADE" for fk in clause_fks)

    # findings -> clauses
    finding_fks = list(tables["findings"].foreign_keys)
    assert any(fk.column.table.name == "clauses" and fk.ondelete == "CASCADE" for fk in finding_fks)

    # chat_history -> documents
    chat_fks = list(tables["chat_history"].foreign_keys)
    assert any(fk.column.table.name == "documents" and fk.ondelete == "CASCADE" for fk in chat_fks)


def test_source_type_enum():
    """Verify source_type supports pdf, docx, txt, text, web."""
    supported = {st.value for st in SourceType}
    assert supported == {"pdf", "docx", "txt", "text", "web"}


def test_risk_level_enum():
    """Verify risk_level supports standard severity levels."""
    levels = {r.value for r in RiskLevel}
    assert levels == {"low", "medium", "high", "critical"}


def test_alembic_migration_file_present():
    """Verify Alembic initial migration exists and exports upgrade/downgrade."""
    import importlib.util
    from pathlib import Path

    migration_file = Path("alembic/versions/2026_10_03_0001_initial_tables.py")
    if not migration_file.exists():
        migration_file = Path("backend/alembic/versions/2026_10_03_0001_initial_tables.py")
    assert migration_file.exists()

    spec = importlib.util.spec_from_file_location("initial_migration", migration_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, "upgrade")
    assert hasattr(module, "downgrade")
    assert module.revision == "0001_initial_tables"
    assert module.down_revision is None
