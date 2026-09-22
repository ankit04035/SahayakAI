"""
OpenAI-Compatible AI Provider Implementation.
Integrates with official OpenAI API and compatible local/cloud engines (Ollama, vLLM, Groq).
Provides strict timeout handling, credential protection, and structured exception mapping.
"""

import logging
import time
from typing import Any, Dict, List, Optional
import openai
from openai import OpenAI

from backend.app.providers.base import BaseAIProvider
from backend.app.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
    sanitize_sensitive_data,
)
from backend.app.providers.models import ProviderResponse, UsageMetadata

logger = logging.getLogger("sahayakai.providers.openai")


class OpenAICompatibleProvider(BaseAIProvider):
    """
    Production adapter for OpenAI and OpenAI-compatible inference servers.
    Ensures safe handling of API keys, configurable endpoints, and robust error translation.
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        timeout: float = 30.0,
    ):
        if not api_key or not str(api_key).strip():
            raise ProviderConfigurationError("OPENAI_API_KEY is required for OpenAICompatibleProvider.")

        self._api_key = str(api_key).strip()
        self._base_url = str(base_url).strip() if base_url and str(base_url).strip() else None
        self._default_model = default_model or "gpt-4o-mini"
        self._timeout = max(1.0, float(timeout))
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self) -> OpenAI:
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=0,  # Controlled retries managed by provider layer
            )
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        start_time = time.perf_counter()
        client = self._get_client()

        # Build message payload
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Sanitize parameters
        model_name = kwargs.pop("model", self._default_model)
        request_params: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
        }
        if temperature is not None:
            request_params["temperature"] = float(temperature)
        if max_tokens is not None:
            request_params["max_tokens"] = int(max_tokens)
        request_params.update(kwargs)

        try:
            logger.info("Calling OpenAI-compatible endpoint with model '%s'", model_name)
            response = client.chat.completions.create(**request_params)
        except openai.AuthenticationError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("OpenAI authentication failure: %s", sanitized)
            raise ProviderAuthenticationError(f"OpenAI authentication failed: {sanitized}") from exc
        except openai.APITimeoutError as exc:
            logger.error("OpenAI request timed out after %.1fs", self._timeout)
            raise ProviderTimeoutError(f"OpenAI request timed out after {self._timeout}s.") from exc
        except openai.BadRequestError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("OpenAI invalid request: %s", sanitized)
            raise ProviderRequestError(f"OpenAI invalid request: {sanitized}") from exc
        except openai.RateLimitError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("OpenAI rate limit reached: %s", sanitized)
            raise ProviderRequestError(f"OpenAI rate limit exceeded: {sanitized}") from exc
        except openai.APIConnectionError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("OpenAI connection error: %s", sanitized)
            raise ProviderRequestError(f"OpenAI connection error: {sanitized}") from exc
        except openai.APIStatusError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("OpenAI status error [%s]: %s", exc.status_code, sanitized)
            if exc.status_code in {401, 403}:
                raise ProviderAuthenticationError(f"OpenAI authorization failed: {sanitized}") from exc
            raise ProviderRequestError(f"OpenAI request failed: {sanitized}") from exc
        except Exception as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("Unexpected error during OpenAI request: %s", sanitized, exc_info=False)
            raise ProviderRequestError(f"OpenAI provider failure: {sanitized}") from exc

        # Validate response format
        if not response.choices:
            raise ProviderResponseError("OpenAI returned an empty choice list.")

        choice = response.choices[0]
        generated_content = choice.message.content
        if generated_content is None:
            raise ProviderResponseError("OpenAI completion content was null.")

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Extract token usage
        usage_data = None
        if response.usage:
            usage_data = UsageMetadata(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return ProviderResponse(
            generated_text=generated_content,
            provider="openai",
            model=response.model or model_name,
            usage=usage_data,
            finish_reason=choice.finish_reason,
            latency_ms=latency_ms,
            metadata={
                "is_demo": False,
                "base_url": self._base_url,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
