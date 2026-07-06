"""
Pydantic schemas for the document upload API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import DocumentStatus


# ── Per-document result ────────────────────────────────────────────────────────

class DocumentResult(BaseModel):
    """Result for a single uploaded file."""

    document_id: uuid.UUID | None = None
    filename: str
    status: DocumentStatus
    page_count: int | None = Field(None, ge=0)
    chunk_count: int | None = Field(None, ge=0)
    file_size_bytes: int | None = Field(None, ge=0)
    error: str | None = None
    created_at: datetime | None = None
    
    # ── Fields for duplicates ──────────────────────────────────────────────────
    message: str | None = None
    existing_document_id: uuid.UUID | None = None
    uploaded_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "filename": "annual_report.pdf",
                "status": "completed",
                "page_count": 42,
                "chunk_count": 178,
                "file_size_bytes": 4194304,
                "error": None,
                "created_at": "2026-07-02T11:00:00Z",
            }
        },
    }


# ── Aggregate upload response ──────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Aggregated result returned by POST /upload."""

    total: int = Field(..., description="Total files submitted")
    succeeded: int = Field(..., description="Files processed successfully")
    failed: int = Field(..., description="Files that encountered errors")
    documents: list[DocumentResult]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 2,
                "succeeded": 2,
                "failed": 0,
                "documents": [],
            }
        }
    }
