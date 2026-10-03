import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.models.clause import Clause
from app.schemas.comparison import PolicyCompareResponse
from app.comparison.matcher import (
    cosine_similarity,
    lexical_similarity,
    calculate_clause_similarity,
    match_policy_clauses,
)
from app.comparison.explainer import (
    explain_clause_modification,
    explain_added_clause,
    explain_removed_clause,
)
from app.comparison.service import PolicyComparisonService
from app.rag.exceptions import DocumentNotFoundError
from app.database.session import get_db


# ==============================================================================
# 1. Similarity Utility Tests
# ==============================================================================

def test_cosine_similarity():
    """Verify cosine similarity calculation between float vectors."""
    # Identical vectors
    assert cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == 1.0
    # Orthogonal vectors
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    # Collinear scaled vectors
    assert round(cosine_similarity([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]), 4) == 1.0
    # Invalid / empty
    assert cosine_similarity([], [1.0]) == 0.0
    assert cosine_similarity(None, [1.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0


def test_lexical_similarity():
    """Verify normalized lexical similarity ratio."""
    assert lexical_similarity("Arbitration is mandatory.", "Arbitration is mandatory.") == 1.0
    # Case & whitespace normalization
    assert lexical_similarity("  Arbitration is MANDATORY. \n", "arbitration is mandatory.") == 1.0
    # Minor word change
    score = lexical_similarity(
        "Disputes are resolved by AAA arbitration.",
        "Disputes are resolved by JAMS arbitration.",
    )
    assert score > 0.8
    # Completely different
    assert lexical_similarity("Privacy policy data collection.", "Billing refund policy.") < 0.4


# ==============================================================================
# 2. Semantic Clause Matching Algorithm Tests (Added, Removed, Modified, Unchanged)
# ==============================================================================

def test_match_policy_clauses_all_cases():
    """
    Test comprehensive matching covering:
    - Unchanged clauses
    - Modified clauses
    - Added clauses
    - Removed clauses
    """
    doc_old = uuid.uuid4()
    doc_new = uuid.uuid4()

    # Old clauses
    c_old_unchanged = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_old,
        clause_order=0,
        clause_text="Subscriptions renew automatically on a monthly basis.",
        section="Billing",
        page_number=1,
    )
    c_old_modified = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_old,
        clause_order=1,
        clause_text="Disputes must be submitted to binding arbitration under AAA rules within 30 days.",
        section="Disputes",
        page_number=2,
    )
    c_old_removed = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_old,
        clause_order=2,
        clause_text="Users may request a full refund within 14 calendar days.",
        section="Refunds",
        page_number=2,
    )

    # New clauses
    c_new_unchanged = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_new,
        clause_order=0,
        clause_text="Subscriptions renew automatically on a monthly basis.",
        section="Billing",
        page_number=1,
    )
    c_new_modified = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_new,
        clause_order=1,
        clause_text="Disputes must be submitted to binding arbitration under JAMS rules within 60 days.",
        section="Disputes",
        page_number=2,
    )
    c_new_added = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_new,
        clause_order=2,
        clause_text="We share personal information with third party advertising partners for commercial purposes.",
        section="Privacy",
        page_number=3,
    )

    old_clauses = [c_old_unchanged, c_old_modified, c_old_removed]
    new_clauses = [c_new_unchanged, c_new_modified, c_new_added]

    unchanged, modified, added, removed = match_policy_clauses(old_clauses, new_clauses)

    # Validate Unchanged
    assert len(unchanged) == 1
    assert unchanged[0][0].clause_id == c_old_unchanged.clause_id
    assert unchanged[0][1].clause_id == c_new_unchanged.clause_id

    # Validate Modified
    assert len(modified) == 1
    old_mod, new_mod, score = modified[0]
    assert old_mod.clause_id == c_old_modified.clause_id
    assert new_mod.clause_id == c_new_modified.clause_id
    assert score > 0.7  # High similarity due to JAMS vs AAA and 60 vs 30 days

    # Validate Added
    assert len(added) == 1
    assert added[0].clause_id == c_new_added.clause_id

    # Validate Removed
    assert len(removed) == 1
    assert removed[0].clause_id == c_old_removed.clause_id


def test_identical_policy_comparison():
    """Verify comparing the exact same document ID returns 100% unchanged."""
    doc_id = uuid.uuid4()
    c1 = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        clause_order=0,
        clause_text="Clause 1 text",
    )
    c2 = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        clause_order=1,
        clause_text="Clause 2 text",
    )

    mock_db = MagicMock()
    mock_doc = Document(document_id=doc_id, filename="terms.pdf")

    with patch("app.comparison.service.DocumentService.get", return_value=mock_doc), \
         patch("app.comparison.service.ClauseService.list_by_document", return_value=[c1, c2]):

        response: PolicyCompareResponse = PolicyComparisonService.compare_documents(
            db=mock_db,
            old_document_id=doc_id,
            new_document_id=doc_id,
        )

        assert response.summary.unchanged_count == 2
        assert response.summary.added_count == 0
        assert response.summary.removed_count == 0
        assert response.summary.modified_count == 0
        assert "identical" in response.summary.overview.lower()


