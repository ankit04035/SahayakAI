"""
Comprehensive Unit and Integration Tests for AI Provider Abstraction Layer.
Validates DemoProvider determinism, Provider Factory selection, Error handling, Secret sanitization,
and Mocked OpenAI and Gemini integrations.
"""

import socket
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

from backend.app.config import Settings
from backend.app.providers import (
    BaseAIProvider,
    DemoProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRequest,
    ProviderRequestError,
    ProviderResponse,
    ProviderResponseError,
    ProviderTimeoutError,
    UnsupportedProviderError,
    check_provider_status,
    get_provider,
    sanitize_sensitive_data,
)


# ==============================================================================
# A. Demo Provider Tests
# ==============================================================================

def test_demo_provider_initializes_without_keys():
    """Test 1: DemoProvider initializes cleanly with zero credentials."""
    provider = DemoProvider()
    assert isinstance(provider, BaseAIProvider)
    assert provider.provider_name == "demo"
    assert provider.default_model == "demo-deterministic"
    status = provider.get_status()
    assert status["status"] == "ready"
    assert status["provider"] == "demo"


def test_demo_provider_deterministic_output():
    """Test 2: Same prompt produces identical, deterministic output across multiple runs."""
    provider = DemoProvider()
    prompt = "Explain how relational database indexes optimize query execution."

    res1 = provider.generate(prompt)
    res2 = provider.generate(prompt)

    assert isinstance(res1, ProviderResponse)
    assert isinstance(res2, ProviderResponse)
    assert res1.generated_text == res2.generated_text
    assert res1.provider == "demo"
    assert res1.metadata["is_demo"] is True
    assert res1.finish_reason == "stop"
    assert res1.usage is not None
    assert res1.usage.prompt_tokens == res2.usage.prompt_tokens
    assert res1.usage.completion_tokens == res2.usage.completion_tokens


def test_demo_provider_summary_style_prompt():
    """Test 3: Summary-style prompt returns structured summary with highlights and conclusions."""
    provider = DemoProvider()
    prompt = "Summarize the key architectural benefits of adopting event-driven microservices for scalable cloud systems."

    response = provider.generate(prompt)
    text = response.generated_text

    assert "Executive Summary" in text
    assert "Key Highlights" in text
    assert "Conclusion" in text
    assert response.metadata["request_type"] == "summary"


def test_demo_provider_explanation_style_prompt():
    """Test 4: General explanation prompt returns structured conceptual breakdown."""
    provider = DemoProvider()
    prompt = "Explain how asynchronous event loops function in FastAPI and Starlette."

    response = provider.generate(prompt, system_prompt="Expert AI Tutor")
    text = response.generated_text

    assert "asynchronous event loop" in text.lower()
    assert "I/O-bound" in text
    assert "Expert AI Tutor" not in text
    assert response.metadata["request_type"] == "explanation"


def test_demo_provider_answers_current_chat_question_without_prompt_metadata():
    provider = DemoProvider()
    response = provider.generate(
        prompt=(
            "Conversation History:\nNone (new conversation)\n\n"
            "Question:\nExplain how a database index helps a query."
        ),
        system_prompt="You are an expert educational mentor and academic tutor. Follow these guidelines.",
    )

    assert "Conversation History" not in response.generated_text
    assert "expert educational mentor" not in response.generated_text
    assert "database index" in response.generated_text.lower()
    assert "B-tree" in response.generated_text


def test_demo_provider_document_context_prompt():
    """Test 5: Document-grounded prompt explicitly separates retrieved context from generated explanation."""
    provider = DemoProvider()
    prompt = (
        "Context: SahayakAI implements a local vector similarity engine using NumPy dot products on L2-normalized embeddings. "
        "It stores vector embeddings as JSON float lists in SQLite to ensure zero external dependencies.\n\n"
        "Question: How does SahayakAI calculate vector similarity?"
    )

    response = provider.generate(prompt)
    text = response.generated_text

    assert "### Retrieved Context Information" in text
    assert "### Generated Explanation" in text
    assert "NumPy" in text or "vector similarity" in text
    assert response.metadata["request_type"] == "document_grounded"


def test_demo_provider_missing_context_handled_safely():
    """Test 6: Grounded query with missing/null context produces a safe notification without hallucinating facts."""
    provider = DemoProvider()
    prompt = "Context: None\nQuestion: What are the eligibility rules for the scholarship?"

    response = provider.generate(prompt)
    text = response.generated_text

    assert "Grounded Retrieval Notice" in text
    assert "No document context was provided" in text
    assert response.metadata["request_type"] == "document_grounded"


def test_demo_provider_mcq_generation_prompt():
    """Test 7: MCQ generation prompt produces formatted questions with options and explanations."""
    provider = DemoProvider()
    prompt = "Generate 3 multiple choice questions (MCQ) with options about Docker containerization."

    response = provider.generate(prompt)
    text = response.generated_text

    assert "Multiple Choice Questions" in text
    assert "Question 1:" in text
    assert "A)" in text
    assert "B)" in text
    assert "Correct Answer:" in text
    assert "Explanation:" in text
    assert response.metadata["request_type"] == "mcq"


