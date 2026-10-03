from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import get_health
from app.core.config import settings
from app.schemas.health import HealthResponse
from app.utils.logger import setup_logging
import logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] environment")
    logger.info(f"Configured AI Provider: {settings.AI_PROVIDER}")
    logger.info(f"Database Target: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI-Powered Fine Print Auditor - Phase 0 Foundation",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Direct root-level health endpoint: GET /health
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root Health Check",
    description="Confirm FastAPI is running and inspect PostgreSQL connectivity status.",
)
def root_health() -> HealthResponse:
    return get_health()


# Root index endpoint
@app.get(
    "/",
    tags=["General"],
    summary="Application Root",
)
def root_index():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }


# Direct root-level analyze endpoints: POST /analyze/file, POST /analyze/text
from app.api.v1.endpoints import analyze, chat, audit, compare
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(audit.router)
app.include_router(compare.router)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)





if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
