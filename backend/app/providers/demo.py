"""
Deterministic Demo AI Provider Engine.
Provides offline, deterministic generative AI behavior without external API keys or network access.
Implements specialized template synthesis for summaries, grounded Q&A, MCQs, career guidance, and explanations.
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from backend.app.providers.base import BaseAIProvider
from backend.app.providers.models import ProviderResponse, UsageMetadata


class DemoProvider(BaseAIProvider):
    """
    Deterministic AI provider operating fully locally with zero credentials.
    Analyzes prompt semantics and produces structured, reproducible outputs.
    """

    def __init__(self, default_model: str = "demo-deterministic"):
        self._default_model = default_model

    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def default_model(self) -> str:
        return self._default_model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        start_time = time.perf_counter()

        cleaned_prompt = prompt.strip() if prompt else ""
        if not cleaned_prompt:
            text = "No prompt was provided. Please provide an input query or context."
            req_type = "empty"
        else:
            text, req_type = self._synthesize_response(cleaned_prompt, system_prompt)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        prompt_token_est = max(1, len(cleaned_prompt.split()))
        completion_token_est = max(1, len(text.split()))

        return ProviderResponse(
            generated_text=text,
            provider="demo",
            model=self._default_model,
            usage=UsageMetadata(
                prompt_tokens=prompt_token_est,
                completion_tokens=completion_token_est,
                total_tokens=prompt_token_est + completion_token_est,
            ),
            finish_reason="stop",
            latency_ms=latency_ms,
            metadata={
                "is_demo": True,
                "request_type": req_type,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

    def _synthesize_response(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
        """Dispatch prompt to deterministic generator based on intent analysis."""
        # 1. Document-Grounded Query Check
        if self._has_document_context_markers(prompt):
            return self._handle_document_grounded_query(prompt), "document_grounded"

        prompt = self._extract_current_question(prompt)
        lower = prompt.lower()

        # 2. Summary Request Check
        if any(w in lower for w in ["summarize", "summary", "tl;dr", "brief overview", "key takeaways", "synopsis"]):
            return self._handle_summary_request(prompt), "summary"

        # 3. MCQ Generation Check
        if any(w in lower for w in ["mcq", "multiple choice", "quiz", "questions with options"]):
            return self._handle_mcq_request(prompt), "mcq"

        # 4. Career / Learning Recommendation Check
        if any(w in lower for w in ["career", "roadmap", "study plan", "interview prep", "skills to learn", "become a"]):
            return self._handle_career_request(prompt), "career"

        # 5. General Explanation Fallback
        return self._handle_general_explanation(prompt, system_prompt), "explanation"

    def _extract_current_question(self, prompt: str) -> str:
        """Keep the current user question separate from bounded chat history."""
        if not prompt.lstrip().lower().startswith("conversation history:"):
            return prompt.strip()

        match = re.search(r"\nQuestion:\s*(.*?)\s*$", prompt, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else prompt.strip()

    def _has_document_context_markers(self, prompt: str) -> bool:
        """Detect whether prompt includes document context delimiters."""
        markers = [
            "context:", "document:", "reference:", "source text:",
            "[context", "based on the provided document", "based on the context",
            "given the following context",
        ]
        lower = prompt.lower()
        return any(m in lower for m in markers)

    def _extract_context_and_question(self, prompt: str) -> Tuple[str, str]:
        """Extract separated context block and question from prompt text."""
        # Try Regex pattern: Context: ... Question: ...
        match = re.search(r"(?:Context|Document|Reference):\s*(.*?)(?:Question|Query|Prompt):\s*(.*)", prompt, re.DOTALL | re.IGNORECASE)
        if match:
            ctx = match.group(1).strip()
            q = match.group(2).strip()
            return ctx, q

        # Try bracket pattern: [Context: ...] ...
        match = re.search(r"\[(?:Context|Document)\]:\s*(.*?)(?:\[Question\]|\n\n)(.*)", prompt, re.DOTALL | re.IGNORECASE)
        if match:
            ctx = match.group(1).strip()
            q = match.group(2).strip()
            return ctx, q

        # Fallback: Split on lines
        lines = prompt.splitlines()
        context_lines = []
        question_lines = []
        in_context = False

        for line in lines:
            ll = line.strip().lower()
            if any(ll.startswith(p) for p in ["context:", "document:", "reference:"]):
                in_context = True
                context_lines.append(line.split(":", 1)[1].strip())
            elif in_context and any(ll.startswith(p) for p in ["question:", "query:"]):
                in_context = False
                question_lines.append(line.split(":", 1)[1].strip())
            elif in_context:
                context_lines.append(line.strip())
            else:
                question_lines.append(line.strip())

        ctx = "\n".join(l for l in context_lines if l).strip()
        q = "\n".join(l for l in question_lines if l).strip()
        return ctx, (q or prompt)

    def _handle_document_grounded_query(self, prompt: str) -> str:
        """Handle document-grounded question with clear separation of context and explanation."""
        context, question = self._extract_context_and_question(prompt)

        # Check if context is absent or explicitly empty
        is_empty_context = (
            not context
            or context.lower() in {"none", "null", "n/a", "no context provided", "empty"}
            or len(context.strip()) < 5
        )

        if is_empty_context:
            return (
                "### Grounded Retrieval Notice\n"
                "No document context was provided to answer this question. "
                "SahayakAI cannot synthesize a document-grounded answer without source material. "
                "Please upload or provide relevant reference text to receive a factual, grounded response."
            )

        # Extract sentences from context that align with words in the question
        q_words = set(re.findall(r"\w+", question.lower())) - {"what", "how", "why", "when", "where", "is", "are", "the", "a", "an", "of", "to", "in"}
        sentences = [s.strip() for s in re.split(r"[.\n]+", context) if s.strip()]

        matched_sentences = []
        for s in sentences:
            s_words = set(re.findall(r"\w+", s.lower()))
            if q_words & s_words:
                matched_sentences.append(s)

        if not matched_sentences:
            matched_sentences = sentences[:3]

        retrieved_block = "\n".join(f"> \"{s}\"" for s in matched_sentences[:4])

        return (
            "### Retrieved Context Information\n"
            f"{retrieved_block}\n\n"
            "### Generated Explanation\n"
            f"Based on the retrieved context above, here is the grounded answer to your query:\n"
            f"- **Direct Answer:** {matched_sentences[0] if matched_sentences else 'The document addresses the referenced subject.'}\n"
            f"- **Synthesis:** The source text explicitly outlines the relevant parameters. "
            f"Key factual points extracted from the document indicate that the query is directly addressed by the provided citations.\n"
            "- **Citation Grounding:** This response is strictly derived from the provided document without external extrapolation."
        )

    def _handle_summary_request(self, prompt: str) -> str:
        """Generate structured deterministic summary from prompt content."""
        sentences = [s.strip() for s in re.split(r"[.\n]+", prompt) if len(s.strip()) > 10]
        words = re.findall(r"\b[A-Za-z]{4,}\b", prompt)

        # Count frequencies for key concept extraction
        freq: Dict[str, int] = {}
        for w in words:
            wl = w.lower()
            if wl not in {"summarize", "summary", "please", "provide", "about", "which", "there", "their", "these", "those"}:
                freq[wl] = freq.get(wl, 0) + 1

        top_concepts = [w.capitalize() for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]
        concept_str = ", ".join(top_concepts) if top_concepts else "Core Concepts"

        key_bullets = sentences[:4] if len(sentences) >= 4 else sentences
        bullet_text = "\n".join(f"- **Point {i+1}:** {s}." for i, s in enumerate(key_bullets))

        return (
            "### Executive Summary\n"
            f"This summary condenses the provided input concerning **{concept_str}**.\n\n"
            "### Key Highlights\n"
            f"{bullet_text}\n\n"
            "### Conclusion\n"
            "The primary focus centers on systematically addressing the foundational principles outlined above, "
            "providing clear clarity and actionable reference points."
        )

    def _handle_mcq_request(self, prompt: str) -> str:
        """Generate structured multiple-choice quiz questions based on prompt keywords."""
        words = [w.capitalize() for w in re.findall(r"\b[A-Za-z]{4,}\b", prompt) if w.lower() not in {"generate", "questions", "options", "multiple", "choice", "quiz", "please", "with"}]
        topic = words[0] if words else "Engineering Principles"
        secondary = words[1] if len(words) > 1 else "Core Architecture"

        return (
            f"### Multiple Choice Questions: {topic}\n\n"
            f"**Question 1:** What is the primary characteristic or purpose of {topic} in modern systems?\n"
            f"A) Arbitrary resource allocation without constraints\n"
            f"B) Structured implementation adhering to {secondary} standards\n"
            f"C) Complete deprecation of static validation\n"
            f"D) Unmonitored execution\n"
            f"**Correct Answer:** B\n"
            f"**Explanation:** Standard system design dictates that {topic} must adhere strictly to structured standards for resilience and correctness.\n\n"
            f"**Question 2:** Which metric is most critical when evaluating {topic} workflows?\n"
            f"A) High latency and unbounded retries\n"
            f"B) Deterministic output reproducibility and minimal overhead\n"
            f"C) Total absence of logging\n"
            f"D) Unbounded memory growth\n"
            f"**Correct Answer:** B\n"
            f"**Explanation:** Reproducibility and predictable latency are essential quality benchmarks.\n\n"
            f"**Question 3:** What is the recommended strategy when deploying {topic} solutions?\n"
            f"A) Incremental verification with automated integration tests\n"
            f"B) Immediate production cutover without rollback paths\n"
            f"C) Hardcoding credentials directly into source control\n"
            f"D) Disabling schema enforcement\n"
            f"**Correct Answer:** A\n"
            f"**Explanation:** Production deployments mandate automated test suites, phased rollouts, and defensive rollback capabilities."
        )

    def _handle_career_request(self, prompt: str) -> str:
        """Generate deterministic career guidance and learning path."""
        # Find potential target role
        target_role = "Software / AI Engineer"
        match = re.search(r"(?:become a|target role|career path for|roadmap for|role:)\s*([A-Za-z\s]+)", prompt, re.IGNORECASE)
        if match:
            extracted = match.group(1).splitlines()[0].strip()
            if len(extracted) > 3:
                target_role = extracted.title()

        return (
            f"### Career Roadmap: {target_role}\n\n"
            "#### 1. Skill Assessment & Core Prerequisites\n"
            "- **Foundational:** Data Structures, Algorithms, Modular Software Engineering, Version Control (Git).\n"
            "- **Core Domain:** Backend Architecture, RESTful API Design, Relational & Structured Data Modeling.\n"
            "- **Specialization:** Production LLM Integrations, RAG Pattern Implementation, Evaluation Benchmarks.\n\n"
            "#### 2. Phased Learning Progression\n"
            "- **Phase 1 (Weeks 1-4):** Language mastery, static type analysis, and robust error handling frameworks.\n"
            "- **Phase 2 (Weeks 5-8):** Asynchronous API development, database relationships, and transaction management.\n"
            "- **Phase 3 (Weeks 9-12):** End-to-end vector embeddings, semantic retrieval, and prompt engineering.\n\n"
            "#### 3. Recommended Portfolio Project\n"
            f"Build a full-stack, end-to-end system showcasing **{target_role}** capabilities: containerized microservices, "
            "comprehensive test coverage (>90%), and CI/CD automated validation.\n\n"
            "#### 4. High-Yield Interview Topics\n"
            "- System scalability and concurrency bottlenecks.\n"
            "- Handling transient failures and exponential backoff strategies.\n"
            "- Schema migration safety and backward compatibility."
        )

    def _handle_general_explanation(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Answer common offline demo questions and avoid inventing other answers."""
        lower = prompt.lower()
        if "database" in lower and "index" in lower:
            return (
                "### How a database index helps a query\n\n"
                "A database index is an auxiliary data structure that helps the database find rows without scanning the whole table. "
                "For example, an index on `email` can find a matching user without checking every user row.\n\n"
                "### How it works\n"
                "- A **B-tree index** keeps values ordered, so equality and range lookups can narrow the search quickly.\n"
                "- The query planner chooses an index when its estimated cost is lower than a table scan.\n"
                "- Indexes speed up many reads, but use disk space and add work to inserts, updates, and deletes.\n\n"
                "### When to add one\n"
                "Index columns often used in filters, joins, or ordering, then use `EXPLAIN` to confirm the query planner uses it."
            )

        if "binary search tree" in lower:
            return (
                "### Binary search trees\n\n"
                "A binary search tree stores values so each node's left subtree contains smaller values and its right subtree contains larger values.\n\n"
                "- Search, insertion, and deletion take $O(h)$ time, where $h$ is the tree height.\n"
                "- A balanced tree has height $O(\\log n)$; a skewed tree can degrade to $O(n)$.\n"
                "- In-order traversal visits values in sorted order.\n\n"
                "Self-balancing variants such as AVL and red-black trees keep the height logarithmic."
            )

        if "event loop" in lower or "asynchronous" in lower:
            return (
                "### How an asynchronous event loop works\n\n"
                "An event loop runs ready tasks and pauses tasks while they wait for I/O, allowing other work to proceed on the same thread.\n\n"
                "1. A coroutine runs until it reaches an `await`.\n"
                "2. The loop registers the pending I/O and schedules another ready task.\n"
                "3. When the I/O completes, the paused coroutine becomes ready to resume.\n\n"
                "This improves concurrency for I/O-bound work; CPU-heavy work needs a process, thread, or other offloading strategy."
            )

        words = [w.capitalize() for w in re.findall(r"\b[A-Za-z]{4,}\b", prompt) if w.lower() not in {"what", "explain", "describe", "tell", "about", "how", "does", "work", "please"}]
        subject = " ".join(words[:3]) if words else "the Requested Subject"

        return (
            f"### About {subject}\n\n"
            "This workspace is using the offline demo provider, so it cannot reliably generate a topic-specific answer for this question. "
            "Configure an OpenAI-compatible or Gemini provider in the backend to enable generated explanations.\n\n"
            "Document-grounded chat remains available for questions answered by your uploaded study materials."
        )
