"""
Cosine Similarity Computation Module.
Provides deterministic, dimension-validated vector cosine similarity computation
for dense semantic retrieval in SahayakAI.

Mathematical Foundation:
    Given two high-dimensional vectors u (query) and v (candidate document chunk):
        cosine_similarity(u, v) = (u · v) / (||u||_2 * ||v||_2)
    where:
        u · v = sum(u_i * v_i)
        ||u||_2 = sqrt(sum(u_i^2))
        ||v||_2 = sqrt(sum(v_i^2))

Why Cosine Similarity for Semantic Retrieval:
    In transformer-based dense representation spaces (such as all-MiniLM-L6-v2),
    semantic orientation indicates conceptual alignment. Cosine similarity evaluates
    the angle between vectors rather than Euclidean magnitude, effectively decoupling
    text length differences from topical relevance. When embeddings are L2-normalized
    (||u||_2 = ||v||_2 = 1.0), cosine similarity simplifies directly to the dot product,
    bounded in [-1.0, 1.0], where 1.0 represents identical orientation and values near
    or below 0.0 indicate semantic independence or divergence.
"""

import math
from typing import Any, List, Sequence
import numpy as np

from backend.app.rag.exceptions import (
    EmbeddingValidationError,
    SimilarityCalculationError,
)
from backend.app.rag.vector_utils import validate_vector


def cosine_similarity(
    vec_a: Any,
    vec_b: Any,
    expected_dim: int = 384,
) -> float:
    """
    Compute cosine similarity between two numeric embedding vectors.

    Args:
        vec_a: First vector (e.g. query embedding), sequence of floats or numpy array.
        vec_b: Second vector (e.g. document chunk embedding).
        expected_dim: Expected dimensionality (default: 384).

    Returns:
        Float similarity score in the range [-1.0, 1.0]. Returns 0.0 if either vector
        is a zero-magnitude vector.

    Raises:
        EmbeddingValidationError: If vector dimensions mismatch, are non-numeric,
            or contain NaN / Inf values.
        SimilarityCalculationError: If an unexpected numerical error occurs.
    """
    try:
        # Validate and convert vectors to validated float lists
        val_a = validate_vector(vec_a, expected_dim=expected_dim)
        val_b = validate_vector(vec_b, expected_dim=expected_dim)
    except EmbeddingValidationError:
        raise
    except Exception as exc:
        raise EmbeddingValidationError(f"Invalid vector supplied for similarity: {str(exc)}")

    try:
        arr_a = np.array(val_a, dtype=np.float32)
        arr_b = np.array(val_b, dtype=np.float32)

        norm_a = float(np.linalg.norm(arr_a))
        norm_b = float(np.linalg.norm(arr_b))

        # Safe zero-vector handling
        if norm_a <= 1e-12 or norm_b <= 1e-12:
            return 0.0

        dot_product = float(np.dot(arr_a, arr_b))
        sim = dot_product / (norm_a * norm_b)

        # Numerical clamping to strictly preserve [-1.0, 1.0] boundary
        if math.isnan(sim):
            return 0.0
        return float(max(-1.0, min(1.0, sim)))

    except Exception as exc:
        raise SimilarityCalculationError(
            message=f"Failed to calculate cosine similarity: {str(exc)}",
            details={"error": str(exc)},
        )


def compute_chunk_similarities(
    query_vector: Sequence[float],
    chunk_vectors: Sequence[Sequence[float]],
    expected_dim: int = 384,
) -> List[float]:
    """
    Compute cosine similarities between a single query vector and a sequence
    of candidate chunk vectors.

    Args:
        query_vector: 1D query vector.
        chunk_vectors: List of candidate chunk vectors.
        expected_dim: Expected dimension for all vectors.

    Returns:
        List of float similarity scores corresponding 1-to-1 with chunk_vectors.
    """
    if not chunk_vectors:
        return []

    q_val = validate_vector(query_vector, expected_dim=expected_dim)
    q_arr = np.array(q_val, dtype=np.float32)
    norm_q = float(np.linalg.norm(q_arr))

    if norm_q <= 1e-12:
        return [0.0 for _ in chunk_vectors]

    results: List[float] = []
    for vec in chunk_vectors:
        results.append(cosine_similarity(q_arr, vec, expected_dim=expected_dim))

    return results
