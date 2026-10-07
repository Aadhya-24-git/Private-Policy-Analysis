import os
import re
import io
import zipfile
from pathlib import Path
from typing import Set, Tuple
from app.extraction.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyDocumentError,
    CorruptedFileError,
)

# Allowed policy file extensions
ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}

# 25 MB default upload limit
MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024

# Maximum allowed filename length
MAX_FILENAME_LENGTH: int = 200

# Executable / dangerous binary magic bytes
DANGEROUS_MAGIC_HEADERS: Tuple[bytes, ...] = (
    b"MZ",              # Windows PE / EXE / DLL
    b"\x7fELF",         # Linux ELF binary
    b"\xca\xfe\xba\xbe", # Mach-O Universal / Java class
    b"\xfe\xed\xfa\xce", # Mach-O 32-bit
    b"\xce\xfa\xed\xfe", # Mach-O 32-bit (reverse)
    b"\xfe\xed\xfa\xcf", # Mach-O 64-bit
    b"\xcf\xfa\xed\xfe", # Mach-O 64-bit (reverse)
    b"#!",              # Unix script shebang
    b"%!PS",            # PostScript executable
)


def sanitize_filename(raw_filename: str) -> str:
    """
    Sanitize an uploaded file's name to prevent path traversal, control character injection,
    and filesystem abuse.
    
    1. Extracts the pure basename (stripping directory paths like / or \\ or ..).
    2. Strips null bytes (\\x00) and ASCII control characters (< 32).
    3. Removes illegal filesystem characters (<, >, :, ", |, ?, *, etc.).
    4. Validates the file extension against allowed types.
    5. Enforces maximum filename length while preserving extension.
    6. Ensures safe fallback if name is empty.
    """
    if not raw_filename or not raw_filename.strip():
        raise EmptyDocumentError("No filename provided.")

    # Strip any null bytes and control chars first
    cleaned = raw_filename.replace("\x00", "")
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

    # Normalize backslashes to forward slashes for cross-platform traversal prevention
    cleaned = cleaned.replace("\\", "/")

    # Extract base name using Path to eliminate path traversal (../, ..\\)
    base_name = Path(cleaned).name

    # Additional regex defense: strip any remaining path separators
    base_name = re.sub(r"[/\\]+", "", base_name)
    base_name = base_name.replace("..", "")

    # Extract extension
    name_part, ext = os.path.splitext(base_name)
    ext_lower = ext.lower().strip()

    if not ext_lower:
        raise UnsupportedFileTypeError(
            "File has no extension. Allowed formats are: .pdf, .docx, and .txt."
        )

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file extension '{ext_lower}'. Allowed formats are: .pdf, .docx, and .txt."
        )

    # Remove illegal characters from name_part
    safe_name_part = re.sub(r'[^a-zA-Z0-9_\-\.\s]', '_', name_part).strip()

    # If the name part was completely erased or was just dots
    safe_name_part = re.sub(r'^\.+', '', safe_name_part).strip()
    if not safe_name_part:
        safe_name_part = "uploaded_policy_document"

    # Truncate length if needed
    allowed_name_len = MAX_FILENAME_LENGTH - len(ext_lower)
    if len(safe_name_part) > allowed_name_len:
        safe_name_part = safe_name_part[:allowed_name_len]

    return f"{safe_name_part}{ext_lower}"


def validate_file_content(filename: str, file_bytes: bytes, max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> None:
    """
    Validate uploaded file content to ensure size limits, MIME/header integrity,
    and prevent masquerading executables or polyglots.
    """
    # 1. Size check
    if not file_bytes or len(file_bytes) == 0:
        raise EmptyDocumentError("The uploaded file is empty (0 bytes).")

    if len(file_bytes) > max_size_bytes:
        raise FileTooLargeError(
            f"File size ({len(file_bytes) / (1024*1024):.2f} MB) exceeds maximum allowed limit ({max_size_bytes / (1024*1024):.0f} MB)."
        )

    # 2. Check for dangerous executable signatures
    for magic in DANGEROUS_MAGIC_HEADERS:
        if file_bytes.startswith(magic):
            raise CorruptedFileError("File contains an executable or script header and cannot be processed.")

    _, ext = os.path.splitext(filename.lower())

    # 3. Format-specific content verification
    if ext == ".pdf":
        # PDF files must contain %PDF- in the initial header
        header_sample = file_bytes[:1024]
        if b"%PDF-" not in header_sample:
            raise CorruptedFileError("Invalid PDF format: file header does not contain standard PDF signature.")

    elif ext == ".docx":
        # DOCX is an OpenXML ZIP container starting with PK\x03\x04
        if not file_bytes.startswith(b"PK\x03\x04"):
            raise CorruptedFileError("Invalid DOCX format: file does not match Microsoft Word ZIP container signature.")

        # Verify ZIP archive structure & check for Zip Slip (path traversal in entry names)
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                # Check for Zip Slip vulnerability
                for member_name in zf.namelist():
                    if ".." in member_name or member_name.startswith("/") or member_name.startswith("\\"):
                        raise CorruptedFileError("DOCX archive contains unsafe path traversal entries.")
                # Verify standard Word XML components exist
                has_word_content = any(
                    name.startswith("word/") or name == "[Content_Types].xml"
                    for name in zf.namelist()
                )
                if not has_word_content:
                    raise CorruptedFileError("Invalid DOCX structure: missing Word processing package components.")
        except zipfile.BadZipFile:
            raise CorruptedFileError("Corrupted DOCX file: unable to read ZIP package.")

    elif ext == ".txt":
        # TXT files should be decodable text without high concentration of binary null bytes
        null_count = file_bytes.count(b"\x00")
        if null_count > 0:
            null_ratio = null_count / len(file_bytes)
            if null_ratio > 0.01:
                raise CorruptedFileError("File appears to be a binary file rather than plain text.")

        # Verify decodability
        decoded = False
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                file_bytes.decode(enc)
                decoded = True
                break
            except UnicodeDecodeError:
                continue

        if not decoded:
            raise CorruptedFileError("Text file could not be decoded with supported character encodings.")


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user textual input (such as Q&A questions) to remove null bytes,
    control characters, and enforce maximum length to prevent resource exhaustion.
    """
    if not text:
        return ""

    # Strip null bytes and control characters (except newline, tab, carriage return)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    cleaned = cleaned.strip()

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()

    return cleaned


def redact_sensitive_string(val: str | None) -> str:
    """
    Redact sensitive information such as database passwords, API keys,
    and secret tokens from strings before logging or returning client errors.
    """
    if not val:
        return ""

    # Redact database password in URLs (postgresql+psycopg://user:password@host:port/db)
    redacted = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", val)
    # Redact OpenAI API keys (sk-...)
    redacted = re.sub(r"sk-[a-zA-Z0-9_\-]{16,}", "sk-***", redacted)
    # Redact Anthropic API keys (sk-ant-...)
    redacted = re.sub(r"sk-ant-[a-zA-Z0-9_\-]{16,}", "sk-ant-***", redacted)
    # Redact password parameter in conninfo: password=xyz
    redacted = re.sub(r"password=\S+", "password=***", redacted)

    return redacted
