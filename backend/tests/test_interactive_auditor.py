import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.document import Document, SourceType, DocumentStatus
from app.models.clause import Clause
from app.models.chat_history import ChatHistory
from app.schemas.chat import (
    DocumentAskRequest,
    ChatQuestionRequest,
    DocumentAskResponse,
)
from app.llm.embeddings import (
    OpenAIEmbeddingProvider,
    OllamaEmbeddingProvider,
    get_embedding_provider,
)
from app.llm.provider import (
    OpenAIClient,
    AnthropicClient,
    OllamaClient,
    get_llm_client,
)
from app.rag.context import assemble_rag_context, format_clause_sources
from app.rag.retriever import ensure_document_embeddings, retrieve_relevant_clauses
from app.rag.qa_service import AuditorQAService, AUDITOR_SYSTEM_PROMPT
from app.rag.exceptions import (
    DocumentNotFoundError,
    EmptyContextError,
    AIConfigurationError,
    LLMProviderError,
)
from app.database.session import get_db


# ==============================================================================
# 1. Embedding Provider Tests
# ==============================================================================

def test_openai_embedding_provider_unconfigured():
    """Verify that unconfigured / placeholder API key raises AIConfigurationError."""
    provider = OpenAIEmbeddingProvider(api_key="your_openai_api_key_here")
    with pytest.raises(AIConfigurationError) as exc_info:
        provider.embed_text("Test legal agreement clause")
    assert "missing or set to placeholder" in str(exc_info.value).lower()


def test_openai_embedding_provider_mocked():
    """Verify OpenAI embedding generation for single text and batch with mock."""
    provider = OpenAIEmbeddingProvider(api_key="sk-valid-test-key", model="text-embedding-3-small", dimension=4)

    mock_client = MagicMock()
    # Mock single embedding response
    item_mock = MagicMock()
    item_mock.embedding = [0.1, 0.2, 0.3, 0.4]
    item_mock.index = 0
    mock_resp = MagicMock()
    mock_resp.data = [item_mock]
    mock_client.embeddings.create.return_value = mock_resp

    with patch.object(provider, "_get_client", return_value=mock_client):
        # Single text
        vec = provider.embed_text("Privacy policy clause")
        assert vec == [0.1, 0.2, 0.3, 0.4]

        # Batch texts
        item2 = MagicMock()
        item2.embedding = [0.5, 0.6, 0.7, 0.8]
        item2.index = 1
        mock_resp.data = [item_mock, item2]

        batch_vecs = provider.embed_batch(["Clause 1", "Clause 2"])
        assert len(batch_vecs) == 2
        assert batch_vecs[0] == [0.1, 0.2, 0.3, 0.4]
        assert batch_vecs[1] == [0.5, 0.6, 0.7, 0.8]


def test_ollama_embedding_provider_mocked():
    """Verify Ollama embedding provider parses HTTP responses correctly."""
    provider = OllamaEmbeddingProvider(base_url="http://localhost:11434", model="qwen2.5:7b", dimension=3)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": [[0.11, 0.22, 0.33]]}

    with patch("httpx.post", return_value=mock_response):
        vec = provider.embed_text("Sample clause text")
        assert vec == [0.11, 0.22, 0.33]


# ==============================================================================
# 2. LLM Provider Tests
# ==============================================================================

def test_openai_llm_client_unconfigured():
    """Verify that unconfigured / placeholder API key raises AIConfigurationError."""
    client = OpenAIClient(api_key="your_openai_api_key_here")
    with pytest.raises(AIConfigurationError) as exc_info:
        client.generate("What is the refund policy?")
    assert "missing or set to placeholder" in str(exc_info.value).lower()


def test_openai_llm_client_mocked():
    """Verify OpenAI LLM client synchronous and asynchronous generation."""
    client = OpenAIClient(api_key="sk-test-openai-key", model="gpt-4o-mini")

    # Sync test
    mock_sync_client = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = "All subscriptions renew automatically unless cancelled 24 hours prior."
    mock_resp = MagicMock()
    mock_resp.choices = [choice_mock]
    mock_sync_client.chat.completions.create.return_value = mock_resp

    with patch.object(client, "_get_sync_client", return_value=mock_sync_client):
        answer = client.generate("Explain the billing policy", system_prompt="Audit prompt")
        assert "renew automatically" in answer
        mock_sync_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_sync_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"


