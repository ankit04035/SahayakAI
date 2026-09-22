"""
Document Text Statistics and Language Heuristics.
Computes character, word, sentence, paragraph, and page counts,
reading time estimation, and script-based language identification.
"""

import math
import re
from pydantic import BaseModel, Field


class DocumentStatistics(BaseModel):
    """Structured document statistics and readability metrics."""

    character_count: int = Field(default=0, ge=0, description="Total number of characters")
    word_count: int = Field(default=0, ge=0, description="Total number of words")
    sentence_count: int = Field(default=0, ge=0, description="Total number of sentences")
    paragraph_count: int = Field(default=0, ge=0, description="Total number of paragraphs")
    page_count: int = Field(default=1, ge=1, description="Total number of pages")
    estimated_reading_time_minutes: float = Field(
        default=0.0, ge=0.0, description="Estimated reading time in minutes (200 WPM)"
    )
    primary_language: str = Field(
        default="en", description="Detected primary language code (en, hi, hinglish, or unknown)"
    )


def detect_language_heuristic(text: str) -> str:
    """
    Detect language based on Unicode character distribution.
    Distinguishes English, Hindi (Devanagari script), and Hinglish (mixed).
    """
    if not text or not text.strip():
        return "unknown"

    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))
    total_letters = devanagari_chars + latin_chars

    if total_letters == 0:
        return "unknown"

    dev_ratio = devanagari_chars / total_letters

    if dev_ratio >= 0.35:
        return "hi"
    elif dev_ratio >= 0.05:
        return "hinglish"

    # For mostly Latin text, inspect common Hinglish marker words
    hinglish_markers = {
        "hai", "hain", "kya", "kyu", "kyun", "kaise", "nahi", "nahin", "accha", "theek",
        "padhai", "kitab", "karo", "karna", "raha", "rahi", "hoga", "sakte", "liye",
        "bahut", "bohot", "samajhna", "samajh", "zaroori", "zaroorat", "aur", "ya",
        "yeh", "woh", "kuch", "sab", "toh", "ka", "ke", "ki", "ko", "se", "me", "mein", "par"
    }
    words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    hinglish_matches = words.intersection(hinglish_markers)
    if len(hinglish_matches) >= 2:
        return "hinglish"

    return "en"


def compute_text_statistics(text: str, page_count: int = 1) -> DocumentStatistics:
    """
    Calculate comprehensive statistics for cleaned document text.
    """
    if not text or not text.strip():
        return DocumentStatistics(
            character_count=0,
            word_count=0,
            sentence_count=0,
            paragraph_count=0,
            page_count=max(1, page_count),
            estimated_reading_time_minutes=0.0,
            primary_language="unknown",
        )

    stripped = text.strip()
    char_count = len(stripped)

    # Word extraction supporting alphanumeric and Devanagari Unicode
    words = re.findall(r"[\w\u0900-\u097F]+", stripped)
    word_count = len(words)

    # Sentence boundary detection (standard .!? and Hindi purna viram ।)
    sentences = [s.strip() for s in re.split(r"[.!?\u0964]+", stripped) if s.strip()]
    sentence_count = max(1, len(sentences)) if word_count > 0 else 0

    # Paragraph count split by double line breaks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", stripped) if p.strip()]
    paragraph_count = max(1, len(paragraphs)) if word_count > 0 else 0

    # Reading time calculation (average 200 WPM)
    reading_time = round(word_count / 200.0, 2)

    # Primary language detection
    lang = detect_language_heuristic(stripped)

    return DocumentStatistics(
        character_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        page_count=max(1, page_count),
        estimated_reading_time_minutes=reading_time,
        primary_language=lang,
    )
