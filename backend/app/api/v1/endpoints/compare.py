import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.comparison import PolicyCompareRequest, PolicyCompareResponse
from app.comparison.service import PolicyComparisonService
from app.rag.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/compare",
    response_model=PolicyCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two policy document versions",
    description=(
        "Executes bipartite semantic clause matching between an old policy and a new policy. "
        "Classifies clauses as Added, Removed, Modified, or Unchanged while preserving exact "
        "original text, section headers, and page/paragraph source coordinates."
    ),
)
def compare_policies(
    payload: PolicyCompareRequest,
    db: Session = Depends(get_db),
) -> PolicyCompareResponse:
    try:
        return PolicyComparisonService.compare_documents(
            db=db,
            old_document_id=payload.old_document_id,
            new_document_id=payload.new_document_id,
            explain_changes=payload.explain_changes,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error during policy comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy version comparison failed: {str(e)}",
        )
