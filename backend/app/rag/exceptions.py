class RAGException(Exception):
    """Base exception for RAG and Auditor operations."""
    pass


class DocumentNotFoundError(RAGException):
    """Raised when the specified document ID does not exist."""
    pass


class EmptyContextError(RAGException):
    """Raised when no context clauses are found for the document."""
    pass


class AIConfigurationError(RAGException):
    """Raised when an AI or embedding provider is improperly configured."""
    pass


class LLMProviderError(RAGException):
    """Raised when an external LLM provider encounters an error."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM provider request times out."""
    pass
