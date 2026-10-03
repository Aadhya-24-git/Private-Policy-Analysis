import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document, DocumentStatus, SourceType
from app.models.clause import Clause
from app.models.finding import Finding, RiskLevel
from app.schemas.finding import DocumentFindingsSummary, FindingWithSource
from app.analysis.engine import RiskAnalysisEngine, default_risk_engine
from app.analysis.detectors import (
    AutoRenewalDetector,
    HiddenFeesDetector,
    ArbitrationDetector,
    DataSharingDetector,
    CancellationDetector,
    DataRetentionDetector,
    LiabilityDetector,
)
from app.database.session import get_db


# ==============================================================================
# 1. Individual Detector Positive & Negative Tests
# ==============================================================================

class TestAutoRenewalDetector:
    detector = AutoRenewalDetector()

    def test_positive_auto_renewal(self):
        text = "Your subscription automatically renews on a monthly basis until you cancel."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "auto_renewal"
        assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        assert "renew automatically" in result.explanation.lower()


    def test_positive_successive_terms(self):
        text = "This agreement renews for successive terms of one year each."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "auto_renewal"
        assert result.risk_level == RiskLevel.HIGH

    def test_negative_no_renewal(self):
        text = "Users may purchase a one-time pass valid for 24 hours."
        assert self.detector.detect(text) is None

    def test_negative_explicit_negation(self):
        text = "Your subscription does not automatically renew at the end of the term."
        assert self.detector.detect(text) is None


class TestHiddenFeesDetector:
    detector = HiddenFeesDetector()

    def test_positive_additional_fees(self):
        text = "Users may be subject to additional fees and administrative charges."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "hidden_fees"
        assert result.risk_level == RiskLevel.MEDIUM

    def test_positive_unannounced_price_change(self):
        text = "All service fees are subject to change without prior notice."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "hidden_fees"
        assert result.risk_level == RiskLevel.HIGH

    def test_negative_transparent_pricing(self):
        text = "The monthly fee is $10.00 with no additional charges or hidden fees."
        assert self.detector.detect(text) is None

    def test_negative_generic_clause(self):
        text = "You can view your current account balance in the settings menu."
        assert self.detector.detect(text) is None


class TestArbitrationDetector:
    detector = ArbitrationDetector()

    def test_positive_binding_arbitration(self):
        text = "Any disputes shall be settled through mandatory binding arbitration."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "arbitration"
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_positive_class_action_waiver(self):
        text = "You agree to resolve disputes in your individual capacity and not as a plaintiff or class member in any class action."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "arbitration"
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_positive_jury_waiver(self):
        text = "Both parties agree that trial by jury is hereby waived in any legal proceeding."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "arbitration"

    def test_negative_arbitration_optional(self):
        text = "Dispute resolution via arbitration is optional for consumers."
        assert self.detector.detect(text) is None

    def test_negative_court_jurisdiction(self):
        text = "This contract is governed by the laws of the State of California."
        assert self.detector.detect(text) is None


class TestDataSharingDetector:
    detector = DataSharingDetector()

    def test_positive_share_with_third_parties(self):
        text = "We share your personal information with third party advertising partners."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "data_sharing"
        assert result.risk_level == RiskLevel.HIGH

    def test_positive_selling_data(self):
        text = "The company reserves the right to sell your user data for commercial purposes."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "data_sharing"
        assert result.risk_level == RiskLevel.CRITICAL

    def test_negative_no_selling(self):
        text = "We do not sell your personal data to any external parties."
        assert self.detector.detect(text) is None

    def test_negative_internal_analytics(self):
        text = "We use system logs internally to monitor server performance."
        assert self.detector.detect(text) is None


class TestCancellationDetector:
    detector = CancellationDetector()

    def test_positive_advance_notice(self):
        text = "To avoid charges, you must cancel at least 30 days prior to the next billing cycle."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "cancellation"
        assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    def test_positive_cancellation_penalty(self):
        text = "Early termination fee of $150 applies if cancelled before contract end."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "cancellation"
        assert result.risk_level == RiskLevel.HIGH

    def test_negative_free_cancellation(self):
        text = "You may cancel at any time without any fee or penalty."
        assert self.detector.detect(text) is None

    def test_negative_generic_mention(self):
        text = "If an item is out of stock, we may cancel your purchase order."
        assert self.detector.detect(text) is None


