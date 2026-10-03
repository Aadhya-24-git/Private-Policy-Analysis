from typing import List, Dict, Any
from app.models.clause import Clause


def assemble_rag_context(clauses: List[Clause]) -> str:
    """
    Format a list of retrieved policy clauses into an unambiguous, highly structured
    context block for document-grounded LLM synthesis.
    """
    if not clauses:
        return "No relevant policy clauses found."

    context_blocks = []
    for clause in clauses:
        meta_parts = []
        if clause.section:
            meta_parts.append(f"Section: '{clause.section}'")
        if clause.page_number is not None:
            meta_parts.append(f"Page {clause.page_number}")
        if clause.paragraph_number is not None:
            meta_parts.append(f"Paragraph {clause.paragraph_number}")

        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""
        header = f"[Clause #{clause.clause_order + 1}{meta_str}]"
        context_blocks.append(f"{header}\n{clause.clause_text.strip()}")

    return "\n\n---\n\n".join(context_blocks)


def format_clause_sources(clauses: List[Clause]) -> List[Dict[str, Any]]:
    """
    Extract citation metadata from retrieved clauses for client presentation.
    """
    return [
        {
            "clause_id": c.clause_id,
            "clause_order": c.clause_order,
            "section": c.section,
            "page_number": c.page_number,
            "paragraph_number": c.paragraph_number,
            "clause_text": c.clause_text,
        }
        for c in clauses
    ]
