"""
SahayakAI NLP Package.
Provides text cleaning, statistics calculation, deterministic keyword extraction,
query preprocessing, and boundary-aware document chunking.
"""

from backend.app.nlp.text_cleaner import clean_text
from backend.app.nlp.text_statistics import (
    DocumentStatistics,
    compute_text_statistics,
    detect_language_heuristic,
)
from backend.app.nlp.keyword_extractor import extract_keywords
from backend.app.nlp.query_preprocessor import (
    QueryPreprocessingResult,
    preprocess_query,
)
from backend.app.nlp.chunker import (
    ChunkItem,
    chunk_pages,
    chunk_text,
)

__all__ = [
    "clean_text",
    "compute_text_statistics",
    "detect_language_heuristic",
    "DocumentStatistics",
    "extract_keywords",
    "preprocess_query",
    "QueryPreprocessingResult",
    "ChunkItem",
    "chunk_text",
    "chunk_pages",
]
