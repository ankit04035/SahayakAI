# SahayakAI — Generative AI Provider Abstraction Architecture

**Status:** APPROVED  
**Version:** 1.0.0  
**Last Updated:** 2026-09-22  
**Implementation Phase:** STEP 4 (AI Provider Abstraction Layer)

---

## 1. Executive Summary & Architectural Motivation

SahayakAI relies on generative AI models to power study assistance, contextual RAG explanations, resume skill gap evaluations, and career roadmaps. Binding domain services directly to specific vendor SDKs creates:
- **Vendor Lock-in**: Inability to transition between cloud providers or self-hosted models.
- **Testing Fragility**: Inability to run test suites without paid API credentials or reliable internet.
- **Credential Leakage Risks**: Accidental logging or network exposure of API keys.
- **Brittle Error Handling**: Leaking low-level SDK exceptions into user-facing HTTP responses.

To solve this, SahayakAI establishes a **Provider-Neutral Abstraction Layer** located under `backend/app/providers/`. Higher-level domain services interact exclusively with the `BaseAIProvider` interface.

```
┌─────────────────────────────────────────────────────────────┐
│  Domain Features (RAG, Resume Analyzer, Study Assistant)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ calls provider.generate(...)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 BaseAIProvider (Interface)                  │
│       generate(), generate_from_request(), get_status()     │
└───────────────▲──────────────────────────────▲──────────────┘
                │                              │
         factory.get_provider(AI_PROVIDER)     │
                │                              │
 ┌──────────────┴──────────────┐ ┌─────────────┴──────────────┐ ┌───────────────────────────┐
 │        DemoProvider         │ │  OpenAICompatibleProvider  │ │      GeminiProvider       │
 │  (Deterministic, Local CPU) │ │ (OpenAI, Ollama, vLLM)     │ │   (Google GenAI SDK)      │
 └─────────────────────────────┘ └────────────────────────────┘ └───────────────────────────┘
```

---

## 2. Architecture & File Structure

The provider system enforces single-responsibility separation:

```
backend/app/providers/
├── __init__.py           # Exports public interfaces, models, exceptions, factory
├── base.py               # Abstract BaseAIProvider contract
├── models.py             # ProviderRequest, ProviderResponse, UsageMetadata
├── factory.py            # Centralized get_provider(), check_provider_status()
├── exceptions.py         # Typed, sanitized provider exceptions
├── demo.py               # Deterministic local offline engine
├── openai_provider.py    # OpenAI & OpenAI-compatible provider adapter
└── gemini_provider.py    # Google Gemini GenAI SDK provider adapter
```

---

## 3. Provider Contract: Request & Response Data Models

### 3.1 `BaseAIProvider`
All providers inherit from `BaseAIProvider` and implement:
```python
@abstractmethod
def generate(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any,
) -> ProviderResponse:
    ...
```

### 3.2 Standardized Response Model (`ProviderResponse`)
```json
{
  "generated_text": "Detailed synthesized answer...",
  "provider": "demo",
  "model": "demo-deterministic",
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 128,
    "total_tokens": 170
  },
  "finish_reason": "stop",
  "latency_ms": 1.45,
  "metadata": {
    "is_demo": true,
    "request_type": "document_grounded"
  }
}
```

---

## 4. Provider Implementations

### 4.1 DemoProvider (`AI_PROVIDER=demo`)
- **Credentials Required**: None.
- **Network Required**: None (100% offline local CPU execution).
- **Determinism**: Guaranteed identical responses for identical inputs.
- **Intent Synthesis Archetypes**:
  1. **Executive Summaries (`summary`)**: Extracts core keywords and compiles highlights, bullets, and conclusions.
  2. **Document-Grounded Q&A (`document_grounded`)**: Explicitly segregates `### Retrieved Context Information` (citations) from `### Generated Explanation`. If context is missing or null, it outputs a strict grounded retrieval notice without hallucinating facts.
  3. **Multiple Choice Questions (`mcq`)**: Extracts topics and generates 4-option questions with marked correct answers and explanations.
  4. **Career Roadmaps (`career`)**: Identifies target roles and synthesizes 3-phase milestones, prerequisite competencies, project proposals, and interview topics.
  5. **General Conceptual Explanations (`explanation`)**: Generates structured definitions, principles, and applications.

### 4.2 OpenAI-Compatible Provider (`AI_PROVIDER=openai`)
- **SDK**: Official `openai>=1.50.0`.
- **Base URL Support**: Configurable via `OPENAI_BASE_URL` to support:
  - OpenAI official API (`https://api.openai.com/v1`)
  - Local Ollama (`http://localhost:11434/v1`)
  - Self-hosted vLLM / LMStudio
  - Fast inference providers (Groq, Together AI)
