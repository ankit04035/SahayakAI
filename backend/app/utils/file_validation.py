"""
File Upload Validation Utilities.
Validates file extensions, size constraints, magic bytes, and text encodings.
"""

from typing import Tuple
from backend.app.config import get_settings
from backend.app.exceptions import AppException

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}

PDF_MAGIC_BYTES = b"%PDF-"


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension with dot."""
    if not filename or "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def validate_file_metadata(filename: str, content_length: int | None = None) -> str:
    """
    Validate filename extension and optional content length header.
    Returns the normalized extension.
    """
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise AppException(
            message=f"Unsupported file type '{ext}'. Allowed types: {allowed}",
            status_code=400,
            error_code="INVALID_FILE_TYPE",
        )

    settings = get_settings()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if content_length is not None and content_length > max_bytes:
        raise AppException(
            message=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            status_code=413,
            error_code="FILE_TOO_LARGE",
        )

    return ext


def validate_file_content(content: bytes, extension: str) -> Tuple[str, str]:
    """
    Validate raw byte content for size, magic bytes, and text validity.
    Returns (mime_type, detected_encoding).
    """
    settings = get_settings()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if not content or len(content) == 0:
        raise AppException(
            message="Uploaded file is empty.",
            status_code=400,
            error_code="EMPTY_FILE",
        )

    if len(content) > max_bytes:
        raise AppException(
            message=f"File size ({len(content)} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            status_code=413,
            error_code="FILE_TOO_LARGE",
        )

    ext = extension.lower()
    if ext == ".pdf":
        if PDF_MAGIC_BYTES not in content[:1024]:
            raise AppException(
                message="Uploaded file is not a valid PDF document (missing %PDF- header).",
                status_code=400,
                error_code="INVALID_FILE_CONTENT",
            )
        return "application/pdf", "binary"

    elif ext == ".txt":
        if b"\x00" in content:
            raise AppException(
                message="Uploaded file appears to be binary data, not plain text.",
                status_code=400,
                error_code="INVALID_FILE_CONTENT",
            )

        encodings = ["utf-8", "utf-8-sig", "latin-1", "windows-1252", "iso-8859-1"]
        decoded_text = None
        detected_enc = "utf-8"
        for enc in encodings:
            try:
                decoded_text = content.decode(enc)
                detected_enc = enc
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise AppException(
                message="Unable to decode plain text file with supported encodings.",
                status_code=400,
                error_code="INVALID_FILE_CONTENT",
            )

        if not decoded_text.strip():
            raise AppException(
                message="Uploaded text file contains only whitespace.",
                status_code=400,
                error_code="EMPTY_FILE",
            )

        return "text/plain", detected_enc

    raise AppException(
        message=f"Unsupported file extension '{ext}'.",
        status_code=400,
        error_code="INVALID_FILE_TYPE",
    )
