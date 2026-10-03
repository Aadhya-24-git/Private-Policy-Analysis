from typing import List, Tuple
from app.extraction.exceptions import EmptyDocumentError
from app.extraction.segmenter import ClauseSegmenter, ExtractedClause
from app.extraction.normalizer import clean_and_normalize_text


def extract_from_plain_text(raw_text: str) -> Tuple[str, List[ExtractedClause]]:
    """
    Extracts text, preserves paragraph numbers, detects sections, and segments clauses from a direct
    plain-text string (from API request body). Page numbers remain NULL.
    """
    if not raw_text or not raw_text.strip():
        raise EmptyDocumentError("Provided text is empty or contains only whitespace.")

    normalized_full_text = clean_and_normalize_text(raw_text)
    if not normalized_full_text:
        raise EmptyDocumentError("Provided text contains no readable content after cleaning.")

    raw_paras = [p.strip() for p in normalized_full_text.split("\n\n") if p.strip()]
    if not raw_paras:
        raw_paras = [p.strip() for p in normalized_full_text.split("\n") if p.strip()]

    raw_blocks: List[Tuple[str, None, int]] = []
    for idx, para in enumerate(raw_paras):
        raw_blocks.append((para, None, idx + 1))

    segmenter = ClauseSegmenter()
    clauses = segmenter.process_blocks(raw_blocks)

    if not clauses:
        raise EmptyDocumentError("No clauses could be segmented from the provided text.")

    return normalized_full_text, clauses