def test_demo_provider_career_recommendation_prompt():
    """Test 8: Career guidance prompt produces structured roadmap with milestones and interview prep."""
    provider = DemoProvider()
    prompt = "Provide a career roadmap to become a Backend Machine Learning Engineer."

    response = provider.generate(prompt)
    text = response.generated_text

    assert "Career Roadmap" in text
    assert "Skill Assessment" in text
    assert "Phased Learning Progression" in text
    assert "Recommended Portfolio Project" in text
    assert "Interview Topics" in text
    assert response.metadata["request_type"] == "career"


def test_demo_provider_never_makes_network_requests(monkeypatch):
    """Test 9: Verify DemoProvider executes without opening any network sockets."""
    def guarded_connect(*args, **kwargs):
        raise AssertionError("Network socket connection attempted during DemoProvider execution!")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)

    provider = DemoProvider()
    res = provider.generate("Summarize computer science principles.")
    assert len(res.generated_text) > 0


# ==============================================================================
# B. Factory Tests
# ==============================================================================

def test_factory_selects_demo_provider():
    """Test 10: Factory returns DemoProvider when provider='demo'."""
    settings = Settings(AI_PROVIDER="demo")
    provider = get_provider("demo", settings=settings)
    assert isinstance(provider, DemoProvider)
    assert provider.provider_name == "demo"


def test_factory_selects_openai_provider():
    """Test 11: Factory returns OpenAICompatibleProvider when provider='openai' and key is present."""
    settings = Settings(
        AI_PROVIDER="openai",
        OPENAI_API_KEY="sk-test-valid-key-for-testing",
        OPENAI_MODEL="gpt-4o-mini",
    )
    provider = get_provider("openai", settings=settings)
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.provider_name == "openai"
    assert provider.default_model == "gpt-4o-mini"


def test_factory_selects_gemini_provider():
    """Test 12: Factory returns GeminiProvider when provider='gemini' and key is present."""
    settings = Settings(
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="AIzaTestValidGeminiKeyForTesting",
        GEMINI_MODEL="gemini-1.5-flash",
    )
    provider = get_provider("gemini", settings=settings)
    assert isinstance(provider, GeminiProvider)
    assert provider.provider_name == "gemini"
    assert provider.default_model == "gemini-1.5-flash"


def test_factory_rejects_unsupported_provider():
    """Test 13: Unsupported provider name raises controlled UnsupportedProviderError."""
    settings = Settings(AI_PROVIDER="unsupported_provider_xyz")
    with pytest.raises(UnsupportedProviderError) as exc_info:
        get_provider("unsupported_provider_xyz", settings=settings)

    assert "Unsupported AI provider" in str(exc_info.value)
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "UNSUPPORTED_PROVIDER_ERROR"


# ==============================================================================
# C. Configuration Validation Tests
# ==============================================================================

def test_missing_api_keys_allow_demo_startup():
    """Test 14: Application starts up cleanly in demo mode without any API keys."""
    settings = Settings(AI_PROVIDER="demo", OPENAI_API_KEY=None, GEMINI_API_KEY=None)
    assert settings.AI_PROVIDER == "demo"
    provider = get_provider(settings=settings)
    assert isinstance(provider, DemoProvider)


def test_factory_validates_openai_missing_key():
    """Test 15: Factory raises ProviderConfigurationError when OpenAI is selected without an API key."""
    settings = Settings(AI_PROVIDER="openai", OPENAI_API_KEY=None)
    with pytest.raises(ProviderConfigurationError) as exc_info:
        get_provider("openai", settings=settings)

    assert "OPENAI_API_KEY is required" in str(exc_info.value)
    assert exc_info.value.status_code == 500


def test_factory_validates_gemini_missing_key():
    """Test 16: Factory raises ProviderConfigurationError when Gemini is selected without an API key."""
    settings = Settings(AI_PROVIDER="gemini", GEMINI_API_KEY="")
    with pytest.raises(ProviderConfigurationError) as exc_info:
        get_provider("gemini", settings=settings)

    assert "GEMINI_API_KEY is required" in str(exc_info.value)
    assert exc_info.value.status_code == 500


def test_timeout_and_generation_settings_validation():
    """Test 17: Settings validates bounds on timeout, temperature, and tokens."""
    # Timeout <= 0 is rejected
    with pytest.raises(ValidationError):
        Settings(AI_TIMEOUT_SECONDS=0)

    # Max tokens <= 0 is rejected
    with pytest.raises(ValidationError):
        Settings(AI_MAX_TOKENS=-10)

    # Temperature < 0 is rejected
    with pytest.raises(ValidationError):
        Settings(AI_TEMPERATURE=-0.5)


# ==============================================================================
# D. Error Handling & Secret Sanitization Tests
# ==============================================================================

