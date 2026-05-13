"""Magic-byte MIME detection and upload validation."""

import magic
from fastapi import HTTPException

from app.config import Settings
from app.models.errors import ErrorCode

ALLOWED_MIMES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


def detect_mime_type(file_bytes: bytes) -> str:
    """Detect MIME type from first 2048 bytes using magic bytes."""
    sample = file_bytes[:2048]
    mime = magic.from_buffer(sample, mime=True)
    return mime


def validate_upload(
    filename: str,
    file_bytes: bytes,
    file_size: int,
    settings: Settings,
) -> str:
    """
    Validate the uploaded file. Returns the detected file_type ('pdf', 'txt', 'docx').
    Raises HTTPException with correct ErrorCode on validation failure.
    """
    # Empty file check
    if file_size == 0 or len(file_bytes) == 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.EMPTY_FILE,
                "message": "Uploaded file is empty",
            },
        )

    # Size check (bytes)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error_code": ErrorCode.FILE_TOO_LARGE,
                "message": (
                    f"File exceeds maximum allowed size of "
                    f"{settings.MAX_FILE_SIZE_MB} MB"
                ),
            },
        )

    # MIME type check
    mime = detect_mime_type(file_bytes)

    # Accept exact MIME matches
    if mime in ALLOWED_MIMES:
        return ALLOWED_MIMES[mime]

    # Accept any text/* as txt
    if mime.startswith("text/"):
        return "txt"

    raise HTTPException(
        status_code=422,
        detail={
            "error_code": ErrorCode.INVALID_MIME_TYPE,
            "message": (
                f"Unsupported file type '{mime}'. "
                f"Accepted types: PDF, DOCX, TXT"
            ),
        },
    )
