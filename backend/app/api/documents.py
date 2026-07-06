"""
Document upload API router.

POST /upload  — Accept 1–N PDF files, run the ingestion pipeline,
                return per-file status.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.schemas.document import UploadResponse
from app.services.document_service import process_uploads
from app.utils.file_utils import validate_document_upload
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and ingest documents",
    description=(
        "Accept one or more files. Each file is:\n"
        "1. Validated (size limit and supported format)\n"
        "2. Text-extracted with the corresponding parser\n"
        "3. Recursively chunked\n"
        "4. Embedded via Gemini text-embedding-004\n"
        "5. Stored in Qdrant (vectors) and PostgreSQL (metadata)\n\n"
        "A per-file status is returned regardless of individual failures."
    ),
)
async def upload_documents(
    files: list[UploadFile] = File(
        ...,
        description="One or more files (max 50 MB each).",
    ),
) -> UploadResponse:
    settings = get_settings()

    # ── Guard: file count ─────────────────────────────────────────────────────
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file must be provided.",
        )

    if len(files) > settings.MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Too many files. Maximum {settings.MAX_FILES_PER_UPLOAD} "
                f"files per request, received {len(files)}."
            ),
        )

    # ── Validate and buffer all files before starting the pipeline ────────────
    # This ensures we reject invalid uploads immediately, before any DB writes.
    file_payloads: list[tuple[str, bytes]] = []

    for upload in files:
        raw_filename = upload.filename or "unknown.ext"
        # Sanitize against path traversal (handles both / and \ regardless of OS)
        filename = raw_filename.replace("\\", "/").split("/")[-1]
        logger.info("Received upload: '%s' (content-type=%s)", filename, upload.content_type)

        try:
            content = await validate_document_upload(upload, settings)
        except HTTPException:
            raise  # propagate validation errors as-is
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read file '{filename}': {exc}",
            ) from exc

        file_payloads.append((filename, content))

    # ── Run the ingestion pipeline ─────────────────────────────────────────────
    logger.info("Starting ingestion pipeline for %d file(s)", len(file_payloads))
    response = await process_uploads(file_payloads)

    logger.info(
        "Upload complete — total=%d succeeded=%d failed=%d",
        response.total,
        response.succeeded,
        response.failed,
    )
    return response
