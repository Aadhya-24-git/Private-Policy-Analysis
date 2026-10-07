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

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.extraction.exceptions import (
    EmptyDocumentError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    CorruptedFileError,
    ExtractionError,
)
from app.rag.exceptions import (
    DocumentNotFoundError,
    EmptyContextError,
    AIConfigurationError,
    LLMProviderError,
    LLMTimeoutError,
)
from app.core.security import redact_sensitive_string

# Configure Cross-Origin Resource Sharing (CORS) safely
cors_origins = [o.rstrip("/") for o in settings.CORS_ORIGINS] if settings.CORS_ORIGINS else []
# Disallow wildcard CORS in production; disable credentials if wildcard is present per CORS spec
is_wildcard = "*" in cors_origins
if is_wildcard and settings.APP_ENV == "production":
    logger.warning("Wildcard CORS origin '*' detected in production environment! Restricting credentials.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ==============================================================================
# Centralized Error Handlers (No Stack Traces, Passwords, or File Paths Leaked)
# ==============================================================================

@app.exception_handler(EmptyDocumentError)
async def empty_document_handler(request: Request, exc: EmptyDocumentError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "empty_document"},
    )


@app.exception_handler(UnsupportedFileTypeError)
async def unsupported_file_type_handler(request: Request, exc: UnsupportedFileTypeError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "unsupported_file_type"},
    )


@app.exception_handler(FileTooLargeError)
async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    return JSONResponse(
        status_code=413,
        content={"detail": str(exc), "error_type": "file_too_large"},
    )


@app.exception_handler(CorruptedFileError)
async def corrupted_file_handler(request: Request, exc: CorruptedFileError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "corrupted_file"},
    )


@app.exception_handler(ExtractionError)
async def extraction_error_handler(request: Request, exc: ExtractionError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "extraction_error"},
    )


@app.exception_handler(DocumentNotFoundError)
async def document_not_found_handler(request: Request, exc: DocumentNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "error_type": "document_not_found"},
    )


@app.exception_handler(EmptyContextError)
async def empty_context_handler(request: Request, exc: EmptyContextError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "empty_context"},
    )


@app.exception_handler(LLMTimeoutError)
async def llm_timeout_handler(request: Request, exc: LLMTimeoutError):
    safe_detail = redact_sensitive_string(str(exc))
    return JSONResponse(
        status_code=504,
        content={"detail": safe_detail, "error_type": "llm_timeout"},
    )


@app.exception_handler(LLMProviderError)
async def llm_provider_error_handler(request: Request, exc: LLMProviderError):
    safe_detail = redact_sensitive_string(str(exc))
    return JSONResponse(
        status_code=502,
        content={"detail": safe_detail, "error_type": "llm_provider_error"},
    )


@app.exception_handler(AIConfigurationError)
async def ai_configuration_error_handler(request: Request, exc: AIConfigurationError):
    safe_detail = redact_sensitive_string(str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": safe_detail, "error_type": "ai_configuration_error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Sanitize validation errors to avoid leaking internal schema paths
    sanitized_errors = []
    for err in exc.errors():
        field_loc = " -> ".join(str(loc) for loc in err.get("loc", []))
        sanitized_errors.append(f"{field_loc}: {err.get('msg', 'Invalid input')}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed. Please check your submitted parameters.",
            "errors": sanitized_errors,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": redact_sensitive_string(str(exc.detail))},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full exception server-side for diagnostics, redacting credentials
    safe_log = redact_sensitive_string(str(exc))
    logger.error(f"Unhandled server exception on {request.method} {request.url.path}: {safe_log}", exc_info=True)
    # Return generic, safe client response with ZERO stack trace or internal filesystem paths
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "status_code": 500},
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
