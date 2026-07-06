"""
Pydantic schemas for Qdrant collection CRUD operations.
"""

from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class DistanceMetric(str, Enum):
    COSINE = "Cosine"
    DOT = "Dot"
    EUCLID = "Euclid"
    MANHATTAN = "Manhattan"


# ── Request schemas ───────────────────────────────────────────────────────────

class CollectionCreate(BaseModel):
    """Payload to create a new Qdrant collection."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Collection name (alphanumeric, underscores, hyphens only).",
    )
    vector_size: int = Field(
        768,
        ge=1,
        le=65536,
        description="Dimensionality of vectors (default: 768 for text-embedding-004).",
    )
    distance: DistanceMetric = Field(
        DistanceMetric.COSINE,
        description="Distance metric used for similarity search.",
    )
    on_disk_payload: bool = Field(
        True,
        description="Store payload on disk to reduce RAM usage.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my_collection",
                "vector_size": 768,
                "distance": "Cosine",
                "on_disk_payload": True,
            }
        }
    }


# ── Response schemas ──────────────────────────────────────────────────────────

class VectorsConfig(BaseModel):
    """Vector configuration details for a collection."""

    size: int
    distance: str


class CollectionInfo(BaseModel):
    """Full details for a single Qdrant collection."""

    name: str
    status: str
    vector_count: int = Field(0, ge=0)
    indexed_vectors_count: int = Field(0, ge=0)
    points_count: int = Field(0, ge=0)
    segments_count: int = Field(0, ge=0)
    vectors_config: VectorsConfig | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "documents",
                "status": "green",
                "vector_count": 15000,
                "indexed_vectors_count": 15000,
                "points_count": 15000,
                "segments_count": 2,
                "vectors_config": {"size": 768, "distance": "Cosine"},
            }
        }
    }


class CollectionSummary(BaseModel):
    """Lightweight entry used in list responses."""

    name: str
    vector_count: int = 0
    points_count: int = 0
    status: str = "unknown"


class CollectionListResponse(BaseModel):
    """Paginated list of all Qdrant collections."""

    total: int
    collections: list[CollectionSummary]


class CollectionDeleteResponse(BaseModel):
    """Confirmation returned after a successful collection deletion."""

    name: str
    message: str = "Collection deleted successfully."

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "my_collection",
                "message": "Collection deleted successfully.",
            }
        }
    }
