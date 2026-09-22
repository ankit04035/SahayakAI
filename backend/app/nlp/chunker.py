"""
Deterministic Document Chunker.
Splits text into sliding-window chunks with configurable size and overlap,
preferring sentence and paragraph boundaries over hard character splits,
and preserving page numbers for PDF attribution.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.config import get_settings


class ChunkItem(BaseModel):
    """Represents an individual extracted document chunk."""

    chunk_index: int = Field(ge=0, description="Sequential 0-based chunk index")
    content: str = Field(min_length=1, description="Text content of the chunk")
    character_count: int = Field(gt=0, description="Character count of the content")
    word_count: int = Field(ge=0, description="Word count of the chunk")
    page_number: Optional[int] = Field(default=None, description="1-based page number")
    chunk_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata such as start/end character offsets"
    )


def find_split_point(text: str, start: int, max_end: int) -> int:
    """
    Find optimal boundary-aware split point within search window [start, max_end].
    Prefers paragraph break (\n\n), then sentence boundary (. ! ? ।), then word boundary.
    Falls back to max_end if no boundary exists.
    """
    if max_end >= len(text):
        return len(text)

    window_length = max_end - start
    search_start = max(start, max_end - max(20, int(window_length * 0.25)))
    search_text = text[search_start:max_end]

    # 1. Paragraph boundary (\n\n)
    para_matches = [m.end() for m in re.finditer(r"\n\s*\n", search_text)]
    if para_matches:
        return search_start + para_matches[-1]

    # 2. Sentence boundary (. ! ? । followed by whitespace)
    sentence_matches = [m.end() for m in re.finditer(r"[.!?\u0964]\s+", search_text)]
    if sentence_matches:
        return search_start + sentence_matches[-1]

    # 3. Word boundary (single whitespace)
    space_matches = [m.end() for m in re.finditer(r"\s+", search_text)]
    if space_matches:
        return search_start + space_matches[-1]

    # Fallback to hard cut
    return max_end


def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    page_number: Optional[int] = None,
    start_index: int = 0,
) -> List[ChunkItem]:
    """
    Split a single continuous text string into overlapping chunks.
    """
    if not text or not text.strip():
        return []

    settings = get_settings()
    size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    if overlap >= size:
        overlap = max(0, size // 5)

    stripped_text = text.strip()
    text_len = len(stripped_text)

    if text_len <= size:
        words = len(stripped_text.split())
        return [
            ChunkItem(
                chunk_index=start_index,
                content=stripped_text,
                character_count=len(stripped_text),
                word_count=words,
                page_number=page_number,
                chunk_metadata={
                    "start_char": 0,
                    "end_char": text_len,
                    "page_number": page_number,
                },
            )
        ]

    chunks: List[ChunkItem] = []
    start = 0
    idx = start_index

    while start < text_len:
        target_end = min(start + size, text_len)
        if target_end == text_len:
            split_end = text_len
        else:
            split_end = find_split_point(stripped_text, start, target_end)

        chunk_content = stripped_text[start:split_end].strip()
        if chunk_content:
            chunks.append(
                ChunkItem(
                    chunk_index=idx,
                    content=chunk_content,
                    character_count=len(chunk_content),
                    word_count=len(chunk_content.split()),
                    page_number=page_number,
                    chunk_metadata={
                        "start_char": start,
                        "end_char": split_end,
                        "page_number": page_number,
                    },
                )
            )
            idx += 1

        if split_end >= text_len:
            break

        next_start = split_end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start

    return chunks


def chunk_pages(
    pages: List[Tuple[int, str]],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[ChunkItem]:
    """
    Chunk page-indexed text list (e.g. from PDF extraction), preserving exact page attribution.
    """
    all_chunks: List[ChunkItem] = []
    current_index = 0

    for page_num, page_text in pages:
        if not page_text or not page_text.strip():
            continue
        page_chunks = chunk_text(
            text=page_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            page_number=page_num,
            start_index=current_index,
        )
        all_chunks.extend(page_chunks)
        current_index += len(page_chunks)

    return all_chunks
