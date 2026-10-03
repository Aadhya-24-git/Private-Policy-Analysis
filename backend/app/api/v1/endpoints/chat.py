import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.chat import (
    DocumentAskRequest,
    ChatQuestionRequest,
    DocumentAskResponse,
)
from app.schemas.chat_history import ChatHistoryResponse
from app.services.chat_service import ChatHistoryService
from app.services.document_service import DocumentService
from app.rag.qa_service import AuditorQAService
from app.rag.exceptions import (
    DocumentNotFoundError,
    EmptyContextError,
    AIConfigurationError,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/documents/{document_id}/ask",
    response_model=DocumentAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about a document",
    description=(
        "Retrieves relevant clauses using pgvector semantic search and generates a strictly "
        "document-grounded answer using the configured LLM provider. Persists the exchange in chat history."
    ),
)
async def ask_document_endpoint(
    document_id: uuid.UUID,
    payload: DocumentAskRequest,
    db: Session = Depends(get_db),
) -> DocumentAskResponse:
    try:
        return await AuditorQAService.ask_document_async(
            db=db,
            document_id=document_id,
            question=payload.question,
            top_k=payload.top_k,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmptyContextError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AIConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except LLMProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in ask_document_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during document audit: {str(e)}",
        )


@router.post(
    "/chat/ask",
    response_model=DocumentAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about a document (body parameter)",
    description="Alternative endpoint accepting document_id within the JSON request body.",
)
async def chat_ask_endpoint(
    payload: ChatQuestionRequest,
    db: Session = Depends(get_db),
) -> DocumentAskResponse:
    try:
        return await AuditorQAService.ask_document_async(
            db=db,
            document_id=payload.document_id,
            question=payload.question,
            top_k=payload.top_k,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmptyContextError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AIConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except LLMProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat_ask_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during document audit: {str(e)}",
        )


@router.get(
    "/documents/{document_id}/chat",
    response_model=List[ChatHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve document chat history",
    description="Fetches chronological audit Q&A history for a specific document.",
)
def get_document_chat_history(
    document_id: uuid.UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[ChatHistoryResponse]:
    doc = DocumentService.get(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return ChatHistoryService.list_by_document(db, document_id, limit=limit)
