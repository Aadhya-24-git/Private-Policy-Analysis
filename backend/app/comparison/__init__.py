from app.comparison.matcher import (
    cosine_similarity,
    lexical_similarity,
    calculate_clause_similarity,
    match_policy_clauses,
)
from app.comparison.explainer import (
    explain_clause_modification,
    explain_added_clause,
    explain_removed_clause,
)
from app.comparison.service import PolicyComparisonService

__all__ = [
    "cosine_similarity",
    "lexical_similarity",
    "calculate_clause_similarity",
    "match_policy_clauses",
    "explain_clause_modification",
    "explain_added_clause",
    "explain_removed_clause",
    "PolicyComparisonService",
]
