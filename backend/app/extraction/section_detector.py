import re
from typing import Optional

# Common standard legal & privacy section keywords
LEGAL_SECTION_KEYWORDS = {
    "OVERVIEW",
    "INTRODUCTION",
    "DEFINITIONS",
    "ELIGIBILITY",
    "ACCOUNT",
    "ACCOUNTS",
    "PRIVACY POLICY",
    "TERMS OF SERVICE",
    "TERMS OF USE",
    "INFORMATION WE COLLECT",
    "PERSONAL INFORMATION",
    "DATA COLLECTION",
    "HOW WE USE YOUR INFORMATION",
    "HOW WE SHARE INFORMATION",
    "COOKIES AND TRACKING",
    "COOKIES",
    "THIRD PARTY SERVICES",
    "DATA RETENTION",
    "SECURITY",
    "USER RIGHTS",
    "YOUR PRIVACY RIGHTS",
    "CALIFORNIA PRIVACY RIGHTS",
    "GDPR COMPLIANCE",
    "CHILDREN'S PRIVACY",
    "PAYMENT TERMS",
    "PAYMENT AND BILLING",
    "BILLING",
    "SUBSCRIPTIONS",
    "CANCELLATION",
    "REFUNDS",
    "TERMINATION",
    "INTELLECTUAL PROPERTY",
    "PROPRIETARY RIGHTS",
    "LICENSE GRANT",
    "USER CONTENT",
    "PROHIBITED CONDUCT",
    "ACCEPTABLE USE",
    "DISCLAIMER OF WARRANTIES",
    "WARRANTIES",
    "LIMITATION OF LIABILITY",
    "INDEMNIFICATION",
    "DISPUTE RESOLUTION",
    "ARBITRATION",
    "CLASS ACTION WAIVER",
    "GOVERNING LAW",
    "JURISDICTION",
    "SEVERABILITY",
    "ENTIRE AGREEMENT",
    "CHANGES TO TERMS",
    "MODIFICATIONS",
    "CONTACT US",
    "CONTACT INFORMATION",
}

# Regex patterns for section titles
SECTION_REGEX_PATTERNS = [
    # Markdown headers: # Header, ## Subheader
    re.compile(r"^#{1,4}\s+(.+)$"),
    # Explicit Section/Article prefixes: Section 1: Intro, Article IV - Terms
    re.compile(r"^(?:Section|Article|Clause|Part)\s+[0-9IVXLCDM]+[:.\-–\s]+(.+)$", re.IGNORECASE),
    # Numbered headers: 1. Overview, 2.1 Information Collected
    re.compile(r"^(\d+(\.\d+)*)\s*[:.\-–\s]\s+([A-Z][A-Za-z0-9\s,&/\-–'\"]{2,70})$"),
    # Lettered headers: A. Information You Provide, B. Automatically Collected
    re.compile(r"^[A-Z]\.\s+([A-Z][A-Za-z0-9\s,&/\-–'\"]{2,70})$"),
]


def detect_section_header(line: str) -> Optional[str]:
    """
    Determines whether a line of text represents a section or heading header.
    Returns the cleaned section title if detected, or None.
    """
    clean_line = line.strip()
    if not clean_line or len(clean_line) < 3 or len(clean_line) > 120:
        return None

    # Do not treat lines ending in regular sentence punctuation as headings
    # (except for short trailing colon or dash)
    if clean_line.endswith(('.', ';', ',')) and not re.match(r'^\d+\.', clean_line):
        return None

    # 1. Check regex patterns
    for pattern in SECTION_REGEX_PATTERNS:
        match = pattern.match(clean_line)
        if match:
            # Extract heading text
            groups = match.groups()
            header_text = groups[-1].strip() if groups else clean_line
            # Normalize title
            return header_text.strip(": -–#")

    # 2. Check uppercase / keyword headings
    upper_line = clean_line.upper().strip(": -–#")
    for keyword in LEGAL_SECTION_KEYWORDS:
        if upper_line == keyword or upper_line.startswith(keyword + " ") or upper_line.endswith(" " + keyword):
            # Return title-cased or uppercase version as section
            return clean_line.strip(": -–#")

    # 3. Check if all-caps short heading line (e.g. "USER OBLIGATIONS")
    if (
        clean_line.isupper()
        and len(clean_line) >= 4
        and len(clean_line) <= 60
        and not any(p in clean_line for p in ('.', '!', '?', ';', '\n'))
        and any(c.isalpha() for c in clean_line)
    ):
        return clean_line.strip(": -–#")

    return None
