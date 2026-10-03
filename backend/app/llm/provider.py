import logging
from typing import Any, Dict, Optional
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.rag.exceptions import AIConfigurationError, LLMProviderError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    Online OpenAI LLM provider supporting models such as gpt-4o-mini and gpt-4o.
    Uses official OpenAI Python SDK with both synchronous and asynchronous generation.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.AI_MODEL
        self._sync_client = None
        self._async_client = None

    def _validate_config(self) -> None:
        if not self.api_key or self.api_key.strip() in ("", "your_openai_api_key_here"):
            raise AIConfigurationError(
                "OpenAI API key is missing or set to placeholder. "
                "Please configure a valid OPENAI_API_KEY in your environment."
            )

    def _get_sync_client(self):
        if self._sync_client is None:
            self._validate_config()
            from openai import OpenAI
            self._sync_client = OpenAI(api_key=self.api_key)
        return self._sync_client

    def _get_async_client(self):
        if self._async_client is None:
            self._validate_config()
            from openai import AsyncOpenAI
            self._async_client = AsyncOpenAI(api_key=self.api_key)
        return self._async_client

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        try:
            client = self._get_sync_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            temperature = kwargs.get("temperature", settings.AI_TEMPERATURE)
            max_tokens = kwargs.get("max_tokens", settings.AI_MAX_TOKENS)

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except AIConfigurationError:
            raise
        except Exception as e:
            logger.error(f"OpenAI LLM generate error: {e}")
            raise LLMProviderError(f"OpenAI generation failed: {e}") from e

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        try:
            client = self._get_async_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            temperature = kwargs.get("temperature", settings.AI_TEMPERATURE)
            max_tokens = kwargs.get("max_tokens", settings.AI_MAX_TOKENS)

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except AIConfigurationError:
            raise
        except Exception as e:
            logger.error(f"OpenAI LLM agenerate error: {e}")
            raise LLMProviderError(f"OpenAI async generation failed: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "openai", "model": self.model, "type": "cloud"}


class AnthropicClient(BaseLLMClient):
    """
    Online Anthropic Claude LLM provider via HTTP API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or (settings.AI_MODEL if "claude" in settings.AI_MODEL else "claude-3-5-sonnet-20241022")

    def _validate_config(self) -> None:
        if not self.api_key or self.api_key.strip() in ("", "your_anthropic_api_key_here"):
            raise AIConfigurationError(
                "Anthropic API key is missing or set to placeholder. "
                "Please configure a valid ANTHROPIC_API_KEY in your environment."
            )

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        self._validate_config()
        import httpx
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", settings.AI_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            content_blocks = data.get("content", [])
            return "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise LLMProviderError(f"Anthropic generation failed: {e}") from e

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        self._validate_config()
        import httpx
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", settings.AI_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
                content_blocks = data.get("content", [])
                return "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        except Exception as e:
            logger.error(f"Anthropic async generation error: {e}")
            raise LLMProviderError(f"Anthropic async generation failed: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "anthropic", "model": self.model, "type": "cloud"}


class OllamaClient(BaseLLMClient):
    """
    Local Ollama client for running models such as Qwen2.5, Llama 3, or Mistral privately.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        import httpx
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", settings.AI_TEMPERATURE),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            res = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
            res.raise_for_status()
            return res.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise LLMProviderError(f"Ollama generation failed at {self.base_url}: {e}") from e

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        import httpx
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", settings.AI_TEMPERATURE),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                res.raise_for_status()
                return res.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama async generation error: {e}")
            raise LLMProviderError(f"Ollama async generation failed at {self.base_url}: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "ollama", "model": self.model, "base_url": self.base_url, "type": "local"}


class LocalQwenClient(BaseLLMClient):
    """
    Direct local GGUF / llama-cpp-python client for running Qwen models completely offline.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.LOCAL_MODEL_PATH
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama
                self._llm = Llama(model_path=self.model_path, n_ctx=4096)
            except ImportError:
                raise AIConfigurationError(
                    "llama-cpp-python is not installed. Please install it or set AI_PROVIDER=openai or ollama."
                )
            except Exception as e:
                raise AIConfigurationError(f"Failed to load local GGUF model from {self.model_path}: {e}")
        return self._llm

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        llm = self._get_llm()
        full_prompt = (
            f"<|im_start|>system\n{system_prompt or ''}<|im_end|>\n"
            f"<|im_start|>user\n{prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        try:
            output = llm(full_prompt, max_tokens=kwargs.get("max_tokens", settings.AI_MAX_TOKENS))
            return output["choices"][0]["text"].strip()
        except Exception as e:
            raise LLMProviderError(f"Local Qwen generation error: {e}") from e

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        return self.generate(prompt, system_prompt, **kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "local_qwen", "model_path": self.model_path, "type": "offline_gguf"}


def get_llm_client() -> BaseLLMClient:
    """
    Factory function returning the configured LLM client.
    Can be dynamically switched via AI_PROVIDER in environment variables.
    """
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        return OpenAIClient()
    elif provider == "anthropic":
        return AnthropicClient()
    elif provider == "ollama":
        return OllamaClient()
    elif provider in ("local", "local_qwen", "qwen"):
        return LocalQwenClient()
    else:
        logger.warning(f"Unknown AI_PROVIDER '{provider}', falling back to OpenAIClient")
        return OpenAIClient()
