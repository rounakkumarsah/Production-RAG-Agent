"""
SQLAlchemy ORM models.

All models inherit from Base (defined in app.db.postgres).
Tables are created on startup via Base.metadata.create_all.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.postgres import Base


class DocumentStatus(str, PyEnum):
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    ALREADY_EXISTS = "already_exists"


class Document(Base):
    """
    Persists metadata for every uploaded PDF.

    Lifecycle:
        PENDING → PARSING → CHUNKING → EMBEDDING → INDEXING → COMPLETED
                                                            ↘ FAILED
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="documentstatus", create_type=True),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Progress Tracking
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    embedded_chunks: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    failed_chunks: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(64), default="pending", server_default="pending", nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # New Multi-Format & OCR Metadata
    file_type: Mapped[str] = mapped_column(String(32), default="pdf", server_default="pdf", nullable=False)
    parser_used: Mapped[str] = mapped_column(String(64), default="PyMuPDF", server_default="PyMuPDF", nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    ocr_engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(64), default="native", server_default="native", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id} filename={self.filename!r} "
            f"status={self.status.value} chunks={self.chunk_count}>"
        )
