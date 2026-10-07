import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Engine with psycopg driver
engine = create_engine(
    settings.sync_database_uri,
    pool_pre_ping=True,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    connect_args={"connect_timeout": 3},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Automatically closes session upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> dict:
    """
    Verify connectivity to PostgreSQL and inspect pgvector extension availability.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            
            # Check for pgvector extension
            vector_check = connection.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()

            has_pgvector = vector_check is not None
            vector_version = vector_check[1] if has_pgvector else None

            return {
                "status": "connected",
                "pgvector_installed": has_pgvector,
                "pgvector_version": vector_version,
                "error": None,
            }
    except Exception as exc:
        from app.core.security import redact_sensitive_string
        safe_msg = redact_sensitive_string(str(exc))
        logger.warning(f"Database connection check failed: {safe_msg}")
        return {
            "status": "disconnected",
            "pgvector_installed": False,
            "pgvector_version": None,
            "error": safe_msg,
        }
