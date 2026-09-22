"""
Filename Sanitization and Storage Security Utilities.
Prevents directory traversal, dangerous path characters, and collisions.
"""

import os
import re
import uuid
from pathlib import Path
from backend.app.exceptions import AppException


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted user-supplied filename.
    Removes directory traversal sequences, path separators, drive letters, and unsafe characters.
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_document.txt"

    # Strip whitespace
    name = filename.strip()

    # Normalize forward/back slashes and extract just the basename
    name = name.replace("\\", "/")
    name = os.path.basename(name)

    # Remove drive letters (e.g. C:)
    name = re.sub(r"^[a-zA-Z]:", "", name)

    # Remove path traversal sequences like ../ or ..
    name = re.sub(r"\.\.+[/]?", "", name)

    # Replace characters other than alphanumeric, dots, hyphens, and underscores
    # Support unicode characters in international filenames but strip shell-sensitive ones
    name = re.sub(r"[^\w\.\-\u0900-\u097F]", "_", name)

    # Collapse multiple dots or underscores
    name = re.sub(r"\.{2,}", ".", name)
    name = re.sub(r"_{2,}", "_", name)

    # Strip leading/trailing dots and underscores
    name = name.strip("._")

    # If completely stripped, provide fallback
    if not name or name == ".":
        name = "unnamed_document.txt"

    # Enforce maximum filename length
    max_len = 128
    if len(name) > max_len:
        stem, ext = os.path.splitext(name)
        ext = ext[:10]
        stem = stem[: max_len - len(ext)]
        name = f"{stem}{ext}"

    return name


def generate_stored_filename(original_filename: str) -> str:
    """
    Generate a collision-free, safe stored filename using UUIDv4 prefix.
    """
    safe_name = sanitize_filename(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}_{safe_name}"


def get_safe_storage_path(base_dir: str | Path, stored_filename: str) -> Path:
    """
    Verify and resolve absolute path within base storage directory.
    Guarantees the target path does not escape the configured base directory.
    """
    base_path = Path(base_dir).resolve()
    target_path = (base_path / stored_filename).resolve()

    if not target_path.is_relative_to(base_path):
        raise AppException(
            message="Path traversal detected in file storage operation.",
            status_code=400,
            error_code="PATH_TRAVERSAL_DETECTED",
        )

    return target_path
