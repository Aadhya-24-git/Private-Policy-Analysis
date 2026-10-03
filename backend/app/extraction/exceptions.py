from fastapi import HTTPException, status


class IngestionException(HTTPException):
    """Base exception for all document ingestion and extraction errors."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class UnsupportedFileTypeError(IngestionException):
    def __init__(self, detail: str = "Unsupported file type. Supported formats are: PDF, DOCX, and TXT."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class EmptyDocumentError(IngestionException):
    def __init__(self, detail: str = "Document is empty or contains no readable text."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class CorruptedFileError(IngestionException):
    def __init__(self, detail: str = "The uploaded file is corrupted or cannot be parsed."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FileTooLargeError(IngestionException):
    def __init__(self, detail: str = "File size exceeds maximum allowed upload limit (25 MB)."):
        super().__init__(status_code=413, detail=detail)


class ExtractionError(IngestionException):
    def __init__(self, detail: str = "An error occurred while extracting content from the document."):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
