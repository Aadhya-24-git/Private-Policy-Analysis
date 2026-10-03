from typing import List, Tuple
from app.extraction.exceptions import CorruptedFileError, EmptyDocumentError
from app.extraction.segmenter import ClauseSegmenter, ExtractedClause
from app.extraction.normalizer import clean_and_normalize_text


def extract_from_txt(file_bytes: bytes) -> Tuple[str, List[ExtractedClause]]:
    """
    Extracts text, preserves paragraph numbers, detects sections, and segments clauses from TXT
    bytes. Page numbers remain NULL.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise EmptyDocumentError("The uploaded TXT file is empty (0 bytes).")

    # Attempt decoding across common text encodings
    decoded_text: str | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            decoded_text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise CorruptedFileError("Failed to decode text file. File may be binary or use an unsupported encoding.")

    normalized_full_text = clean_and_normalize_text(decoded_text)
    if not normalized_full_text:
        raise EmptyDocumentError("TXT document contains no readable text.")

    # Split into raw paragraphs based on double newlines or line blocks
    raw_paras = [p.strip() for p in normalized_full_text.split("\n\n") if p.strip()]
    if not raw_paras:
        # Fallback to single line splitting
        raw_paras = [p.strip() for p in normalized_full_text.split("\n") if p.strip()]

    raw_blocks: List[Tuple[str, None, int]] = []
    for idx, para in enumerate(raw_paras):
        raw_blocks.append((para, None, idx + 1))

    segmenter = ClauseSegmenter()
    clauses = segmenter.process_blocks(raw_blocks)

    if not clauses:
        raise EmptyDocumentError("No readable clauses could be extracted from the TXT file.")

    return normalized_full_text, clauses
