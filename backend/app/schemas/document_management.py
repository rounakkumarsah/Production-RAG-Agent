"""
Schemas for document listing and management endpoints (Phase 3).

Kept separate from app.schemas.document (Phase 2) to honour the
'do not modify previous code' constraint.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import DocumentStatus


class DocumentSummary(BaseModel):
    """Lightweight document row — used in paginated list responses."""

    document_id: uuid.UUID
    filename: str
    status: DocumentStatus
    page_count: int
    chunk_count: int
    file_size_bytes: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    total: int = Field(..., description="Total documents matching the filter")
    page: int = Field(..., description="Current page (1-indexed)")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    documents: list[DocumentSummary]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 42,
                "page": 1,
                "limit": 20,
                "pages": 3,
                "documents": [],
            }
        }
    }


class DocumentDeleteResponse(BaseModel):
    """Confirmation returned after a successful document deletion."""

    document_id: uuid.UUID
    filename: str
    message: str = "Document and associated vectors deleted successfully."

    model_config = {
        "json_schema_extra": {
            "example": {
                "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "filename": "annual_report.pdf",
                "message": "Document and associated vectors deleted successfully.",
            }
        }
    }