@pytest.mark.asyncio
async def test_openai_llm_client_async_mocked():
    """Verify async LLM generation via AsyncOpenAI."""
    client = OpenAIClient(api_key="sk-test-openai-key", model="gpt-4o-mini")

    mock_async_client = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = "Async audit response."
    mock_resp = MagicMock()
    mock_resp.choices = [choice_mock]
    mock_async_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch.object(client, "_get_async_client", return_value=mock_async_client):
        answer = await client.agenerate("Explain arbitration clause", system_prompt="System prompt")
        assert answer == "Async audit response."


def test_ollama_llm_client_mocked():
    """Verify Ollama LLM client HTTP payload formatting and response parsing."""
    client = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:7b")

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"response": "The agreement includes a mandatory arbitration clause."}

    with patch("httpx.post", return_value=mock_res) as mock_post:
        result = client.generate("Analyze dispute resolution", system_prompt="Legal auditor")
        assert "mandatory arbitration" in result
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        assert payload["model"] == "qwen2.5:7b"
        assert payload["system"] == "Legal auditor"


# ==============================================================================
# 3. RAG Context Assembly Tests
# ==============================================================================

def test_assemble_rag_context():
    """Verify structured RAG context assembly from Clause objects."""
    c1 = Clause(
        clause_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=1,
        paragraph_number=3,
        section="Billing & Subscriptions",
        clause_text="Subscriptions renew on a monthly basis automatically.",
        clause_order=0,
    )
    c2 = Clause(
        clause_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=2,
        paragraph_number=5,
        section="Dispute Resolution",
        clause_text="You waive all rights to trial by jury or class action.",
        clause_order=1,
    )

    context = assemble_rag_context([c1, c2])
    assert "[Clause #1 (Section: 'Billing & Subscriptions', Page 1, Paragraph 3)]" in context
    assert "Subscriptions renew on a monthly basis automatically." in context
    assert "[Clause #2 (Section: 'Dispute Resolution', Page 2, Paragraph 5)]" in context
    assert "waive all rights to trial by jury" in context
    assert "---" in context


def test_assemble_rag_context_empty():
    """Verify fallback string when clauses list is empty."""
    assert "No relevant policy clauses found" in assemble_rag_context([])


def test_format_clause_sources():
    """Verify extraction of source citation dictionaries."""
    cid = uuid.uuid4()
    c = Clause(
        clause_id=cid,
        document_id=uuid.uuid4(),
        page_number=3,
        paragraph_number=None,
        section="Data Sharing",
        clause_text="We may share telemetry with trusted advertising partners.",
        clause_order=2,
    )
    sources = format_clause_sources([c])
    assert len(sources) == 1
    assert sources[0]["clause_id"] == cid
    assert sources[0]["section"] == "Data Sharing"
    assert sources[0]["page_number"] == 3
    assert sources[0]["paragraph_number"] is None


# ==============================================================================
# 4. Clause Retrieval & Embedding Sync Tests
# ==============================================================================

def test_ensure_document_embeddings_sync():
    """Verify that unembedded clauses are embedded in batch and updated."""
    doc_id = uuid.uuid4()
    c1 = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        clause_text="Clause text 1",
        clause_order=0,
        embedding=None,
    )
    c2 = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        clause_text="Clause text 2",
        clause_order=1,
        embedding=[0.1, 0.2],  # Already has embedding
    )

    mock_db = MagicMock()
    mock_provider = MagicMock()
    mock_provider.embed_batch.return_value = [[0.9, 0.8]]

    with patch("app.rag.retriever.ClauseService.list_by_document", return_value=[c1, c2]):
        count = ensure_document_embeddings(mock_db, doc_id, provider=mock_provider)
        assert count == 1
        assert c1.embedding == [0.9, 0.8]
        mock_provider.embed_batch.assert_called_once_with(["Clause text 1"])
        mock_db.commit.assert_called_once()


