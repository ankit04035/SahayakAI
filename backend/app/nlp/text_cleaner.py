"""
Deterministic Text Cleaning and Normalization Pipeline.
Handles Unicode normalization, whitespace standardization, line breaks,
PDF artifact removal, and multilingual text (English, Hindi, Hinglish).
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Perform deterministic cleaning on extracted text.
    - Normalizes Unicode to NFC.
    - Replaces odd whitespace characters (NBSP, thin spaces, zero-width spaces).
    - Fixes PDF end-of-line hyphenation.
    - Normalizes line endings to \\n.
    - Collapses excessive blank lines and trailing spaces.
    - Preserves Devanagari script and punctuation.
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Unicode NFC normalization
    cleaned = unicodedata.normalize("NFC", text)

    # 2. Remove null bytes and dangerous control characters except \\t and \\n
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # 3. Standardize line endings (\\r\\n and \\r -> \\n)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Replace zero-width spaces and formatting characters
    cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", cleaned)

    # 5. Replace non-standard whitespace (NBSP, en-space, em-space, thin space, etc.) with standard space
    cleaned = re.sub(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]", " ", cleaned)

    # 6. Fix PDF end-of-line hyphenation (e.g. "commer-\\ncial" -> "commercial")
    cleaned = re.sub(r"([a-zA-Z\u0900-\u097F])-\n\s*([a-zA-Z\u0900-\u097F])", r"\1\2", cleaned)

    # 7. Strip trailing spaces per line and normalize repeated horizontal whitespace
    lines = []
    for line in cleaned.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)

    cleaned = "\n".join(lines)

    # 8. Collapse 3 or more consecutive newlines into 2 (paragraph break)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 9. Strip leading and trailing whitespace of entire text
    return cleaned.strip()
