from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMClient(ABC):
    """
    Abstract interface for LLM providers.
    Allows seamless hot-swapping between online cloud APIs (OpenAI, Anthropic)
    and offline / local inferencing (Ollama, Qwen GGUF/vLLM).
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Synchronously generate text response."""
        pass

    @abstractmethod
    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Asynchronously generate text response."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return provider and model metadata."""
        pass


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for text embedding providers.
    Supports online APIs and local models (sentence-transformers / HuggingFace).
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text chunk."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text chunks."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return vector dimension."""
        pass
