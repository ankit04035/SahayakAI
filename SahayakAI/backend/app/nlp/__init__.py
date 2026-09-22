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
from backend.app.nlp.skill_extractor import (
    SKILL_ALIAS_MAP,
    extract_skills,
    normalize_skill,
)
from backend.app.nlp.resume_parser import (
    extract_education,
    extract_experience,
    parse_resume_sections,
    parse_structured_resume,
)
from backend.app.nlp.role_taxonomy import (
    ROLE_TAXONOMY,
    get_role_taxonomy,
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
    "SKILL_ALIAS_MAP",
    "extract_skills",
    "normalize_skill",
    "extract_education",
    "extract_experience",
    "parse_resume_sections",
    "parse_structured_resume",
    "ROLE_TAXONOMY",
    "get_role_taxonomy",
]
