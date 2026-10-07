from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter
import httpx
from app.core.config import settings
from app.database.session import check_database_connection
from app.schemas.health import HealthResponse, DatabaseHealth, AIConfigSummary, OllamaDiagnostics
from app.core.security import redact_sensitive_string

logger = logging.getLogger(__name__)
router = APIRouter()


def check_ollama_diagnostics(
    base_url: str,
    chat_model: str,
    embedding_model: str,
) -> OllamaDiagnostics:
    """
    Probe the local Ollama daemon to verify:
    1. HTTP reachability
    2. Availability of configured chat model (e.g. qwen3:4b)
    3. Availability of configured embedding model (e.g. qwen3-embedding:0.6b)
    """
    candidates = [base_url]
    if "host.docker.internal" in base_url:
        candidates.append(base_url.replace("host.docker.internal", "127.0.0.1"))
        candidates.append(base_url.replace("host.docker.internal", "localhost"))
    elif "127.0.0.1" in base_url or "localhost" in base_url:
        candidates.append(base_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal"))

    last_error = None
    for url in candidates:
        try:
            res = httpx.get(f"{url.rstrip('/')}/api/tags", timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                raw_models = data.get("models", [])
                model_names = [m.get("name", "") for m in raw_models if m.get("name")]

                def model_matches(target: str, available_list: list[str]) -> bool:
                    target_clean = target.lower().strip()
                    target_prefix = target_clean.split(":")[0]
                    for m in available_list:
                        m_clean = m.lower().strip()
                        if target_clean == m_clean or m_clean.startswith(f"{target_prefix}:"):
                            return True
                    return False

                chat_ok = model_matches(chat_model, model_names)
                embed_ok = model_matches(embedding_model, model_names)

                return OllamaDiagnostics(
                    reachable=True,
                    base_url=url,
                    chat_model=chat_model,
                    chat_model_available=chat_ok,
                    embedding_model=embedding_model,
                    embedding_model_available=embed_ok,
                    available_models=model_names,
                    error=None,
                )
        except Exception as e:
            last_error = e
            continue

    safe_error = redact_sensitive_string(str(last_error)) if last_error else "Connection refused"
    return OllamaDiagnostics(
        reachable=False,
        base_url=base_url,
        chat_model=chat_model,
        chat_model_available=False,
        embedding_model=embedding_model,
        embedding_model_available=False,
        available_models=[],
        error=safe_error,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Confirms that the FastAPI service is running, reports PostgreSQL connectivity, pgvector status, and AI/Ollama diagnostics.",
)
def get_health() -> HealthResponse:
    db_health_info = check_database_connection()

    db_health = DatabaseHealth(
        status=db_health_info["status"],
        pgvector_installed=db_health_info["pgvector_installed"],
        pgvector_version=db_health_info["pgvector_version"],
        error=db_health_info["error"],
    )

    ollama_diag: Optional[OllamaDiagnostics] = None
    if settings.AI_PROVIDER == "ollama" or settings.EMBEDDING_PROVIDER == "ollama":
        ollama_diag = check_ollama_diagnostics(
            base_url=settings.OLLAMA_BASE_URL,
            chat_model=settings.AI_MODEL,
            embedding_model=settings.EMBEDDING_MODEL,
        )

    ai_subsystem = AIConfigSummary(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        ollama_diagnostics=ollama_diag,
    )

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
        database=db_health,
        ai_subsystem=ai_subsystem,
    )
