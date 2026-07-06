"""
Document query & management service (Phase 3).

Provides:
  - Paginated listing of Document rows from PostgreSQL
  - Hard-delete: removes the PostgreSQL row AND all associated Qdrant vectors

This module is intentionally separate from document_service.py (Phase 2 upload
pipeline) so that Phase 2 code is never touched.
"""

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select

from app.db.models import Document, DocumentStatus
from app.db.postgres import get_db_session
from app.schemas.document_management import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentSummary,
)
from app.services.vector_service import delete_by_document_id
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def list_documents(
    page: int = 1,
    limit: int = 20,
    status: DocumentStatus | None = None,
) -> DocumentListResponse:
    """
    Return a paginated list of all Document rows, optionally filtered by status.

    Args:
        page:   1-indexed page number.
        limit:  Rows per page (1–100).
        status: Optional filter on DocumentStatus.

    Returns:
        DocumentListResponse with documents and pagination metadata.
    """
    offset = (page - 1) * limit

    async with get_db_session() as session:
        # ── Base query ────────────────────────────────────────────────────────
        base_q = select(Document)
        count_q = select(func.count()).select_from(Document)

        if status is not None:
            base_q = base_q.where(Document.status == status)
            count_q = count_q.where(Document.status == status)

        # ── Total count ───────────────────────────────────────────────────────
        total: int = (await session.execute(count_q)).scalar_one()

        # ── Paginated fetch ───────────────────────────────────────────────────
        rows_result = await session.execute(
            base_q
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows: list[Document] = list(rows_result.scalars().all())

    pages = max(1, math.ceil(total / limit))

    summaries = [
        DocumentSummary(
            document_id=row.id,
            filename=row.filename,
            status=row.status,
            page_count=row.page_count,
            chunk_count=row.chunk_count,
            file_size_bytes=row.file_size,
            error=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]

    logger.info(
        "list_documents → total=%d page=%d/%d limit=%d status=%s",
        total, page, pages, limit, status,
    )

    return DocumentListResponse(
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        documents=summaries,
    )


async def delete_document(document_id: uuid.UUID) -> DocumentDeleteResponse:
    """
    Hard-delete a document: remove its Qdrant vectors first, then the PG row.

    Qdrant vectors are deleted before the PG row so that a partial failure
    (Qdrant down) leaves the PG record intact and the operation can be retried.

    Args:
        document_id: UUID of the document to delete.

    Returns:
        DocumentDeleteResponse on success.

    Raises:
        KeyError: If no document with the given ID exists.
    """
    # ── 1. Fetch document metadata ────────────────────────────────────────────
    async with get_db_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc: Document | None = result.scalar_one_or_none()

    if doc is None:
        raise KeyError(f"Document '{document_id}' not found.")

    filename = doc.filename
    doc_id_str = str(document_id)

    logger.info("Deleting document id=%s filename='%s'", doc_id_str, filename)

    # ── 2. Delete vectors from Qdrant (fail-safe first) ───────────────────────
    try:
        await delete_by_document_id(doc_id_str)
        logger.info("Qdrant vectors deleted for document_id=%s", doc_id_str)
    except Exception as exc:
        # Log and re-raise; PG row intentionally NOT deleted on Qdrant failure
        logger.error(
            "Failed to delete Qdrant vectors for document_id=%s: %s — aborting delete",
            doc_id_str,
            exc,
        )
        raise RuntimeError(
            f"Vector deletion failed ({exc}). PostgreSQL record preserved for retry."
        ) from exc

    # ── 3. Delete PostgreSQL row ──────────────────────────────────────────────
    async with get_db_session() as session:
        await session.execute(
            delete(Document).where(Document.id == document_id)
        )

    logger.info("Document id=%s deleted successfully", doc_id_str)

    return DocumentDeleteResponse(
        document_id=document_id,
        filename=filename,
    )