class TestDataRetentionDetector:
    detector = DataRetentionDetector()

    def test_positive_indefinite_retention(self):
        text = "We may retain your personal data indefinitely for archival and business purposes."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "data_retention"
        assert result.risk_level == RiskLevel.HIGH

    def test_positive_retention_after_deletion(self):
        text = "We retain copies of your records even after you delete your account."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "data_retention"

    def test_negative_immediate_deletion(self):
        text = "All user records are immediately deleted upon account closure."
        assert self.detector.detect(text) is None

    def test_negative_purged_period(self):
        text = "Temporary cache is permanently purged within 24 hours."
        assert self.detector.detect(text) is None


class TestLiabilityDetector:
    detector = LiabilityDetector()

    def test_positive_limitation_of_liability(self):
        text = "In no event shall the company be liable for any indirect, incidental, or consequential damages."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "liability"
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_positive_strict_monetary_cap(self):
        text = "Our aggregate liability for any claims shall not exceed fifty dollars ($50)."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "liability"
        assert result.risk_level == RiskLevel.CRITICAL

    def test_positive_as_is_disclaimer(self):
        text = "The platform is provided on an 'as is' and 'as available' basis without warranties of any kind."
        result = self.detector.detect(text)
        assert result is not None
        assert result.category == "liability"

    def test_negative_liability_preserved(self):
        text = "This agreement does not exclude or limit our liability for gross negligence."
        assert self.detector.detect(text) is None

    def test_negative_unrelated_text(self):
        text = "Users must be at least 18 years old to access this application."
        assert self.detector.detect(text) is None


# ==============================================================================
# 2. Multi-Category Detection in Single Clause & Document
# ==============================================================================

def test_multiple_categories_single_clause():
    """Verify a clause containing multiple risk provisions triggers all applicable detectors."""
    engine = RiskAnalysisEngine()
    multi_text = (
        "Your subscription automatically renews each month; "
        "any early termination fee applies if you cancel, and "
        "all payments are non-refundable upon cancellation."
    )
    results = engine.analyze_clause_text(multi_text)
    categories = {r.category for r in results}
    assert "auto_renewal" in categories
    assert "cancellation" in categories


def test_multiple_categories_in_document():
    """Verify that multiple clauses in a document trigger findings across different categories."""
    engine = RiskAnalysisEngine()
    doc_id = uuid.uuid4()

    clauses = [
        Clause(
            clause_id=uuid.uuid4(),
            document_id=doc_id,
            clause_order=0,
            clause_text="Your subscription automatically renews on a monthly basis.",
            section="Billing",
        ),
        Clause(
            clause_id=uuid.uuid4(),
            document_id=doc_id,
            clause_order=1,
            clause_text="We share your personal information with third party advertisers.",
            section="Privacy",
        ),
        Clause(
            clause_id=uuid.uuid4(),
            document_id=doc_id,
            clause_order=2,
            clause_text="All disputes shall be resolved by mandatory binding arbitration and class action waiver.",
            section="Disputes",
        ),
        Clause(
            clause_id=uuid.uuid4(),
            document_id=doc_id,
            clause_order=3,
            clause_text="In no event shall we be liable; our total liability shall not exceed fifty dollars.",
            section="Liability",
        ),
    ]

    mock_db = MagicMock()
    mock_doc = Document(document_id=doc_id, filename="terms.pdf")

    with patch("app.analysis.engine.DocumentService.get", return_value=mock_doc), \
         patch("app.analysis.engine.ClauseService.list_by_document", return_value=clauses), \
         patch("app.analysis.engine.FindingService.list_by_document", return_value=[]), \
         patch("app.analysis.engine.FindingService.bulk_create") as mock_bulk:

        engine.analyze_document(mock_db, doc_id)

        assert mock_bulk.called
        created_findings = mock_bulk.call_args[0][1]
        created_categories = {f.category for f in created_findings}

        assert "auto_renewal" in created_categories
        assert "data_sharing" in created_categories
        assert "arbitration" in created_categories
        assert "liability" in created_categories


# ==============================================================================
# 3. Duplicate Prevention Tests
# ==============================================================================

def test_duplicate_prevention_on_reanalysis():
    """Verify running the engine multiple times on the same document avoids duplicate findings."""
    engine = RiskAnalysisEngine()
    doc_id = uuid.uuid4()
    clause_id = uuid.uuid4()

    clause = Clause(
        clause_id=clause_id,
        document_id=doc_id,
        clause_order=0,
        clause_text="Your subscription automatically renews each month.",
    )

    existing_finding = Finding(
        finding_id=uuid.uuid4(),
        clause_id=clause_id,
        category="auto_renewal",
        risk_level=RiskLevel.MEDIUM,
        explanation="Existing finding explanation",
    )

    mock_db = MagicMock()
    mock_doc = Document(document_id=doc_id, filename="terms.pdf")

    with patch("app.analysis.engine.DocumentService.get", return_value=mock_doc), \
         patch("app.analysis.engine.ClauseService.list_by_document", return_value=[clause]), \
         patch("app.analysis.engine.FindingService.list_by_document", return_value=[existing_finding]), \
         patch("app.analysis.engine.FindingService.bulk_create") as mock_bulk:

        engine.analyze_document(mock_db, doc_id)

        # bulk_create should NOT be called since auto_renewal already exists for this clause
        assert not mock_bulk.called


