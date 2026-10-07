import logging
from typing import List, Optional
from app.core.config import settings
from app.llm.base import BaseEmbeddingProvider
from app.rag.exceptions import AIConfigurationError, LLMProviderError

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Online OpenAI embedding provider using the modern OpenAI SDK.
    Configured via settings: EMBEDDING_MODEL (default: text-embedding-3-small)
    and EMBEDDING_DIMENSION (default: 1536).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, dimension: Optional[int] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client = None

    def _validate_config(self) -> None:
        if not self.api_key or self.api_key.strip() in ("", "your_openai_api_key_here"):
            raise AIConfigurationError(
                "OpenAI API key is missing or set to placeholder. "
                "Please configure a valid OPENAI_API_KEY in your environment."
            )

    def _get_client(self):
        if self._client is None:
            self._validate_config()
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        try:
            client = self._get_client()
            response = client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding
        except AIConfigurationError:
            raise
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise LLMProviderError(f"Failed to generate OpenAI embedding: {e}") from e

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            client = self._get_client()
            # Clean empty strings
            cleaned_texts = [t if t and t.strip() else " " for t in texts]
            response = client.embeddings.create(
                input=cleaned_texts,
                model=self.model,
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except AIConfigurationError:
            raise
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise LLMProviderError(f"Failed to generate OpenAI batch embeddings: {e}") from e

    def get_dimension(self) -> int:
        return self.dimension


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama embedding provider for local/private embedding generation.
    Connects to Ollama daemon via HTTP and supports batch embedding via /api/embed.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, dimension: Optional[int] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

    def _get_candidate_urls(self) -> list[str]:
        candidates = [self.base_url]
        if "host.docker.internal" in self.base_url:
            candidates.append(self.base_url.replace("host.docker.internal", "127.0.0.1"))
            candidates.append(self.base_url.replace("host.docker.internal", "localhost"))
        elif "127.0.0.1" in self.base_url or "localhost" in self.base_url:
            alt = self.base_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal")
            candidates.append(alt)
        return candidates

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        embeddings = self.embed_batch([text])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        return [0.0] * self.dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        import httpx
        if not texts:
            return []

        cleaned_texts = [t if t and t.strip() else " " for t in texts]

        last_error = None
        for url in self._get_candidate_urls():
            try:
                # 1. Try modern Ollama /api/embed endpoint supporting batch arrays
                res = httpx.post(
                    f"{url}/api/embed",
                    json={"model": self.model, "input": cleaned_texts},
                    timeout=60.0,
                )
                if res.status_code == 200:
                    data = res.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) == len(cleaned_texts):
                        return embeddings

                # 2. Fallback to /api/embeddings in sequence if /api/embed returned 404
                results = []
                for t in cleaned_texts:
                    res_single = httpx.post(
                        f"{url}/api/embeddings",
                        json={"model": self.model, "prompt": t},
                        timeout=30.0,
                    )
                    res_single.raise_for_status()
                    results.append(res_single.json()["embedding"])
                return results
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_error = e
                logger.debug(f"Could not connect to Ollama embedding endpoint at {url}: {e}")
                continue
            except Exception as e:
                logger.error(f"Ollama embedding error at {url}: {e}")
                raise LLMProviderError(f"Failed to generate Ollama embedding for model '{self.model}': {e}") from e

        raise LLMProviderError(f"Ollama embedding failed: could not connect to candidate endpoints ({self._get_candidate_urls()}): {last_error}")

    def get_dimension(self) -> int:
        return self.dimension


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local HuggingFace / sentence-transformers embeddings for offline processing.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.LOCAL_EMBEDDING_MODEL
        self.dimension = 384
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise AIConfigurationError(
                    "sentence-transformers is not installed. Please install it or set EMBEDDING_PROVIDER=openai."
                )
        return self._model

    def embed_text(self, text: str) -> List[float]:
        model = self._get_model()
        return model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        return model.encode(texts).tolist()

    def get_dimension(self) -> int:
        return self.dimension


def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "local":
        return LocalEmbeddingProvider()
    elif provider == "ollama":
        return OllamaEmbeddingProvider()
    elif provider == "openai":
        return OpenAIEmbeddingProvider()
    else:
        logger.warning(f"Unknown EMBEDDING_PROVIDER '{provider}', falling back to OpenAIEmbeddingProvider")
        return OpenAIEmbeddingProvider()
