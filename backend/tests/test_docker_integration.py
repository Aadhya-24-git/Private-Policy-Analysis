"""
Docker & Full Application Integration Smoke Tests
Verifies that all API contracts, health checks, entrypoint logic,
and service dependencies are properly configured and operational.
"""
import os
import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.database.session import get_db
from app.analysis.engine import RiskAnalysisEngine


@pytest.fixture
def override_db():
    mock_db = MagicMock()

    def mock_add(instance):
        if hasattr(instance, "document_id") and not instance.document_id:
            instance.document_id = uuid.uuid4()
        if hasattr(instance, "clause_id") and not instance.clause_id:
            instance.clause_id = uuid.uuid4()

    def mock_add_all(instances):
        for inst in instances:
            mock_add(inst)

    mock_db.add.side_effect = mock_add
    mock_db.add_all.side_effect = mock_add_all

    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.pop(get_db, None)


def test_root_and_documentation_endpoints(client: TestClient):
    """Verify application root and OpenAPI documentation are exposed and operational."""
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    data = root_resp.json()
    assert data["status"] == "operational"
    assert data["name"] == settings.APP_NAME
    assert data["health"] == "/health"
    assert data["api_v1"] == settings.API_V1_STR

    openapi_resp = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert openapi_resp.status_code == 200
    openapi_spec = openapi_resp.json()
    assert "paths" in openapi_spec
    assert f"{settings.API_V1_STR}/health" in openapi_spec["paths"]
    assert f"{settings.API_V1_STR}/analyze/text" in openapi_spec["paths"]
    assert f"{settings.API_V1_STR}/compare" in openapi_spec["paths"]


def test_health_check_contract_and_db_reporting(client: TestClient):
    """
    Verify /health and /api/v1/health contract.
    Ensure database connectivity status is explicitly reported as 'connected' or 'disconnected',
    and is NEVER falsely reported as healthy when disconnected.
    """
    for endpoint in ["/health", "/api/v1/health"]:
        resp = client.get(endpoint)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "database" in data
        db_data = data["database"]
        assert "status" in db_data
        # Status must be strictly 'connected' or 'disconnected'
        assert db_data["status"] in ("connected", "disconnected")
        if db_data["status"] == "disconnected":
            assert db_data["pgvector_installed"] is False
        assert "ai_subsystem" in data
        assert "provider" in data["ai_subsystem"]


def test_analyze_text_pipeline_schema(client: TestClient, override_db):
    """Verify document ingestion endpoint is structurally wired."""
    payload = {
        "text": "1. You may not cancel your subscription. 2. We share your data with third parties.",
        "filename": "terms_sample.txt",
    }
    resp = client.post("/api/v1/analyze/text", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "document_id" in data
    assert "status" in data
    assert "clauses" in data
    assert len(data["clauses"]) > 0


def test_risk_engine_all_seven_categories_registered():
    """Verify that all seven required risk categories are registered in the engine."""
    engine = RiskAnalysisEngine()
    registered_categories = {d.category_name for d in engine.detectors}
    expected_categories = {
        "auto_renewal",
        "hidden_fees",
        "arbitration",
        "data_sharing",
        "cancellation",
        "data_retention",
        "liability",
    }
    assert expected_categories == registered_categories


def test_docker_configuration_files_exist():
    """Verify all Docker Compose and container configuration files are present in the filesystem."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not os.path.exists(os.path.join(repo_root, "docker-compose.yml")):
        pytest.skip("Repo root files not mounted in container environment")

    required_files = [
        os.path.join(repo_root, "docker-compose.yml"),
        os.path.join(repo_root, ".env.example"),
        os.path.join(repo_root, ".dockerignore"),
        os.path.join(repo_root, "backend", "Dockerfile"),
        os.path.join(repo_root, "backend", ".dockerignore"),
        os.path.join(repo_root, "backend", "scripts", "init-db.sql"),
        os.path.join(repo_root, "backend", "scripts", "entrypoint.sh"),
        os.path.join(repo_root, "frontend", "Dockerfile"),
        os.path.join(repo_root, "frontend", ".dockerignore"),
        os.path.join(repo_root, "frontend", "vite.config.js"),
    ]

    for file_path in required_files:
        assert os.path.isfile(file_path), f"Required Docker configuration file missing: {file_path}"
