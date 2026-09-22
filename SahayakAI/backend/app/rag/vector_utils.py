"""
Vector Serialization, Deserialization, and Validation Utilities.
Ensures numeric vector integrity, dimensional correctness, and safe JSON persistence
without pickle or unsafe object deserialization.
"""

import json
import math
from typing import Any, List, Sequence
import numpy as np

from backend.app.rag.exceptions import EmbeddingValidationError


def validate_vector(vector: Any, expected_dim: int = 384) -> List[float]:
    """
    Validate that an embedding vector is a valid 1D sequence of finite floats
    matching the expected dimension.
    """
    if vector is None:
        raise EmbeddingValidationError("Vector cannot be None.")

    # Support numpy array, list, tuple
    if isinstance(vector, np.ndarray):
        if vector.ndim != 1:
            raise EmbeddingValidationError(f"Expected 1D vector, got ndim={vector.ndim}.")
        raw_list = vector.tolist()
    elif isinstance(vector, (list, tuple)):
        raw_list = list(vector)
    else:
        raise EmbeddingValidationError(
            f"Invalid vector container type: {type(vector).__name__}. Expected list or numpy.ndarray."
        )

    if len(raw_list) != expected_dim:
        raise EmbeddingValidationError(
            f"Vector dimension mismatch: expected {expected_dim}, got {len(raw_list)}."
        )

    validated: List[float] = []
    for i, val in enumerate(raw_list):
        if not isinstance(val, (int, float, np.floating, np.integer)):
            raise EmbeddingValidationError(
                f"Element at index {i} has invalid non-numeric type: {type(val).__name__}."
            )
        float_val = float(val)
        if math.isnan(float_val) or math.isinf(float_val):
            raise EmbeddingValidationError(
                f"Element at index {i} is invalid (NaN or Inf)."
            )
        validated.append(float_val)

    return validated


def serialize_vector(vector: Any, expected_dim: int = 384) -> List[float]:
    """
    Serialize an embedding vector to a clean Python list of floats
    suitable for SQLAlchemy JSON column persistence.
    """
    return validate_vector(vector, expected_dim=expected_dim)


def deserialize_vector(data: Any, expected_dim: int = 384) -> List[float]:
    """
    Deserialize an embedding from stored JSON string or parsed JSON list.
    Enforces strict dimension and numerical checks on deserialization.
    """
    if data is None:
        raise EmbeddingValidationError("Cannot deserialize None into vector.")

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except Exception as err:
            raise EmbeddingValidationError(f"Failed to parse JSON vector string: {str(err)}")
    else:
        parsed = data

    return validate_vector(parsed, expected_dim=expected_dim)