def test_retrieve_relevant_clauses():
    """Verify pgvector cosine similarity search is invoked with question vector."""
    doc_id = uuid.uuid4()
    mock_doc = Document(document_id=doc_id, filename="terms.pdf")
    c1 = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        clause_text="Clause text 1",
        clause_order=0,
        embedding=[0.1, 0.2, 0.3],
    )

    mock_db = MagicMock()
    mock_provider = MagicMock()
    mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]

    with patch("app.rag.retriever.DocumentService.get", return_value=mock_doc), \
         patch("app.rag.retriever.ClauseService.list_by_document", return_value=[c1]), \
         patch("app.rag.retriever.ClauseService.search_similar", return_value=[c1]) as mock_search:
        results = retrieve_relevant_clauses(
            db=mock_db,
            question="What are the subscription terms?",
            document_id=doc_id,
            top_k=3,
            provider=mock_provider,
        )
        assert len(results) == 1
        mock_search.assert_called_once_with(
            db=mock_db,
            query_vector=[0.1, 0.2, 0.3],
            limit=3,
            document_id=doc_id,
        )


def test_retrieve_relevant_clauses_document_not_found():
    """Verify DocumentNotFoundError is raised if document does not exist."""
    mock_db = MagicMock()
    with patch("app.rag.retriever.DocumentService.get", return_value=None):
        with pytest.raises(DocumentNotFoundError):
            retrieve_relevant_clauses(mock_db, "question", uuid.uuid4())


# ==============================================================================
# 5. Document-Grounded Q&A Service Tests
# ==============================================================================

