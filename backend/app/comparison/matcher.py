import math
from difflib import SequenceMatcher
from typing import List, Tuple, Set, Optional
from app.models.clause import Clause
from app.extraction.normalizer import clean_and_normalize_text


def cosine_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(vec1, vec2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b

    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0

    sim = dot / (math.sqrt(norm1) * math.sqrt(norm2))
    return max(0.0, min(1.0, float(sim)))


def lexical_similarity(text1: str, text2: str) -> float:
    """Calculate normalized character sequence ratio between two strings."""
    t1 = clean_and_normalize_text(text1).lower()
    t2 = clean_and_normalize_text(text2).lower()
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0
    return SequenceMatcher(None, t1, t2).ratio()


def calculate_clause_similarity(c1: Clause, c2: Clause) -> float:
    """
    Compute hybrid similarity between two clauses.
    Uses exact normalized comparison first, then blends embedding cosine distance (if available)
    with lexical sequence matching.
    """
    t1_norm = clean_and_normalize_text(c1.clause_text).lower()
    t2_norm = clean_and_normalize_text(c2.clause_text).lower()

    if t1_norm == t2_norm:
        return 1.0

    lex_sim = SequenceMatcher(None, t1_norm, t2_norm).ratio()

    # If both clauses have embedding vectors, blend semantic and lexical scores
    if c1.embedding is not None and c2.embedding is not None:
        emb_sim = cosine_similarity(c1.embedding, c2.embedding)
        return (0.7 * emb_sim) + (0.3 * lex_sim)

    return lex_sim


def match_policy_clauses(
    old_clauses: List[Clause],
    new_clauses: List[Clause],
    match_threshold: float = 0.55,
) -> Tuple[
    List[Tuple[Clause, Clause]],                # Unchanged pairs
    List[Tuple[Clause, Clause, float]],         # Modified pairs (old, new, score)
    List[Clause],                               # Added clauses
    List[Clause],                               # Removed clauses
]:
    """
    Bipartite semantic clause matching algorithm:
    1. Extracts exact identical matches (Unchanged).
    2. Computes pairwise similarity for remaining clauses.
    3. Greedily pairs highest similarity matches above match_threshold (Modified).
    4. Unpaired new clauses are categorized as Added.
    5. Unpaired old clauses are categorized as Removed.
    """
    unchanged_pairs: List[Tuple[Clause, Clause]] = []
    modified_pairs: List[Tuple[Clause, Clause, float]] = []

    matched_old_ids: Set[object] = set()
    matched_new_ids: Set[object] = set()

    # Pass 1: Identify identical verbatim clauses
    for o in old_clauses:
        o_clean = clean_and_normalize_text(o.clause_text).lower()
        for n in new_clauses:
            if n.clause_id in matched_new_ids:
                continue
            n_clean = clean_and_normalize_text(n.clause_text).lower()
            if o_clean == n_clean:
                unchanged_pairs.append((o, n))
                matched_old_ids.add(o.clause_id)
                matched_new_ids.add(n.clause_id)
                break

    # Pass 2: Pairwise similarity for remaining clauses
    remaining_old = [o for o in old_clauses if o.clause_id not in matched_old_ids]
    remaining_new = [n for n in new_clauses if n.clause_id not in matched_new_ids]

    candidates: List[Tuple[float, Clause, Clause]] = []
    for o in remaining_old:
        for n in remaining_new:
            score = calculate_clause_similarity(o, n)
            if score >= match_threshold:
                candidates.append((score, o, n))

    # Sort candidates by descending similarity score
    candidates.sort(key=lambda x: x[0], reverse=True)

    for score, o, n in candidates:
        if o.clause_id in matched_old_ids or n.clause_id in matched_new_ids:
            continue

        if score >= 0.98:
            unchanged_pairs.append((o, n))
        else:
            modified_pairs.append((o, n, round(score, 3)))

        matched_old_ids.add(o.clause_id)
        matched_new_ids.add(n.clause_id)

    # Pass 3: Added clauses (present in new but not in old)
    added_clauses = [n for n in new_clauses if n.clause_id not in matched_new_ids]

    # Pass 4: Removed clauses (present in old but excised from new)
    removed_clauses = [o for o in old_clauses if o.clause_id not in matched_old_ids]

    return unchanged_pairs, modified_pairs, added_clauses, removed_clauses
