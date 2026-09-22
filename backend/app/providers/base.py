"""
Abstract Base AI Provider Interface.
Defines the standardized contract implemented by all AI model providers in SahayakAI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from backend.app.providers.models import ProviderRequest, ProviderResponse


class BaseAIProvider(ABC):
    """Abstract interface defining required methods for all AI providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical identifier for this provider (e.g. 'demo', 'openai', 'gemini')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the active model name used by this provider."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Generate completion text from the underlying AI model.

        Args:
            prompt: Main user or contextual instruction.
            system_prompt: Optional system persona or guidance.
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Maximum tokens in completion.
            **kwargs: Provider-specific parameters (e.g., stop sequences).

        Returns:
            ProviderResponse containing generated text, model metadata, and token usage.
        """
        pass

    def generate_from_request(self, request: ProviderRequest) -> ProviderResponse:
        """Generate response directly from a structured ProviderRequest."""
        return self.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **(request.metadata or {}),
        )

    def get_status(self) -> Dict[str, Any]:
        """Return sanitized operational status metadata for health checks."""
        return {
            "provider": self.provider_name,
            "model": self.default_model,
            "status": "ready",
        }
