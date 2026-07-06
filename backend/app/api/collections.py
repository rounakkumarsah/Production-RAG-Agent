"""
Collections CRUD API router (Phase 3).

Endpoints:
  GET    /collections           — list all collections with stats
  POST   /collections           — create a new collection
  GET    /collections/{name}    — get single collection details
  DELETE /collections/{name}    — delete a collection (primary collection protected)
"""

from fastapi import APIRouter, HTTPException, Path, status
from typing import Annotated

from app.schemas.collection import (
    CollectionCreate,
    CollectionDeleteResponse,
    CollectionInfo,
    CollectionListResponse,
)
from app.services.collection_service import (
    create_collection,
    delete_collection,
    get_collection,
    list_collections,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/collections", tags=["Collections"])


# ── GET /collections ──────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=CollectionListResponse,
    summary="List all Qdrant collections",
    description=(
        "Returns all collections present in the Qdrant instance, each with "
        "a lightweight stats snapshot (vector count, points count, status)."
    ),
)
async def list_collections_endpoint() -> CollectionListResponse:
    return await list_collections()


# ── POST /collections ─────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=CollectionInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Qdrant collection",
    description=(
        "Creates a new vector collection with the specified configuration. "
        "A `document_id` keyword payload index is created automatically. "
        "Returns the full collection details as stored in Qdrant."
    ),
)
async def create_collection_endpoint(
    payload: CollectionCreate,
) -> CollectionInfo:
    try:
        return await create_collection(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# ── GET /collections/{name} ───────────────────────────────────────────────────

@router.get(
    "/{name}",
    response_model=CollectionInfo,
    summary="Get collection details",
    description=(
        "Returns full configuration and runtime statistics for the named "
        "collection (vector count, index status, segment count, vector config)."
    ),
)
async def get_collection_endpoint(
    name: Annotated[str, Path(description="Collection name.")],
) -> CollectionInfo:
    try:
        return await get_collection(name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ── DELETE /collections/{name} ────────────────────────────────────────────────

@router.delete(
    "/{name}",
    response_model=CollectionDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a Qdrant collection",
    description=(
        "Permanently deletes the named collection and **all** its vectors. "
        "This operation is **irreversible**.\n\n"
        "> **Note**: The primary RAG collection (configured via "
        "`QDRANT_COLLECTION`) is protected and cannot be deleted through this "
        "endpoint. Use `DELETE /documents/{id}` to remove individual documents."
    ),
)
async def delete_collection_endpoint(
    name: Annotated[str, Path(description="Collection name to delete.")],
) -> CollectionDeleteResponse:
    try:
        return await delete_collection(name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        # Primary collection protection or other business-rule violations
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