def test_simulated_openai_timeout_becomes_provider_timeout_error():
    """Test 18: Simulated OpenAI timeout is translated into ProviderTimeoutError."""
    provider = OpenAICompatibleProvider(api_key="sk-dummy-key", timeout=1.0)

    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Request timed out")
    provider._client = mock_client

    # When generic timeout occurs:
    with pytest.raises(ProviderRequestError):
        provider.generate("Hello world")

    # With APITimeoutError:
    from openai import APITimeoutError
    mock_client.chat.completions.create.side_effect = APITimeoutError(request=mock_request)
    with pytest.raises(ProviderTimeoutError):
        provider.generate("Hello world")


def test_simulated_openai_auth_failure_becomes_provider_auth_error():
    """Test 19: Simulated OpenAI 401/AuthenticationError translates into ProviderAuthenticationError."""
    provider = OpenAICompatibleProvider(api_key="sk-dummy-key")

    mock_client = MagicMock()
    import httpx
    fake_response = httpx.Response(
        status_code=401,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )
    from openai import AuthenticationError
    mock_client.chat.completions.create.side_effect = AuthenticationError(
        message="Incorrect API key provided: sk-secret-1234567890abcdef",
        response=fake_response,
        body={"error": {"message": "Incorrect API key"}},
    )
    provider._client = mock_client

    with pytest.raises(ProviderAuthenticationError) as exc_info:
        provider.generate("Test prompt")

    err_str = str(exc_info.value)
    assert "sk-secret-1234567890abcdef" not in err_str
    assert "sk-***REDACTED***" in err_str


def test_simulated_openai_malformed_response_becomes_provider_response_error():
    """Test 20: Malformed empty response from OpenAI raises ProviderResponseError."""
    provider = OpenAICompatibleProvider(api_key="sk-dummy-key")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = []  # Empty choices
    mock_client.chat.completions.create.return_value = mock_response
    provider._client = mock_client

    with pytest.raises(ProviderResponseError):
        provider.generate("Test prompt")


def test_secrets_sanitization_in_exceptions():
    """Test 21: Verify sanitization utility strips OpenAI and Gemini keys and Bearer tokens."""
    raw_message = (
        "Failed request with key sk-proj-1234567890abcdef123456 and gemini AIzaSyD12345678901234567890123456 "
        "using header Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    )
    sanitized = sanitize_sensitive_data(raw_message)

    assert "sk-proj-1234567890abcdef123456" not in sanitized
    assert "AIzaSyD12345678901234567890123456" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "sk-***REDACTED***" in sanitized
    assert "AIza***REDACTED***" in sanitized
    assert "Bearer ***REDACTED***" in sanitized


# ==============================================================================
# E. Mocked Provider Execution Tests
# ==============================================================================

def test_mocked_openai_successful_generation():
    """Test 22: Mocked OpenAI successful generation creates valid ProviderResponse."""
    provider = OpenAICompatibleProvider(api_key="sk-test-key", default_model="gpt-4o-mini")

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OpenAI generated text successfully."
    mock_choice.finish_reason = "stop"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 25
    mock_usage.total_tokens = 40

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = mock_usage
    mock_resp.model = "gpt-4o-mini"

    mock_client.chat.completions.create.return_value = mock_resp
    provider._client = mock_client

    result = provider.generate("Say hello", system_prompt="Be concise")

    assert result.generated_text == "OpenAI generated text successfully."
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert result.finish_reason == "stop"
    assert result.usage.prompt_tokens == 15
    assert result.usage.completion_tokens == 25
    assert result.usage.total_tokens == 40
    assert result.latency_ms is not None
    assert result.metadata["is_demo"] is False


def test_mocked_gemini_successful_generation():
    """Test 23: Mocked Gemini successful generation creates valid ProviderResponse."""
    provider = GeminiProvider(api_key="AIzaTestKey", default_model="gemini-1.5-flash")

    mock_client = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 20
    mock_usage.total_token_count = 30

    mock_resp = MagicMock()
    mock_resp.text = "Gemini synthesized response."
    mock_resp.candidates = [mock_candidate]
    mock_resp.usage_metadata = mock_usage

    mock_client.models.generate_content.return_value = mock_resp
    provider._client = mock_client

    result = provider.generate("Explain AI", temperature=0.5)

    assert result.generated_text == "Gemini synthesized response."
    assert result.provider == "gemini"
    assert result.model == "gemini-1.5-flash"
    assert result.usage.total_tokens == 30
    assert result.finish_reason == "STOP"
    assert result.latency_ms is not None
    assert result.metadata["is_demo"] is False


def test_provider_status_check():
    """Test 24: Internal check_provider_status reports safe readiness metadata."""
    demo_status = check_provider_status(Settings(AI_PROVIDER="demo"))
    assert demo_status["status"] == "ok"
    assert demo_status["provider"] == "demo"

    openai_unconfigured = check_provider_status(Settings(AI_PROVIDER="openai", OPENAI_API_KEY=None))
    assert openai_unconfigured["status"] == "unconfigured"
    assert "Missing OPENAI_API_KEY" in openai_unconfigured["details"]

    gemini_configured = check_provider_status(Settings(AI_PROVIDER="gemini", GEMINI_API_KEY="AIzaTest"))
    assert gemini_configured["status"] == "ok"
    assert gemini_configured["model"] == "gemini-1.5-flash"