# ==============================================================================
# 3. Modification Explainer Tests
# ==============================================================================

def test_explain_clause_modification_mocked():
    """Verify LLM explainer passes old/new clauses with neutral instructions."""
    old_text = "Notice of cancellation must be provided 14 days in advance."
    new_text = "Notice of cancellation must be provided 30 days in advance."

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "The required cancellation notice period was increased from 14 to 30 days."

    explanation = explain_clause_modification(old_text, new_text, llm_client=mock_llm)
    assert "increased from 14 to 30 days" in explanation

    mock_llm.generate.assert_called_once()
    call_kwargs = mock_llm.generate.call_args.kwargs
    assert "EXCLUSIVELY" in call_kwargs["system_prompt"]
    assert old_text in call_kwargs["prompt"]
    assert new_text in call_kwargs["prompt"]


def test_explain_clause_modification_fallback():
    """Verify deterministic fallback if LLM encounters an exception."""
    old_text = "Old short clause."
    new_text = "New longer clause with expanded stipulations."

    mock_llm = MagicMock()
    mock_llm.generate.side_effect = Exception("LLM offline")

    explanation = explain_clause_modification(old_text, new_text, llm_client=mock_llm)
    assert "Clause text was" in explanation
    assert len(explanation) > 10


def test_explain_added_and_removed():
    """Verify standard explanation strings for added and removed clauses."""
    added_exp = explain_added_clause("New clause")
    assert "Newly introduced" in added_exp

    removed_exp = explain_removed_clause("Old clause")
    assert "excised" in removed_exp or "removed" in removed_exp


# ==============================================================================
# 4. API Endpoint Integration Tests
# ==============================================================================

@pytest.fixture
def override_db():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.pop(get_db, None)


def test_compare_endpoint_success(client: TestClient, override_db):
    """Verify POST /api/v1/compare executes comparison and returns structured JSON."""
    old_id = uuid.uuid4()
    new_id = uuid.uuid4()

    mock_response = PolicyCompareResponse(
        old_document_id=old_id,
        new_document_id=new_id,
        old_document_name="Terms_2025.pdf",
        new_document_name="Terms_2026.pdf",
        summary={
            "total_old_clauses": 3,
            "total_new_clauses": 3,
            "added_count": 1,
            "removed_count": 1,
            "modified_count": 1,
            "unchanged_count": 1,
            "overview": "Policy comparison identified 1 modified clauses, 1 newly added clauses, 1 removed clauses.",
        },
        modified_clauses=[
            {
                "old_clause": {
                    "clause_id": uuid.uuid4(),
                    "clause_order": 1,
                    "section": "Arbitration",
                    "clause_text": "Disputes resolved via AAA.",
                },
                "new_clause": {
                    "clause_id": uuid.uuid4(),
                    "clause_order": 1,
                    "section": "Arbitration",
                    "clause_text": "Disputes resolved via JAMS.",
                },
                "similarity_score": 0.85,
                "change_type": "modified",
                "explanation": "Arbitration provider changed from AAA to JAMS.",
            }
        ],
        added_clauses=[],
        removed_clauses=[],
        unchanged_count=1,
    )

    with patch("app.api.v1.endpoints.compare.PolicyComparisonService.compare_documents", return_value=mock_response):
        res = client.post(
            "/api/v1/compare",
            json={
                "old_document_id": str(old_id),
                "new_document_id": str(new_id),
                "explain_changes": True,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["old_document_id"] == str(old_id)
        assert data["new_document_id"] == str(new_id)
        assert data["summary"]["modified_count"] == 1
        assert len(data["modified_clauses"]) == 1
        assert data["modified_clauses"][0]["old_clause"]["section"] == "Arbitration"
        assert "AAA to JAMS" in data["modified_clauses"][0]["explanation"]


def test_compare_endpoint_document_not_found(client: TestClient, override_db):
    """Verify 404 when either old or new document ID does not exist."""
    old_id = uuid.uuid4()
    new_id = uuid.uuid4()

    with patch(
        "app.api.v1.endpoints.compare.PolicyComparisonService.compare_documents",
        side_effect=DocumentNotFoundError(f"Previous policy document with ID '{old_id}' not found."),
    ):
        res = client.post(
            "/api/v1/compare",
            json={
                "old_document_id": str(old_id),
                "new_document_id": str(new_id),
            },
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()