def test_auditor_qa_service_document_grounded():
    """Verify AuditorQAService enforces strict context grounding and persists ChatHistory."""
    doc_id = uuid.uuid4()
    mock_doc = Document(document_id=doc_id, filename="privacy_policy.txt")
    mock_clause = Clause(
        clause_id=uuid.uuid4(),
        document_id=doc_id,
        section="Data Sharing",
        page_number=1,
        paragraph_number=2,
        clause_text="We do not sell personal information to third parties.",
        clause_order=0,
    )

    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Based on [Clause #1, Section: Data Sharing], the policy states that personal information is not sold to third parties."
    mock_llm.get_model_info.return_value = {"provider": "openai", "model": "gpt-4o-mini"}

    mock_chat_entry = ChatHistory(
        chat_id=uuid.uuid4(),
        document_id=doc_id,
        question="Do you sell my data?",
        answer=mock_llm.generate.return_value,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.rag.qa_service.DocumentService.get", return_value=mock_doc), \
         patch("app.rag.qa_service.retrieve_relevant_clauses", return_value=[mock_clause]), \
         patch("app.rag.qa_service.ChatHistoryService.create", return_value=mock_chat_entry) as mock_create_chat:

        response: DocumentAskResponse = AuditorQAService.ask_document(
            db=mock_db,
            document_id=doc_id,
            question="Do you sell my data?",
            top_k=3,
            llm_client=mock_llm,
        )

        assert response.document_id == doc_id
        assert "not sold to third parties" in response.answer
        assert len(response.sources) == 1
        assert response.sources[0].section == "Data Sharing"
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"

        # Verify system prompt enforces grounded directives
        call_kwargs = mock_llm.generate.call_args.kwargs
        assert "EXCLUSIVELY" in call_kwargs["system_prompt"]
        assert "not specified in the document" in call_kwargs["system_prompt"]

        # Verify chat history record was created and saved in PostgreSQL
        mock_create_chat.assert_called_once()
        saved_chat_in = mock_create_chat.call_args.kwargs["chat_in"]
        assert saved_chat_in.document_id == doc_id
        assert saved_chat_in.question == "Do you sell my data?"


# ==============================================================================
# 6. API Endpoint Integration Tests (TestClient)
# ==============================================================================

@pytest.fixture
def override_db():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.pop(get_db, None)


def test_ask_endpoint_success(client: TestClient, override_db):
    """Verify POST /api/v1/documents/{document_id}/ask returns 200 with answers and sources."""
    doc_id = uuid.uuid4()
    mock_response = DocumentAskResponse(
        chat_id=uuid.uuid4(),
        document_id=doc_id,
        question="What is the refund policy?",
        answer="According to Clause #2, refunds are not permitted after 14 days.",
        sources=[
            {
                "clause_id": uuid.uuid4(),
                "clause_order": 1,
                "section": "Refunds",
                "page_number": 2,
                "paragraph_number": 4,
                "clause_text": "Refunds are strictly prohibited after 14 calendar days.",
            }
        ],
        provider="openai",
        model="gpt-4o-mini",
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.api.v1.endpoints.chat.AuditorQAService.ask_document_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = mock_response

        res = client.post(
            f"/api/v1/documents/{doc_id}/ask",
            json={"question": "What is the refund policy?", "top_k": 5},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == str(doc_id)
        assert "refunds are not permitted" in data["answer"].lower()
        assert len(data["sources"]) == 1
        assert data["sources"][0]["section"] == "Refunds"


def test_chat_ask_endpoint_body_param(client: TestClient, override_db):
    """Verify POST /api/v1/chat/ask endpoint accepting document_id in body."""
    doc_id = uuid.uuid4()
    mock_response = DocumentAskResponse(
        chat_id=uuid.uuid4(),
        document_id=doc_id,
        question="Is arbitration required?",
        answer="Clause #4 mandates binding arbitration.",
        sources=[],
        provider="openai",
        model="gpt-4o-mini",
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.api.v1.endpoints.chat.AuditorQAService.ask_document_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = mock_response

        res = client.post(
            "/api/v1/chat/ask",
            json={"document_id": str(doc_id), "question": "Is arbitration required?", "top_k": 3},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == str(doc_id)
        assert "arbitration" in data["answer"].lower()


def test_ask_endpoint_document_not_found(client: TestClient, override_db):
    """Verify non-existent document ID returns 404 Not Found."""
    doc_id = uuid.uuid4()
    with patch(
        "app.api.v1.endpoints.chat.AuditorQAService.ask_document_async",
        side_effect=DocumentNotFoundError(f"Document with ID '{doc_id}' not found."),
    ):
        res = client.post(
            f"/api/v1/documents/{doc_id}/ask",
            json={"question": "Where is my data stored?"},
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


def test_ask_endpoint_unconfigured_api_key(client: TestClient, override_db):
    """Verify unconfigured AI provider returns 503 Service Unavailable."""
    doc_id = uuid.uuid4()
    with patch(
        "app.api.v1.endpoints.chat.AuditorQAService.ask_document_async",
        side_effect=AIConfigurationError("OpenAI API key is missing or set to placeholder."),
    ):
        res = client.post(
            f"/api/v1/documents/{doc_id}/ask",
            json={"question": "What are the privacy terms?"},
        )
        assert res.status_code == 503
        assert "placeholder" in res.json()["detail"].lower()


def test_get_document_chat_history(client: TestClient, override_db):
    """Verify GET /api/v1/documents/{document_id}/chat returns chat records."""
    doc_id = uuid.uuid4()
    mock_doc = Document(document_id=doc_id, filename="test.txt")
    chat_id = uuid.uuid4()
    mock_chat = ChatHistory(
        chat_id=chat_id,
        document_id=doc_id,
        question="What are the payment terms?",
        answer="Payment is required upfront.",
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.api.v1.endpoints.chat.DocumentService.get", return_value=mock_doc), \
         patch("app.api.v1.endpoints.chat.ChatHistoryService.list_by_document", return_value=[mock_chat]):

        res = client.get(f"/api/v1/documents/{doc_id}/chat")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["chat_id"] == str(chat_id)
        assert data[0]["question"] == "What are the payment terms?"
        assert data[0]["answer"] == "Payment is required upfront."
