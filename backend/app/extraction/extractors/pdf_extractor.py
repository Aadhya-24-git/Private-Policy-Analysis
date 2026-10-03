from typing import List, Tuple
import fitz  # PyMuPDF
from app.extraction.exceptions import CorruptedFileError, EmptyDocumentError, ExtractionError
from app.extraction.segmenter import ClauseSegmenter, ExtractedClause
from app.extraction.normalizer import clean_and_normalize_text


def extract_from_pdf(file_bytes: bytes) -> Tuple[str, List[ExtractedClause]]:
    """
    Extracts text, preserves page numbers, detects sections, and segments clauses from PDF bytes
    using PyMuPDF.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise EmptyDocumentError("The uploaded PDF file is empty (0 bytes).")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except fitz.FileDataError as e:
        raise CorruptedFileError(f"Corrupted or invalid PDF file: {str(e)}")
    except Exception as e:
        raise ExtractionError(f"Failed to open PDF document: {str(e)}")

    if doc.page_count == 0:
        doc.close()
        raise EmptyDocumentError("PDF document has 0 pages.")

    raw_blocks: List[Tuple[str, int, None]] = []
    full_text_parts: List[str] = []

    try:
        for page_idx in range(doc.page_count):
            page = doc[page_idx]
            page_number = page_idx + 1

            # Extract layout-aware blocks (text, block_no, etc.)
            blocks = page.get_text("blocks")
            for b in blocks:
                # b = (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 is text, 1 is image
                if len(b) >= 5 and (len(b) < 7 or b[6] == 0):
                    block_text = b[4].strip()
                    if block_text:
                        raw_blocks.append((block_text, page_number, None))
                        full_text_parts.append(block_text)
    except Exception as e:
        doc.close()
        raise ExtractionError(f"Error reading PDF page contents: {str(e)}")
    finally:
        doc.close()

    combined_text = "\n\n".join(full_text_parts)
    normalized_full_text = clean_and_normalize_text(combined_text)

    if not normalized_full_text:
        raise EmptyDocumentError("PDF document contains no readable text (may be image-only or scanned).")

    segmenter = ClauseSegmenter()
    clauses = segmenter.process_blocks(raw_blocks)

    if not clauses:
        raise EmptyDocumentError("No readable clauses could be extracted from the PDF.")

    return normalized_full_text, clauses
