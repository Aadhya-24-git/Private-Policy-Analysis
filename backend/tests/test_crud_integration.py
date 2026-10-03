import uuid
import pytest
from app.database.session import SessionLocal, check_database_connection
from app.models.document import SourceType, DocumentStatus
from app.models.finding import RiskLevel
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.schemas.clause import ClauseCreate
from app.schemas.finding import FindingCreate
from app.schemas.chat_history import ChatHistoryCreate
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.services.finding_service import FindingService
from app.services.chat_service import ChatHistoryService


@pytest.fixture
def db_session():
    health = check_database_connection()
    if health["status"] == "disconnected":
        pytest.skip("PostgreSQL live instance is not running; skipping live DB test.")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_database_health_check_live():
    """Verify live PostgreSQL and pgvector health check returns connected and active."""
    health = check_database_connection()
    if health["status"] == "disconnected":
        pytest.skip("PostgreSQL live instance is not running; skipping live DB test.")
    assert health["status"] == "connected"
    assert health["pgvector_installed"] is True
    assert health["pgvector_version"] is not None
    assert health["error"] is None


def test_complete_crud_and_cascade_lifecycle(db_session):
    """
    Test full lifecycle across all 4 tables:
    1. Create document
    2. Create clauses with pgvector 1536-dim embedding
    3. Create findings linked to clauses
    4. Create chat_history linked to document
    5. Query and vector search
    6. Cascade delete
    """
    # 1. Create Document
    doc_in = DocumentCreate(
        filename="test_privacy_policy.pdf",
        source_type=SourceType.PDF,
        original_text="This is a test privacy policy text for Phase 1 verification.",
        status=DocumentStatus.PENDING,
    )
    doc = DocumentService.create(db_session, doc_in)
    assert doc.document_id is not None
    assert doc.filename == "test_privacy_policy.pdf"
    assert doc.source_type == SourceType.PDF
    assert doc.status == DocumentStatus.PENDING

    doc_id = doc.document_id

    # Update document status
    updated_doc = DocumentService.update(db_session, doc_id, DocumentUpdate(status=DocumentStatus.INDEXED))
    assert updated_doc.status == DocumentStatus.INDEXED

    # 2. Create Clauses with pgvector embedding
    # Mock a 1536-dimensional embedding vector
    vec_1 = [0.01 * (i % 10) for i in range(1536)]
    vec_2 = [0.02 * (i % 10) for i in range(1536)]

    clause_1_in = ClauseCreate(
        document_id=doc_id,
        page_number=1,
        paragraph_number=1,
        section="Data Collection",
        clause_text="We collect your personal information including location and biometrics.",
        clause_order=0,
        embedding=vec_1,
    )
    clause_2_in = ClauseCreate(
        document_id=doc_id,
        page_number=1,
        paragraph_number=2,
        section="Liability",
        clause_text="You agree to waive all rights to trial by jury and class actions.",
        clause_order=1,
        embedding=vec_2,
    )

    clause_1 = ClauseService.create(db_session, clause_1_in)
    clause_2 = ClauseService.create(db_session, clause_2_in)

    assert clause_1.clause_id is not None
    assert clause_2.clause_id is not None

    # Verify clauses retrieval
    clauses = ClauseService.list_by_document(db_session, doc_id)
    assert len(clauses) == 2
    assert clauses[0].clause_order == 0
    assert clauses[1].clause_order == 1

    # Test pgvector similarity search
    similar_clauses = ClauseService.search_similar(db_session, query_vector=vec_1, limit=1, document_id=doc_id)
    assert len(similar_clauses) == 1
    assert similar_clauses[0].clause_id == clause_1.clause_id

    # 3. Create Findings linked to Clause
    finding_in = FindingCreate(
        clause_id=clause_2.clause_id,
        category="forced_arbitration",
        risk_level=RiskLevel.HIGH,
        explanation="Forced arbitration clause eliminates right to court litigation.",
        validated=False,
    )
    finding = FindingService.create(db_session, finding_in)
    assert finding.finding_id is not None
    assert finding.risk_level == RiskLevel.HIGH

    # Verify finding query by document and clause
    doc_findings = FindingService.list_by_document(db_session, doc_id)
    assert len(doc_findings) == 1
    assert doc_findings[0].category == "forced_arbitration"

    # Validate finding
    val_finding = FindingService.set_validated(db_session, finding.finding_id, True)
    assert val_finding.validated is True

    # 4. Create ChatHistory linked to Document
    chat_in = ChatHistoryCreate(
        document_id=doc_id,
        question="Does this policy have forced arbitration?",
        answer="Yes, Clause 2 mandates forced arbitration and class action waiver.",
    )
    chat = ChatHistoryService.create(db_session, chat_in)
    assert chat.chat_id is not None
    assert "forced arbitration" in chat.answer

    chats = ChatHistoryService.list_by_document(db_session, doc_id)
    assert len(chats) == 1

    # 5. Test Cascade Deletion: deleting Document must delete all linked clauses, findings, and chat
    deleted = DocumentService.delete(db_session, doc_id)
    assert deleted is True

    # Verify cascades
    assert DocumentService.get(db_session, doc_id) is None
    assert ClauseService.get(db_session, clause_1.clause_id) is None
    assert ClauseService.get(db_session, clause_2.clause_id) is None
    assert FindingService.get(db_session, finding.finding_id) is None
    assert ChatHistoryService.get(db_session, chat.chat_id) is None
