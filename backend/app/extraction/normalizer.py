import re
import unicodedata


def clean_and_normalize_text(text: str) -> str:
    """
    Cleans and standardizes raw text extracted from documents:
    - Strips NULL bytes (\x00) which break PostgreSQL text fields.
    - Normalizes Unicode characters into standard NFC format.
    - Standardizes smart quotes, apostrophes, and hyphens/dashes.
    - Cleans excessive horizontal whitespace and tabs.
    - Preserves meaningful paragraph breaks while eliminating excess empty lines.
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize unicode representations
    text = unicodedata.normalize("NFKC", text)

    # Standardize quotation marks and apostrophes
    text = re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb]', '"', text)
    text = re.sub(r'[\u2018\u2019\u201a\u201b\u2032]', "'", text)

    # Standardize dashes and hyphens
    text = re.sub(r'[\u2013\u2014\u2015\u2212]', "-", text)

    # Standardize bullet points
    text = re.sub(r'[\u2022\u2023\u25e6\u2043\u2219]', " - ", text)

    # Replace non-breaking spaces
    text = text.replace("\xa0", " ").replace("\u200b", "")

    # Standardize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace on each line and clear blank lines containing spaces
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[ \t]+$', '', text, flags=re.MULTILINE)

    # Collapse multiple inline spaces/tabs (preserve newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse 3 or more newlines to 2 newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
