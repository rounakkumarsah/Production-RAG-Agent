"""
Document management API router (Phase 3).

New endpoints added without touching Phase 2 code:
  GET    /documents            — paginated document list
  DELETE /documents/{id}       — delete document + vectors
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.db.models import DocumentStatus
from app.schemas.document_management import (
    DocumentDeleteResponse,
    DocumentListResponse,
)
from app.services.document_query_service import delete_document, list_documents
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Document Management"])


# ── GET /documents ─────────────────────────────────────────────────────────────

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
    description=(
        "Returns a paginated list of all documents, sorted by upload date "
        "descending. Optionally filter by processing status."
    ),
)
async def list_documents_endpoint(
    page: Annotated[
        int,
        Query(ge=1, description="Page number (1-indexed)."),
    ] = 1,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Items per page (max 100)."),
    ] = 20,
    status: Annotated[
        DocumentStatus | None,
        Query(description="Filter by document status."),
    ] = None,
) -> DocumentListResponse:
    return await list_documents(page=page, limit=limit, status=status)


# ── DELETE /documents/{id} ────────────────────────────────────────────────────

@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document and all its vectors",
    description=(
        "Permanently removes the document record from PostgreSQL and all "
        "associated vector embeddings from Qdrant. This operation is "
        "**irreversible**. Qdrant vectors are deleted first so the PostgreSQL "
        "record is preserved on vector-store failure, enabling safe retries."
    ),
)
async def delete_document_endpoint(
    document_id: Annotated[
        uuid.UUID,
        Path(description="UUID of the document to delete."),
    ],
) -> DocumentDeleteResponse:
    try:
        return await delete_document(document_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        # Qdrant deletion failed; PG row is safe, tell the caller to retry
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
