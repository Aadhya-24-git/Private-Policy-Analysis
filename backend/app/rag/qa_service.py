import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.services.document_service import DocumentService
from app.services.chat_service import ChatHistoryService
from app.schemas.chat_history import ChatHistoryCreate
from app.schemas.chat import (
    DocumentAskResponse,
    RetrievedClauseSource,
)
from app.llm.base import BaseLLMClient, BaseEmbeddingProvider
from app.llm.provider import get_llm_client
from app.llm.embeddings import get_embedding_provider
from app.rag.retriever import retrieve_relevant_clauses
from app.rag.context import assemble_rag_context
from app.rag.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)

AUDITOR_SYSTEM_PROMPT = """You are the AI-Powered Fine Print Auditor, an expert autonomous legal risk intelligence assistant.
Your mission is to audit and answer user questions regarding terms of service, privacy policies, and legal agreements.

STRICT OPERATIONAL DIRECTIVES:
1. Ground your answers EXCLUSIVELY and ENTIRELY on the provided retrieved policy clauses in the context.
2. If the provided clauses do NOT contain sufficient information to answer the question, you MUST reply:
   "Based on the provided policy clauses, this information is not specified in the document."
   Do NOT speculate, assume, extrapolate, or hallucinate terms not present in the clauses.
3. Always cite specific clauses, sections, page numbers, or paragraph numbers when referencing terms (e.g., "[Clause #3, Section: Data Sharing, Page 2]").
4. Highlight any unfair, predatory, or privacy-invasive terms that are explicitly stated in the cited clauses.
5. Provide concise, clear, and objective plain-language explanations."""


class AuditorQAService:
    """
    Orchestrates document-grounded question answering:
    1. Validates document existence.
    2. Retrieves relevant clauses via pgvector cosine similarity search.
    3. Assembles structured RAG context.
    4. Enforces strict document-grounded synthesis via the configured LLM provider.
    5. Persists the Q&A exchange to the ChatHistory database table.
    """

    @classmethod
    def ask_document(
        cls,
        db: Session,
        document_id: uuid.UUID,
        question: str,
        top_k: int = 5,
        llm_client: Optional[BaseLLMClient] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> DocumentAskResponse:
        cleaned_question = question.strip() if question else ""
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        # 1. Verify document exists
        doc = DocumentService.get(db, document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")

        # 2. Retrieve relevant clauses via pgvector
        clauses = retrieve_relevant_clauses(
            db=db,
            question=cleaned_question,
            document_id=document_id,
            top_k=top_k,
            provider=embedding_provider,
        )

        # 3. Assemble RAG context
        context_text = assemble_rag_context(clauses)

        # 4. Construct prompt
        user_prompt = (
            f"Retrieved Policy Clauses from document '{doc.filename or 'Untitled'}':\n\n"
            f"{context_text}\n\n"
            f"User Question:\n{cleaned_question}\n\n"
            "Audit Analysis & Grounded Answer:"
        )

        # 5. Query configured LLM provider
        client = llm_client or get_llm_client()
        raw_answer = client.generate(
            prompt=user_prompt,
            system_prompt=AUDITOR_SYSTEM_PROMPT,
        )
        answer = raw_answer.strip() if raw_answer else "Based on the provided policy clauses, no answer could be generated."

        # 6. Persist Q&A to ChatHistory
        chat_entry = ChatHistoryService.create(
            db=db,
            chat_in=ChatHistoryCreate(
                document_id=document_id,
                question=cleaned_question,
                answer=answer,
            ),
        )

        # 7. Format sources
        sources = [
            RetrievedClauseSource(
                clause_id=c.clause_id,
                clause_order=c.clause_order,
                section=c.section,
                page_number=c.page_number,
                paragraph_number=c.paragraph_number,
                clause_text=c.clause_text,
            )
            for c in clauses
        ]

        model_info = client.get_model_info()

        return DocumentAskResponse(
            chat_id=chat_entry.chat_id,
            document_id=document_id,
            question=cleaned_question,
            answer=answer,
            sources=sources,
            provider=model_info.get("provider", "unknown"),
            model=model_info.get("model", "unknown"),
            created_at=chat_entry.created_at,
        )

    @classmethod
    async def ask_document_async(
        cls,
        db: Session,
        document_id: uuid.UUID,
        question: str,
        top_k: int = 5,
        llm_client: Optional[BaseLLMClient] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> DocumentAskResponse:
        cleaned_question = question.strip() if question else ""
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        # 1. Verify document exists
        doc = DocumentService.get(db, document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")

        # 2. Retrieve relevant clauses via pgvector
        clauses = retrieve_relevant_clauses(
            db=db,
            question=cleaned_question,
            document_id=document_id,
            top_k=top_k,
            provider=embedding_provider,
        )

        # 3. Assemble RAG context
        context_text = assemble_rag_context(clauses)

        # 4. Construct prompt
        user_prompt = (
            f"Retrieved Policy Clauses from document '{doc.filename or 'Untitled'}':\n\n"
            f"{context_text}\n\n"
            f"User Question:\n{cleaned_question}\n\n"
            "Audit Analysis & Grounded Answer:"
        )

        # 5. Query configured LLM provider asynchronously
        client = llm_client or get_llm_client()
        raw_answer = await client.agenerate(
            prompt=user_prompt,
            system_prompt=AUDITOR_SYSTEM_PROMPT,
        )
        answer = raw_answer.strip() if raw_answer else "Based on the provided policy clauses, no answer could be generated."

        # 6. Persist Q&A to ChatHistory
        chat_entry = ChatHistoryService.create(
            db=db,
            chat_in=ChatHistoryCreate(
                document_id=document_id,
                question=cleaned_question,
                answer=answer,
            ),
        )

        # 7. Format sources
        sources = [
            RetrievedClauseSource(
                clause_id=c.clause_id,
                clause_order=c.clause_order,
                section=c.section,
                page_number=c.page_number,
                paragraph_number=c.paragraph_number,
                clause_text=c.clause_text,
            )
            for c in clauses
        ]

        model_info = client.get_model_info()

        return DocumentAskResponse(
            chat_id=chat_entry.chat_id,
            document_id=document_id,
            question=cleaned_question,
            answer=answer,
            sources=sources,
            provider=model_info.get("provider", "unknown"),
            model=model_info.get("model", "unknown"),
            created_at=chat_entry.created_at,
        )
