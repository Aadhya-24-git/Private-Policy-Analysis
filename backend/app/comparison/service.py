import logging
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.services.document_service import DocumentService
from app.services.clause_service import ClauseService
from app.schemas.comparison import (
    ClauseSourceInfo,
    ModifiedClauseComparison,
    AddedClauseComparison,
    RemovedClauseComparison,
    PolicyCompareSummary,
    PolicyCompareResponse,
)
from app.comparison.matcher import match_policy_clauses
from app.comparison.explainer import (
    explain_clause_modification,
    explain_added_clause,
    explain_removed_clause,
)
from app.rag.exceptions import DocumentNotFoundError
from app.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class PolicyComparisonService:
    """
    Orchestrates semantic policy version comparison:
    1. Validates existence of both document versions.
    2. Retrieves segmented clauses.
    3. Executes bipartite semantic clause matching.
    4. Categorizes clauses into Added, Removed, Modified, and Unchanged.
    5. Synthesizes neutral, grounded explanations for modified clauses.
    """

    @classmethod
    def compare_documents(
        cls,
        db: Session,
        old_document_id: uuid.UUID,
        new_document_id: uuid.UUID,
        explain_changes: bool = True,
        llm_client: Optional[BaseLLMClient] = None,
    ) -> PolicyCompareResponse:
        # 1. Fetch documents
        old_doc = DocumentService.get(db, old_document_id)
        if not old_doc:
            raise DocumentNotFoundError(f"Previous policy document with ID '{old_document_id}' not found.")

        new_doc = DocumentService.get(db, new_document_id)
        if not new_doc:
            raise DocumentNotFoundError(f"Updated policy document with ID '{new_document_id}' not found.")

        old_clauses = ClauseService.list_by_document(db, old_document_id)
        new_clauses = ClauseService.list_by_document(db, new_document_id)

        # 2. Check for identical document IDs
        if old_document_id == new_document_id:
            summary = PolicyCompareSummary(
                total_old_clauses=len(old_clauses),
                total_new_clauses=len(new_clauses),
                added_count=0,
                removed_count=0,
                modified_count=0,
                unchanged_count=len(old_clauses),
                overview="Identical document comparison: Both versions contain identical clauses with zero additions, removals, or modifications.",
            )
            return PolicyCompareResponse(
                old_document_id=old_document_id,
                new_document_id=new_document_id,
                old_document_name=old_doc.filename or "Previous Policy",
                new_document_name=new_doc.filename or "Updated Policy",
                summary=summary,
                modified_clauses=[],
                added_clauses=[],
                removed_clauses=[],
                unchanged_count=len(old_clauses),
            )

        # 3. Execute semantic clause matching
        unchanged_pairs, modified_pairs, added, removed = match_policy_clauses(
            old_clauses=old_clauses,
            new_clauses=new_clauses,
        )

        # 4. Format Modified clauses
        modified_items: List[ModifiedClauseComparison] = []
        for o_clause, n_clause, score in modified_pairs:
            explanation = None
            if explain_changes:
                explanation = explain_clause_modification(
                    old_text=o_clause.clause_text,
                    new_text=n_clause.clause_text,
                    llm_client=llm_client,
                )

            modified_items.append(
                ModifiedClauseComparison(
                    old_clause=ClauseSourceInfo.model_validate(o_clause),
                    new_clause=ClauseSourceInfo.model_validate(n_clause),
                    similarity_score=score,
                    change_type="modified",
                    explanation=explanation,
                )
            )

        # 5. Format Added clauses
        added_items: List[AddedClauseComparison] = [
            AddedClauseComparison(
                new_clause=ClauseSourceInfo.model_validate(c),
                change_type="added",
                explanation=explain_added_clause(c.clause_text) if explain_changes else None,
            )
            for c in added
        ]

        # 6. Format Removed clauses
        removed_items: List[RemovedClauseComparison] = [
            RemovedClauseComparison(
                old_clause=ClauseSourceInfo.model_validate(c),
                change_type="removed",
                explanation=explain_removed_clause(c.clause_text) if explain_changes else None,
            )
            for c in removed
        ]

        # 7. Generate overview summary
        unchanged_count = len(unchanged_pairs)
        overview_parts = []
        if modified_items:
            overview_parts.append(f"{len(modified_items)} modified clauses")
        if added_items:
            overview_parts.append(f"{len(added_items)} newly added clauses")
        if removed_items:
            overview_parts.append(f"{len(removed_items)} removed clauses")
        if unchanged_count:
            overview_parts.append(f"{unchanged_count} unchanged clauses")

        if not overview_parts:
            overview = "No substantive textual differences identified between the two policy versions."
        else:
            overview = f"Policy comparison identified {', '.join(overview_parts)} between versions."

        summary = PolicyCompareSummary(
            total_old_clauses=len(old_clauses),
            total_new_clauses=len(new_clauses),
            added_count=len(added_items),
            removed_count=len(removed_items),
            modified_count=len(modified_items),
            unchanged_count=unchanged_count,
            overview=overview,
        )

        return PolicyCompareResponse(
            old_document_id=old_document_id,
            new_document_id=new_document_id,
            old_document_name=old_doc.filename or "Previous Policy",
            new_document_name=new_doc.filename or "Updated Policy",
            summary=summary,
            modified_clauses=modified_items,
            added_clauses=added_items,
            removed_clauses=removed_items,
            unchanged_count=unchanged_count,
        )
