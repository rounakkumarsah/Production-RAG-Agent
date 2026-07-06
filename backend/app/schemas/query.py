"""
Pydantic schemas for the RAG query endpoint and SSE event stream (Phase 4).
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Body accepted by POST /query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The user's natural-language question.",
    )
    conversation_id: uuid.UUID | None = Field(
        None,
        description=(
            "UUID of an existing conversation to continue. "
            "Omit (or send null) to start a new conversation."
        ),
    )
    top_k: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve from the vector store.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What are the main risk factors discussed in the report?",
                "conversation_id": None,
                "top_k": 5,
            }
        }
    }


# ── Source citation ───────────────────────────────────────────────────────────

class SourceCitation(BaseModel):
    """A single retrieved chunk that was used to answer the query."""

    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text_snippet: str = Field(..., description="First 300 chars of the chunk text.")
    score: float = Field(..., description="Cosine similarity score (0–1).")


# ── SSE event payloads ────────────────────────────────────────────────────────

class SSEThinking(BaseModel):
    """Emitted immediately to signal the pipeline has started."""
    type: Literal["thinking"] = "thinking"


class SSESources(BaseModel):
    """Emitted after retrieval — before any generated tokens."""
    type: Literal["sources"] = "sources"
    sources: list[SourceCitation]
    retrieved_count: int


class SSEChunk(BaseModel):
    """One streaming token (or small group of tokens) from the LLM."""
    type: Literal["chunk"] = "chunk"
    content: str


class SSEDone(BaseModel):
    """Emitted once the full answer has been streamed."""
    type: Literal["done"] = "done"
    conversation_id: str
    total_chars: int


class SSEError(BaseModel):
    """Emitted on any unrecoverable pipeline error."""
    type: Literal["error"] = "error"
    message: str
