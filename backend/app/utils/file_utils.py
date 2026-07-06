"""
File validation utilities for upload endpoints.
"""

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

_ALLOWED_EXTENSIONS = {
    "pdf", "docx", "pptx", "xlsx", "csv", "txt", "md", "markdown",
    "png", "jpg", "jpeg", "tiff", "bmp", "webp", "json", "log"
}

async def validate_document_upload(file: UploadFile, settings=None) -> bytes:
    """
    Read the uploaded file into memory and validate:
      1. File size does not exceed MAX_UPLOAD_SIZE_MB
      2. File format is supported
    
    Returns the raw bytes so the caller doesn't re-read from disk.
    Raises HTTPException on any violation.
    """
    if settings is None:
        settings = get_settings()

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Read entire file into memory (bounded by max_bytes + 1 so we can detect oversize)
    content = await file.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File '{file.filename}' exceeds the maximum allowed size "
                f"of {settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' is empty.",
        )

    filename = file.filename or ""
    ext = filename.lower().split('.')[-1] if '.' in filename else ""
    
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File '{filename}' has an unsupported extension '{ext}'."
        )

    # 3. Magic bytes verification (prevent MIME spoofing)
    header = content[:8]
    is_valid_magic = False
    
    if ext == "pdf" and header.startswith(b"%PDF-"):
        is_valid_magic = True
    elif ext in {"docx", "pptx", "xlsx"} and header.startswith(b"PK\x03\x04"):
        is_valid_magic = True
    elif ext == "png" and header.startswith(b"\x89PNG\r\n\x1a\n"):
        is_valid_magic = True
    elif ext in {"jpg", "jpeg"} and header.startswith(b"\xff\xd8\xff"):
        is_valid_magic = True
    elif ext in {"txt", "md", "markdown", "csv", "json", "log"}:
        # Text files don't have standard magic bytes; verify they contain valid text
        # Attempt decoding with UTF-8, Windows-1252, and Latin-1 fallbacks, ensuring no null bytes
        is_valid_magic = False
        for encoding in ["utf-8", "windows-1252", "latin-1"]:
            try:
                decoded = content[:1024].decode(encoding)
                if "\x00" not in decoded:
                    is_valid_magic = True
                    break
            except UnicodeDecodeError:
                continue
    else:
        # Fallback for other image formats (tiff, bmp, webp) if not strictly checked
        is_valid_magic = True
        
    if not is_valid_magic:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File '{filename}' content does not match extension '{ext}'."
        )

    return content
