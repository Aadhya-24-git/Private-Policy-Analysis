from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.database.session import check_database_connection
from app.schemas.health import HealthResponse, DatabaseHealth, AIConfigSummary

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Confirms that the FastAPI service is running, reports PostgreSQL connectivity, and provides AI subsystem configuration status.",
)
def get_health() -> HealthResponse:
    db_health_info = check_database_connection()

    db_health = DatabaseHealth(
        status=db_health_info["status"],
        pgvector_installed=db_health_info["pgvector_installed"],
        pgvector_version=db_health_info["pgvector_version"],
        error=db_health_info["error"],
    )

    ai_subsystem = AIConfigSummary(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL if settings.AI_PROVIDER in ("openai", "anthropic") else settings.OLLAMA_MODEL,
        embedding_provider=settings.EMBEDDING_PROVIDER,
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