# ==============================================================================
# 4. Source Preservation Tests
# ==============================================================================

def test_source_preservation_in_findings():
    """Verify that finding summaries faithfully retain verbatim clause text and location metadata."""
    clause_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    clause = Clause(
        clause_id=clause_id,
        document_id=doc_id,
        clause_order=4,
        clause_text="In no event shall the company be liable for incidental damages.",
        section="Limitation of Liability",
        page_number=3,
        paragraph_number=2,
    )

    finding = Finding(
        finding_id=uuid.uuid4(),
        clause_id=clause_id,
        category="liability",
        risk_level=RiskLevel.HIGH,
        explanation="Clause disclaims warranties and excludes consequential damages.",
        validated=False,
        created_at=datetime.now(timezone.utc),
    )
    finding.clause = clause

    mock_db = MagicMock()
    with patch("app.api.v1.endpoints.audit.FindingService.list_by_document", return_value=[finding]):
        from app.api.v1.endpoints.audit import _build_findings_summary
        summary: DocumentFindingsSummary = _build_findings_summary(mock_db, doc_id)

        assert summary.total_findings == 1
        assert summary.high_count == 1
        f_res: FindingWithSource = summary.findings[0]
        assert f_res.clause_id == clause_id
        assert f_res.clause_order == 4
        assert f_res.section == "Limitation of Liability"
        assert f_res.page_number == 3
        assert f_res.paragraph_number == 2
        assert f_res.clause_text == "In no event shall the company be liable for incidental damages."


# ==============================================================================
# 5. API Endpoint Tests
# ==============================================================================

@pytest.fixture
def override_db():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.pop(get_db, None)


def test_audit_document_endpoint_success(client: TestClient, override_db):
    """Verify POST /api/v1/documents/{document_id}/audit executes the engine and returns summary."""
    doc_id = uuid.uuid4()
    clause_id = uuid.uuid4()

    mock_doc = Document(document_id=doc_id, filename="terms.pdf", status=DocumentStatus.INDEXED)
    mock_clause = Clause(
        clause_id=clause_id,
        document_id=doc_id,
        clause_order=0,
        clause_text="All disputes shall be resolved by binding arbitration.",
        section="Arbitration",
    )
    mock_finding = Finding(
        finding_id=uuid.uuid4(),
        clause_id=clause_id,
        category="arbitration",
        risk_level=RiskLevel.HIGH,
        explanation="Mandatory binding arbitration specified.",
        validated=False,
        created_at=datetime.now(timezone.utc),
    )
    mock_finding.clause = mock_clause

    with patch("app.analysis.engine.DocumentService.get", return_value=mock_doc), \
         patch("app.analysis.engine.ClauseService.list_by_document", return_value=[mock_clause]), \
         patch("app.analysis.engine.FindingService.list_by_document", side_effect=[[], [mock_finding], [mock_finding]]), \
         patch("app.analysis.engine.FindingService.bulk_create"):

        res = client.post(f"/api/v1/documents/{doc_id}/audit")
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == str(doc_id)
        assert data["total_findings"] >= 1
        assert data["high_count"] >= 1
        assert data["findings"][0]["category"] == "arbitration"
        assert data["findings"][0]["clause_id"] == str(clause_id)


def test_get_document_findings_endpoint(client: TestClient, override_db):
    """Verify GET /api/v1/documents/{document_id}/findings retrieves risk findings."""
    doc_id = uuid.uuid4()
    mock_doc = Document(document_id=doc_id, filename="privacy.pdf")

    with patch("app.api.v1.endpoints.audit.DocumentService.get", return_value=mock_doc), \
         patch("app.api.v1.endpoints.audit.FindingService.list_by_document", return_value=[]):

        res = client.get(f"/api/v1/documents/{doc_id}/findings")
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == str(doc_id)
        assert data["total_findings"] == 0


def test_audit_nonexistent_document(client: TestClient, override_db):
    """Verify auditing a non-existent document ID returns 404."""
    random_id = uuid.uuid4()
    with patch("app.analysis.engine.DocumentService.get", return_value=None):
        res = client.post(f"/api/v1/documents/{random_id}/audit")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()
