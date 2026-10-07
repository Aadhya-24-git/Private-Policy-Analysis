#!/usr/bin/env python3
"""
Re-indexes all policy clauses in PostgreSQL with NULL embeddings
using the active embedding provider (default: Ollama qwen3-embedding:0.6b, 1024 dimensions).
Safe to run multiple times; only processes clauses that have not yet been embedded.
"""
import sys
import os
import logging

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reindex_embeddings")


def main():
    try:
        from app.database.session import SessionLocal
        from app.rag.retriever import reindex_all_unembedded_clauses

        db = SessionLocal()
        try:
            logger.info("Checking for unembedded policy clauses to re-index...")
            count = reindex_all_unembedded_clauses(db)
            logger.info(f"Re-indexing complete. Total clauses embedded: {count}")
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"Re-indexing encountered an issue: {exc}. Clauses will be embedded lazily during search.")
        sys.exit(0)


if __name__ == "__main__":
    main()
