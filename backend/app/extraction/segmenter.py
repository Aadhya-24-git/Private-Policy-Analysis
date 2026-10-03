from dataclasses import dataclass
from typing import List, Optional, Tuple
import re
from app.extraction.section_detector import detect_section_header
from app.extraction.normalizer import clean_and_normalize_text


@dataclass
class ExtractedClause:
    clause_text: str
    page_number: Optional[int]
    paragraph_number: Optional[int]
    section: Optional[str]
    clause_order: int


class ClauseSegmenter:
    """
    Segments document paragraphs/blocks into structured clauses while preserving
    source references:
    - Page number (for paginated documents like PDF)
    - Paragraph number (for linear documents like DOCX/TXT)
    - Current detected section header
    - Sequential clause ordering
    - Original unadulterated text
    """

    def __init__(self):
        self.current_section: Optional[str] = None
        self.clause_counter: int = 0

    def process_blocks(
        self,
        blocks: List[Tuple[str, Optional[int], Optional[int]]],
    ) -> List[ExtractedClause]:
        """
        Process a list of raw (text, page_number, paragraph_number) blocks.
        Detects headings to establish active section context and outputs ExtractedClauses.
        """
        clauses: List[ExtractedClause] = []

        for text, page_num, para_num in blocks:
            cleaned = clean_and_normalize_text(text)
            if not cleaned:
                continue

            lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
            if not lines:
                continue

            # Case 1: First line is a section header
            first_line_header = detect_section_header(lines[0])
            if first_line_header:
                self.current_section = first_line_header
                # If block was ONLY the header, continue to next block
                if len(lines) == 1:
                    continue
                # Otherwise, the remaining lines represent the clause(s) under this new section
                remaining_text = "\n".join(lines[1:])
            else:
                # Case 2: Check if entire block is a section header
                section_header = detect_section_header(cleaned)
                if section_header:
                    self.current_section = section_header
                    continue
                remaining_text = cleaned

            # Split block into sub-clauses if containing enumerated lists
            sub_clauses = self._split_subclauses(remaining_text)

            for sub_text in sub_clauses:
                sub_clean = sub_text.strip()
                if not sub_clean:
                    continue

                clause = ExtractedClause(
                    clause_text=sub_clean,
                    page_number=page_num,
                    paragraph_number=para_num,
                    section=self.current_section,
                    clause_order=self.clause_counter,
                )
                clauses.append(clause)
                self.clause_counter += 1

        return clauses

    def _split_subclauses(self, text: str) -> List[str]:
        """
        Splits a paragraph into distinct clauses if formatted as numbered or bulleted items,
        otherwise returns the full paragraph as a cohesive clause.
        """
        # Split on newline-delimited list items like:
        # (a) First clause
        # (b) Second clause
        # or 1. First clause \n 2. Second clause
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) <= 1:
            return [text]

        # Check if multiple lines start with list markers
        list_marker_pattern = re.compile(r'^(\([a-zA-Z0-9]+\)|[0-9]+[\.\)]|\u2022|\-|\*)\s+')
        marker_count = sum(1 for line in lines if list_marker_pattern.match(line))

        if marker_count >= 2:
            return lines

        # Otherwise keep paragraph intact
        return [text]