- **Model**: Default `gpt-4o-mini` (configurable via `OPENAI_MODEL`).
- **Validation**: Requires non-empty `OPENAI_API_KEY`.

### 4.3 Google Gemini Provider (`AI_PROVIDER=gemini`)
- **SDK**: Official modern `google.genai` (`google-genai>=2.0.0`).
- **Model**: Default `gemini-1.5-flash` (configurable via `GEMINI_MODEL`).
- **Timeout**: Enforced in milliseconds via `types.HttpOptions(timeout=int(seconds * 1000))`.
- **Validation**: Requires non-empty `GEMINI_API_KEY`.

---

## 5. Configuration Settings

Settings are managed via Pydantic Settings in `backend/app/config.py`:

| Variable | Type | Default | Description |
|---|---|---|---|
| `AI_PROVIDER` | `str` | `"demo"` | Active provider (`demo`, `openai`, `gemini`) |
| `AI_TIMEOUT_SECONDS` | `int` | `30` | Request timeout duration ($1 \le t \le 300$) |
| `AI_MAX_TOKENS` | `int` | `1000` | Output token generation limit ($1 \le n \le 32000$) |
| `AI_TEMPERATURE` | `float` | `0.2` | Sampling randomness ($0.0 \le T \le 2.0$) |
| `OPENAI_API_KEY` | `str \| None` | `None` | OpenAI API key (backend-only) |
| `OPENAI_BASE_URL` | `str \| None` | `None` | Custom inference server base URL |
| `OPENAI_MODEL` | `str` | `"gpt-4o-mini"` | Default OpenAI model |
| `GEMINI_API_KEY` | `str \| None` | `None` | Google Gemini API key (backend-only) |
| `GEMINI_MODEL` | `str` | `"gemini-1.5-flash"` | Default Gemini model |

---

## 6. Error Handling & Secret Sanitization

### 6.1 Exception Hierarchy
```
AppException (backend.app.exceptions)
   └── ProviderError
         ├── ProviderConfigurationError
         │     └── UnsupportedProviderError
         ├── ProviderAuthenticationError
         ├── ProviderTimeoutError
         ├── ProviderRequestError
         └── ProviderResponseError
```

### 6.2 Defensive Credential Scrubbing
All exceptions and loggers process error strings through `sanitize_sensitive_data()`, stripping:
- OpenAI secret keys: `sk-...` $\to$ `sk-***REDACTED***`
- Google Gemini API keys: `AIza...` $\to$ `AIza***REDACTED***`
- Bearer tokens: `Bearer eyJ...` $\to$ `Bearer ***REDACTED***`
- Query/Header credentials: `api_key=...` $\to$ `api_key=***REDACTED***`

Secrets are **never** rendered in exception traces, HTTP responses, or console logs.

---

## 7. Timeout and Retry Policies

1. **Timeout Policy**:
   - Provider calls enforce an explicit timeout (`AI_TIMEOUT_SECONDS`, default 30s).
   - If an external call exceeds the threshold, it is aborted and converted into `ProviderTimeoutError` (HTTP 504 Gateway Timeout).
2. **Retry Policy**:
   - **No Blind Retries**: Timeouts, authentication errors (401/403), and client formatting errors (400) **fail immediately**.
   - **Controlled Retries**: Provider SDK automated retry loops are disabled (`max_retries=0`) to prevent compounding tail latency. Upstream services may selectively retry transient network failures (e.g. 503 Service Unavailable) with exponential backoff.

---

## 8. Health Check Integration

The liveness endpoint `GET /api/health` queries `check_provider_status()`:
- Performs purely internal configuration validation.
- Makes **zero external network requests** or expensive generation calls during health checks.
- In Demo mode, reports:
  ```json
  {
    "status": "ok",
    "database": "ok",
    "ai_provider": "demo",
    "version": "0.1.0"
  }
  ```

---

## 9. Testing Strategy

The test suite in `tests/providers/test_providers.py` verifies 24 isolated test cases across 5 categories:
1. **Demo Provider**: Determinism, summary generation, MCQ creation, career guidance, grounded answers with context, and safe empty context notification. Proves zero network access via monkeypatched socket connections.
2. **Factory Selection**: Instantiation of `DemoProvider`, `OpenAICompatibleProvider`, and `GeminiProvider`, and rejection of unsupported provider names.
3. **Configuration Validation**: Startup in Demo mode without keys, validation of required keys when external providers are selected, and bounds checks on timeout, temperature, and tokens.
4. **Error Translation & Sanitization**: Simulated timeout to `ProviderTimeoutError`, simulated 401 to `ProviderAuthenticationError`, malformed choices to `ProviderResponseError`, and credential masking.
5. **Mocked Execution**: Validates structured `ProviderResponse`, token accounting, and latency tracking without contacting live APIs.
