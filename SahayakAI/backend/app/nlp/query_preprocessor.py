"""
Query Preprocessor for Document Search and Q&A.
Preserves original query, produces normalized forms, extracts clean tokens,
filters conversational stopwords, and detects input language.
"""

import re
import unicodedata
from typing import List
from pydantic import BaseModel, Field

from backend.app.nlp.keyword_extractor import ALL_STOPWORDS
from backend.app.nlp.text_statistics import detect_language_heuristic


class QueryPreprocessingResult(BaseModel):
    """Structured result of query preprocessing."""

    original_query: str = Field(description="Original user-supplied query string")
    normalized_query: str = Field(description="Normalized, lowercased, punctuation-cleaned query")
    tokens: List[str] = Field(default_factory=list, description="All extracted query tokens")
    filtered_tokens: List[str] = Field(
        default_factory=list, description="Tokens after removing multilingual stopwords"
    )
    language: str = Field(description="Detected language (en, hi, hinglish, or unknown)")
    is_empty: bool = Field(description="Whether the query contained meaningful terms")


def preprocess_query(query: str) -> QueryPreprocessingResult:
    """
    Preprocess user search or Q&A query into clean tokens and normalized text.
    Handles English, Hindi (Devanagari), and Hinglish transparently.
    """
    if not query or not isinstance(query, str):
        return QueryPreprocessingResult(
            original_query="" if query is None else str(query),
            normalized_query="",
            tokens=[],
            filtered_tokens=[],
            language="unknown",
            is_empty=True,
        )

    original = query.strip()
    if not original:
        return QueryPreprocessingResult(
            original_query="",
            normalized_query="",
            tokens=[],
            filtered_tokens=[],
            language="unknown",
            is_empty=True,
        )

    # 1. Unicode normalization
    normalized = unicodedata.normalize("NFC", original)

    # 2. Lowercase (affects Latin letters; Devanagari is unaffected)
    normalized = normalized.lower()

    # 3. Detect language before stripping punctuation
    lang = detect_language_heuristic(normalized)

    # 4. Extract word tokens (preserving Devanagari characters and alphanumeric words)
    tokens = re.findall(r"[\w\u0900-\u097F]+", normalized)

    # 5. Remove punctuation, preserving single spaces between tokens
    cleaned_query = " ".join(tokens)

    # 6. Filter out stopwords and short meaningless tokens (< 2 chars unless digit)
    filtered = [
        t for t in tokens
        if t not in ALL_STOPWORDS and (len(t) >= 2 or t.isdigit())
    ]

    return QueryPreprocessingResult(
        original_query=original,
        normalized_query=cleaned_query,
        tokens=tokens,
        filtered_tokens=filtered,
        language=lang,
        is_empty=len(tokens) == 0,
    )
