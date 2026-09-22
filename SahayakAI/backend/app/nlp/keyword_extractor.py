"""
Deterministic Keyword and Keyphrase Extraction.
Extracts significant unigrams and bigrams using term frequency scoring
with comprehensive multilingual stopword filtering (English, Hindi, Hinglish).
"""

from collections import Counter
import math
import re
from typing import Any, Dict, List, Set

# Comprehensive Multilingual Stopword Collections
ENGLISH_STOPWORDS: Set[str] = {
    "about", "above", "after", "again", "against", "all", "also", "and", "any", "are",
    "aren't", "because", "been", "before", "being", "below", "between", "both", "but",
    "cannot", "can't", "could", "couldn't", "did", "didn't", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "how", "into", "itself", "just", "more",
    "most", "must", "mustn't", "myself", "off", "once", "only", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "should", "shouldn't", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "too", "under", "until", "very", "was", "wasn't",
    "were", "weren't", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "won't", "would", "wouldn't", "you", "your", "yours", "yourself", "yourselves",
}

HINDI_STOPWORDS: Set[str] = {
    "और", "कि", "का", "के", "की", "है", "हैं", "था", "थी", "थे", "से", "को", "पर", "में",
    "यह", "वह", "इस", "उस", "एक", "तो", "भी", "नहीं", "होता", "होती", "होते", "होना",
    "करना", "करते", "किया", "गया", "गई", "गए", "जाता", "जाती", "जाते", "अपने", "अपनी",
    "अपना", "द्वारा", "लिये", "लिए", "साथ", "सब", "कोई", "कुछ", "या", "बहुत", "तथा",
    "एवं", "इत्यादि", "तक", "हो", "रहे", "रही", "रहा", "सकते", "सकता", "सकती",
}

HINGLISH_STOPWORDS: Set[str] = {
    "hai", "hain", "tha", "thi", "the", "ka", "ke", "ki", "ko", "se", "par", "me", "mein",
    "aur", "ya", "yeh", "woh", "is", "us", "kya", "kyu", "kyun", "kaise", "nahi", "nahin",
    "hota", "hoti", "hote", "hona", "karo", "karna", "kare", "karen", "raha", "rahi", "rahe",
    "hoga", "hogi", "hoge", "apna", "apni", "apne", "saath", "liye", "bhi", "toh", "jab",
    "tab", "ab", "ek", "bohot", "bahut", "sirf", "sab", "koi", "kuch",
}

ALL_STOPWORDS: Set[str] = ENGLISH_STOPWORDS | HINDI_STOPWORDS | HINGLISH_STOPWORDS


def extract_keywords(
    text: str,
    top_n: int = 10,
    include_scores: bool = True,
) -> List[Dict[str, Any]]:
    """
    Extract top keywords and keyphrases from cleaned text.
    Uses TF frequency weighting and n-gram scoring.
    """
    if not text or not text.strip():
        return []

    # Tokenize words preserving Devanagari and Latin letters (at least 3 chars)
    raw_tokens = re.findall(r"[\w\u0900-\u097F]{3,}", text.lower())
    if not raw_tokens:
        return []

    # Unigram candidate collection (excluding stopwords and pure digits)
    valid_unigrams: List[str] = []
    for token in raw_tokens:
        if token.isdigit():
            continue
        if token in ALL_STOPWORDS:
            continue
        valid_unigrams.append(token)

    unigram_counts = Counter(valid_unigrams)

    # Bigram candidate collection (consecutive pairs of valid tokens)
    valid_bigrams: List[str] = []
    for i in range(len(raw_tokens) - 1):
        t1, t2 = raw_tokens[i], raw_tokens[i + 1]
        if t1.isdigit() or t2.isdigit():
            continue
        if t1 in ALL_STOPWORDS or t2 in ALL_STOPWORDS:
            continue
        valid_bigrams.append(f"{t1} {t2}")

    bigram_counts = Counter(valid_bigrams)

    # Calculate scoring
    # Bigrams receive a slight boost (1.3x) because specific phrases are informative
    total_tokens = max(1, len(valid_unigrams))
    scores: Dict[str, Dict[str, Any]] = {}

    for word, count in unigram_counts.items():
        # Score normalized by sqrt(total_tokens)
        score = round((count / math.sqrt(total_tokens)), 4)
        scores[word] = {"keyword": word, "score": score, "count": count}

    for phrase, count in bigram_counts.items():
        if count >= 1:
            score = round((count * 1.3 / math.sqrt(total_tokens)), 4)
            scores[phrase] = {"keyword": phrase, "score": score, "count": count}

    # Sort candidates by score descending, then count descending, then keyword alphabetically
    sorted_keywords = sorted(
        scores.values(),
        key=lambda item: (-item["score"], -item["count"], item["keyword"]),
    )

    return sorted_keywords[:top_n]
