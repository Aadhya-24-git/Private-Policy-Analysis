from fastapi.testclient import TestClient
from app.llm.provider import get_llm_client, OpenAIClient, OllamaClient
from app.core.config import settings


def test_root_index(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["name"] == settings.APP_NAME
    assert "health" in data


def test_get_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME
    assert data["version"] == "0.1.0"
    assert "database" in data
    assert "status" in data["database"]
    assert "ai_subsystem" in data
    assert "provider" in data["ai_subsystem"]


def test_get_api_v1_health(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_modular_llm_factory(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    client = get_llm_client()
    assert isinstance(client, OpenAIClient)
    assert client.get_model_info()["provider"] == "openai"

    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    client = get_llm_client()
    assert isinstance(client, OllamaClient)
    assert client.get_model_info()["provider"] == "ollama"
