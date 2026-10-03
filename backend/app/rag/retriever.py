import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.clause import Clause
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.llm.base import BaseEmbeddingProvider
from app.llm.embeddings import get_embedding_provider
from app.rag.exceptions import DocumentNotFoundError, EmptyContextError

logger = logging.getLogger(__name__)


def ensure_document_embeddings(
    db: Session,
    document_id: uuid.UUID,
    provider: Optional[BaseEmbeddingProvider] = None,
) -> int:
    """
    Ensure all clauses for a given document have generated vector embeddings.
    If any clauses have NULL embedding, they are embedded in batch and persisted to PostgreSQL.
    Returns the count of newly embedded clauses.
    """
    clauses = ClauseService.list_by_document(db, document_id)
    unembedded = [c for c in clauses if c.embedding is None]
    if not unembedded:
        return 0

    emb_provider = provider or get_embedding_provider()
    logger.info(f"Generating vector embeddings for {len(unembedded)} clauses of document {document_id}")

    texts = [c.clause_text for c in unembedded]
    vectors = emb_provider.embed_batch(texts)

    for clause, vec in zip(unembedded, vectors):
        clause.embedding = vec

    db.commit()
    for clause in unembedded:
        db.refresh(clause)

    return len(unembedded)


def retrieve_relevant_clauses(
    db: Session,
    question: str,
    document_id: uuid.UUID,
    top_k: int = 5,
    provider: Optional[BaseEmbeddingProvider] = None,
) -> List[Clause]:
    """
    Retrieve the most semantically relevant policy clauses using pgvector cosine similarity search.
    Reuses existing pgvector infrastructure and ClauseService.search_similar.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # 1. Verify document exists
    doc = DocumentService.get(db, document_id)
    if not doc:
        raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")

    # 2. Verify document has clauses
    all_clauses = ClauseService.list_by_document(db, document_id)
    if not all_clauses:
        raise EmptyContextError(f"Document '{document_id}' has no extracted clauses.")

    # 3. Ensure vector embeddings exist for all clauses
    ensure_document_embeddings(db, document_id, provider=provider)

    # 4. Generate query embedding vector
    emb_provider = provider or get_embedding_provider()
    query_vector = emb_provider.embed_text(question.strip())

    # 5. Execute pgvector cosine similarity search via ClauseService
    similar_clauses = ClauseService.search_similar(
        db=db,
        query_vector=query_vector,
        limit=top_k,
        document_id=document_id,
    )

    # 6. Fallback if pgvector returns no results
    if not similar_clauses:
        logger.warning(f"pgvector search returned 0 clauses for doc {document_id}; falling back to ordered clauses.")
        return all_clauses[:top_k]

    return similar_clauses
