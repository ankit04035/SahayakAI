"""
Google Gemini AI Provider Implementation.
Integrates with the official Google GenAI SDK (`google.genai`).
Provides timeout controls, token accounting, and controlled exception mapping without secret leakage.
"""

import logging
import time
from typing import Any, Dict, Optional
from google import genai
from google.genai import errors, types

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

logger = logging.getLogger("sahayakai.providers.gemini")


class GeminiProvider(BaseAIProvider):
    """
    Production adapter for Google Gemini multimodal language models.
    Translates Google GenAI SDK responses into standardized ProviderResponse models.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gemini-1.5-flash",
        timeout: float = 30.0,
    ):
        if not api_key or not str(api_key).strip():
            raise ProviderConfigurationError("GEMINI_API_KEY is required for GeminiProvider.")

        self._api_key = str(api_key).strip()
        self._default_model = default_model or "gemini-1.5-flash"
        self._timeout = max(1.0, float(timeout))
        self._client: Optional[genai.Client] = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self) -> genai.Client:
        """Lazily initialize the official Google GenAI client."""
        if self._client is None:
            # Set timeout in milliseconds via HttpOptions
            http_opts = types.HttpOptions(timeout=int(self._timeout * 1000))
            self._client = genai.Client(
                api_key=self._api_key,
                http_options=http_opts,
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

        model_name = kwargs.pop("model", self._default_model)

        # Build GenerateContentConfig
        config_kwargs: Dict[str, Any] = {}
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
        if temperature is not None:
            config_kwargs["temperature"] = float(temperature)
        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = int(max_tokens)
        config_kwargs.update(kwargs)

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        try:
            logger.info("Calling Gemini API with model '%s'", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        except errors.ClientError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("Gemini client error: %s", sanitized)
            code = getattr(exc, "code", None)
            msg_lower = sanitized.lower()
            if code in {401, 403} or "api_key_invalid" in msg_lower or "unauthenticated" in msg_lower or "permission_denied" in msg_lower:
                raise ProviderAuthenticationError(f"Gemini authentication failed: {sanitized}") from exc
            if code in {408, 504} or "timed out" in msg_lower or "deadline_exceeded" in msg_lower:
                raise ProviderTimeoutError(f"Gemini request timed out: {sanitized}") from exc
            raise ProviderRequestError(f"Gemini request error: {sanitized}") from exc
        except errors.APIError as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            logger.error("Gemini API error: %s", sanitized)
            code = getattr(exc, "code", None)
            msg_lower = sanitized.lower()
            if code in {408, 504} or "timed out" in msg_lower or "deadline_exceeded" in msg_lower:
                raise ProviderTimeoutError(f"Gemini request timed out: {sanitized}") from exc
            raise ProviderRequestError(f"Gemini API error: {sanitized}") from exc
        except (TimeoutError, Exception) as exc:
            sanitized = sanitize_sensitive_data(str(exc))
            msg_lower = sanitized.lower()
            if isinstance(exc, TimeoutError) or "timed out" in msg_lower:
                logger.error("Gemini request timed out after %.1fs", self._timeout)
                raise ProviderTimeoutError(f"Gemini request timed out after {self._timeout}s.") from exc
            logger.error("Unexpected Gemini error: %s", sanitized, exc_info=False)
            raise ProviderRequestError(f"Gemini provider failure: {sanitized}") from exc

        # Extract completion content safely
        generated_text = response.text
        if generated_text is None:
            # Check for candidate block or empty generation
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, "finish_reason", "BLOCKED")
                raise ProviderResponseError(f"Gemini returned empty text with finish reason: {finish_reason}")
            raise ProviderResponseError("Gemini response contained no candidates or text content.")

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Extract token usage metadata
        usage_data = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            usage_data = UsageMetadata(
                prompt_tokens=getattr(usage, "prompt_token_count", None),
                completion_tokens=getattr(usage, "candidates_token_count", None),
                total_tokens=getattr(usage, "total_token_count", None),
            )

        finish_reason = None
        if hasattr(response, "candidates") and response.candidates:
            finish_reason = str(getattr(response.candidates[0], "finish_reason", None))

        return ProviderResponse(
            generated_text=generated_text,
            provider="gemini",
            model=model_name,
            usage=usage_data,
            finish_reason=finish_reason,
            latency_ms=latency_ms,
            metadata={
                "is_demo": False,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
