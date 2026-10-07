import logging
from typing import Any, Dict, Optional
from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.rag.exceptions import AIConfigurationError, LLMProviderError, LLMTimeoutError
from app.llm.scaffolding import clean_model_scaffolding

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
    Local Ollama client for running models such as Qwen (e.g. qwen3:4b) privately.
    Supports /api/chat with fallback to /api/generate and automatic network resolution.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.AI_MODEL or settings.OLLAMA_MODEL
        self.timeout = float(timeout if timeout is not None else settings.OLLAMA_TIMEOUT)

    def _get_candidate_urls(self) -> list[str]:
        candidates = [self.base_url]
        if "host.docker.internal" in self.base_url:
            candidates.append(self.base_url.replace("host.docker.internal", "127.0.0.1"))
            candidates.append(self.base_url.replace("host.docker.internal", "localhost"))
        elif "127.0.0.1" in self.base_url or "localhost" in self.base_url:
            alt = self.base_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal")
            candidates.append(alt)
        return candidates

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        prefill_answer = kwargs.get("prefill_answer", False)
        if prefill_answer:
            messages.append({"role": "assistant", "content": "Answer:\n"})

        options = {
            "temperature": kwargs.get("temperature", settings.AI_TEMPERATURE),
            "num_predict": kwargs.get("num_predict", kwargs.get("max_tokens", 450)),
        }
        if "stop" in kwargs:
            options["stop"] = kwargs["stop"]
        else:
            options["stop"] = ["<|im_end|>", "<|im_start|>", "<think>", "\nuser\n", "\nContext:"]

        payload = {
            "model": self.model,
            "prompt": prompt,
            "messages": messages,
            "stream": False,
            "think": kwargs.get("think", False),
            "options": options,
        }
        if system_prompt:
            payload["system"] = system_prompt

        timeout_config = httpx.Timeout(timeout=self.timeout, connect=5.0)
        last_error = None
        for url in self._get_candidate_urls():
            try:
                # 1. Post to Ollama /api/chat (optimized for Qwen conversational reasoning)
                res = httpx.post(f"{url}/api/chat", json=payload, timeout=timeout_config)
                if res.status_code == 200:
                    data = res.json()
                    content = ""
                    if isinstance(data.get("message"), dict):
                        content = data["message"].get("content", "")
                    if not content and "response" in data:
                        content = data.get("response", "")
                    if not content and "thinking" in data:
                        raw_thinking = data.get("thinking", "")
                        if "answer:" in raw_thinking.lower():
                            content = raw_thinking
                    if content:
                        if prefill_answer and not content.strip().lower().startswith("answer:"):
                            content = "Answer:\n" + content.lstrip()
                        return clean_model_scaffolding(content)

                # 2. Fallback to /api/generate if /api/chat returned 404
                if res.status_code == 404:
                    res_gen = httpx.post(f"{url}/api/generate", json=payload, timeout=timeout_config)
                    res_gen.raise_for_status()
                    gen_data = res_gen.json()
                    raw = gen_data.get("response", "") or (
                        gen_data.get("message", {}).get("content", "")
                        if isinstance(gen_data.get("message"), dict)
                        else ""
                    )
                    if prefill_answer and raw and not raw.strip().lower().startswith("answer:"):
                        raw = "Answer:\n" + raw.lstrip()
                    return clean_model_scaffolding(raw)

                res.raise_for_status()
                data = res.json()
                raw = data.get("response", "") or (
                    data.get("message", {}).get("content", "")
                    if isinstance(data.get("message"), dict)
                    else ""
                )
                if prefill_answer and raw and not raw.strip().lower().startswith("answer:"):
                    raw = "Answer:\n" + raw.lstrip()
                return clean_model_scaffolding(raw)
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_error = e
                logger.debug(f"Could not connect to Ollama at {url}: {e}. Trying fallback candidates...")
                continue
            except httpx.ReadTimeout as e:
                logger.error(f"Ollama generation timed out after {self.timeout}s at {url}: {e}")
                raise LLMTimeoutError(
                    f"Ollama model '{self.model}' generation timed out after {int(self.timeout)} seconds. "
                    "The legal document analysis took longer than expected to complete. "
                    "Please retry with a more specific question, or increase OLLAMA_TIMEOUT in your environment."
                ) from e
            except httpx.TimeoutException as e:
                logger.error(f"Ollama request timed out after {self.timeout}s at {url}: {e}")
                raise LLMTimeoutError(
                    f"Ollama request timed out after {int(self.timeout)} seconds: {e}"
                ) from e
            except Exception as e:
                logger.error(f"Ollama generation error at {url}: {e}")
                raise LLMProviderError(f"Ollama generation failed with model '{self.model}': {e}") from e

        raise LLMProviderError(f"Ollama generation failed: could not connect to candidate endpoints ({self._get_candidate_urls()}): {last_error}")

    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        prefill_answer = kwargs.get("prefill_answer", False)
        if prefill_answer:
            messages.append({"role": "assistant", "content": "Answer:\n"})

        options = {
            "temperature": kwargs.get("temperature", settings.AI_TEMPERATURE),
            "num_predict": kwargs.get("num_predict", kwargs.get("max_tokens", 450)),
        }
        if "stop" in kwargs:
            options["stop"] = kwargs["stop"]
        else:
            options["stop"] = ["<|im_end|>", "<|im_start|>", "<think>", "\nuser\n", "\nContext:"]

        payload = {
            "model": self.model,
            "prompt": prompt,
            "messages": messages,
            "stream": False,
            "think": kwargs.get("think", False),
            "options": options,
        }
        if system_prompt:
            payload["system"] = system_prompt

        timeout_config = httpx.Timeout(timeout=self.timeout, connect=5.0)
        last_error = None
        for url in self._get_candidate_urls():
            try:
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    res = await client.post(f"{url}/api/chat", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        content = ""
                        if isinstance(data.get("message"), dict):
                            content = data["message"].get("content", "")
                        if not content and "response" in data:
                            content = data.get("response", "")
                        if not content and "thinking" in data:
                            raw_thinking = data.get("thinking", "")
                            if "answer:" in raw_thinking.lower():
                                content = raw_thinking
                        if content:
                            if prefill_answer and not content.strip().lower().startswith("answer:"):
                                content = "Answer:\n" + content.lstrip()
                            return clean_model_scaffolding(content)

                    if res.status_code == 404:
                        res_gen = await client.post(f"{url}/api/generate", json=payload)
                        res_gen.raise_for_status()
                        gen_data = res_gen.json()
                        raw = gen_data.get("response", "") or (
                            gen_data.get("message", {}).get("content", "")
                            if isinstance(gen_data.get("message"), dict)
                            else ""
                        )
                        if prefill_answer and raw and not raw.strip().lower().startswith("answer:"):
                            raw = "Answer:\n" + raw.lstrip()
                        return clean_model_scaffolding(raw)

                    res.raise_for_status()
                    data = res.json()
                    raw = data.get("response", "") or (
                        data.get("message", {}).get("content", "")
                        if isinstance(data.get("message"), dict)
                        else ""
                    )
                    if prefill_answer and raw and not raw.strip().lower().startswith("answer:"):
                        raw = "Answer:\n" + raw.lstrip()
                    return clean_model_scaffolding(raw)
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_error = e
                logger.debug(f"Could not connect to Ollama at {url}: {e}. Trying fallback candidates...")
                continue
            except httpx.ReadTimeout as e:
                logger.error(f"Ollama async generation timed out after {self.timeout}s at {url}: {e}")
                raise LLMTimeoutError(
                    f"Ollama model '{self.model}' generation timed out after {int(self.timeout)} seconds. "
                    "The legal document analysis took longer than expected to complete. "
                    "Please retry with a more specific question, or increase OLLAMA_TIMEOUT in your environment."
                ) from e
            except httpx.TimeoutException as e:
                logger.error(f"Ollama async request timed out after {self.timeout}s at {url}: {e}")
                raise LLMTimeoutError(
                    f"Ollama request timed out after {int(self.timeout)} seconds: {e}"
                ) from e
            except Exception as e:
                logger.error(f"Ollama async generation error at {url}: {e}")
                raise LLMProviderError(f"Ollama async generation failed with model '{self.model}': {e}") from e

        raise LLMProviderError(f"Ollama async generation failed: could not connect to candidate endpoints: {last_error}")

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "type": "local",
        }


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
