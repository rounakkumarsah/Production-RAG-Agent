"""
Qdrant collection CRUD service (Phase 3).

Wraps AsyncQdrantClient operations in domain-layer functions so the API
router stays thin and can be tested independently.

Operations:
  - list_collections   → GET  /collections
  - get_collection     → GET  /collections/{name}
  - create_collection  → POST /collections
  - delete_collection  → DELETE /collections/{name}
"""

from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import get_settings
from app.db.qdrant import get_qdrant_client
from app.schemas.collection import (
    CollectionCreate,
    CollectionDeleteResponse,
    CollectionInfo,
    CollectionListResponse,
    CollectionSummary,
    VectorsConfig,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_vectors_config(info) -> VectorsConfig | None:
    """
    Safely pull the vector size and distance from a CollectionInfo response.
    Qdrant's response schema varies slightly between versions, so we guard with
    try/except rather than relying on a single attribute path.
    """
    try:
        cfg = info.config.params.vectors
        # Named-vectors collections have a dict; single-vector has an object
        if isinstance(cfg, dict):
            first = next(iter(cfg.values()))
            return VectorsConfig(size=first.size, distance=str(first.distance.value))
        return VectorsConfig(size=cfg.size, distance=str(cfg.distance.value))
    except Exception:
        return None


def _safe_count(info, attr: str, default: int = 0) -> int:
    """Return an int attribute from the Qdrant info object, defaulting on None."""
    val = getattr(info, attr, None)
    return int(val) if val is not None else default


# ── Public service functions ──────────────────────────────────────────────────

async def list_collections() -> CollectionListResponse:
    """
    Return all Qdrant collections with lightweight stats.

    Stats (vector_count, points_count) are fetched individually so the list
    stays accurate even for newly created empty collections.
    """
    client = get_qdrant_client()

    collections_resp = await client.get_collections()
    summaries: list[CollectionSummary] = []

    for col in collections_resp.collections:
        try:
            detail = await client.get_collection(collection_name=col.name)
            summaries.append(CollectionSummary(
                name=col.name,
                vector_count=_safe_count(detail, "vectors_count"),
                points_count=_safe_count(detail, "points_count"),
                status=str(detail.status.value) if detail.status else "unknown",
            ))
        except Exception as exc:
            logger.warning("Could not fetch stats for collection '%s': %s", col.name, exc)
            summaries.append(CollectionSummary(name=col.name))

    logger.info("Listed %d Qdrant collections", len(summaries))
    return CollectionListResponse(total=len(summaries), collections=summaries)


async def get_collection(name: str) -> CollectionInfo:
    """
    Return detailed info for a single collection.

    Raises:
        KeyError: If the collection does not exist.
    """
    client = get_qdrant_client()

    try:
        info = await client.get_collection(collection_name=name)
    except UnexpectedResponse as exc:
        if exc.status_code == 404:
            raise KeyError(f"Collection '{name}' not found.") from exc
        raise

    result = CollectionInfo(
        name=name,
        status=str(info.status.value) if info.status else "unknown",
        vector_count=_safe_count(info, "vectors_count"),
        indexed_vectors_count=_safe_count(info, "indexed_vectors_count"),
        points_count=_safe_count(info, "points_count"),
        segments_count=_safe_count(info, "segments_count"),
        vectors_config=_extract_vectors_config(info),
    )

    logger.info(
        "Fetched collection '%s': %d vectors, status=%s",
        name, result.vector_count, result.status,
    )
    return result


async def create_collection(payload: CollectionCreate) -> CollectionInfo:
    """
    Create a new Qdrant collection.

    Raises:
        ValueError: If a collection with the same name already exists.
    """
    client = get_qdrant_client()

    # Guard: check existence first (Qdrant raises 400, not 409, on duplicate)
    existing = await client.get_collections()
    names = {c.name for c in existing.collections}
    if payload.name in names:
        raise ValueError(f"Collection '{payload.name}' already exists.")

    # Map the schema distance enum to the Qdrant SDK enum
    distance_map: dict[str, qmodels.Distance] = {
        "Cosine":    qmodels.Distance.COSINE,
        "Dot":       qmodels.Distance.DOT,
        "Euclid":    qmodels.Distance.EUCLID,
        "Manhattan": qmodels.Distance.MANHATTAN,
    }
    qdrant_distance = distance_map.get(payload.distance.value, qmodels.Distance.COSINE)

    await client.create_collection(
        collection_name=payload.name,
        vectors_config=qmodels.VectorParams(
            size=payload.vector_size,
            distance=qdrant_distance,
        ),
        on_disk_payload=payload.on_disk_payload,
    )

    # Create a document_id payload index by default for all new collections
    try:
        await client.create_payload_index(
            collection_name=payload.name,
            field_name="document_id",
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )
    except Exception as exc:
        logger.warning("Could not create payload index on '%s': %s", payload.name, exc)

    logger.info(
        "Created collection '%s' (size=%d distance=%s on_disk=%s)",
        payload.name, payload.vector_size, payload.distance.value, payload.on_disk_payload,
    )

    # Return a fresh get so the response reflects the actual stored config
    return await get_collection(payload.name)


async def delete_collection(name: str) -> CollectionDeleteResponse:
    """
    Delete a Qdrant collection and all its vectors.

    Raises:
        KeyError:   If the collection does not exist.
        ValueError: If the caller tries to delete the system default collection.
    """
    settings = get_settings()
    client = get_qdrant_client()

    # Guard: disallow deleting the primary RAG collection via this endpoint
    if name == settings.QDRANT_COLLECTION:
        raise ValueError(
            f"Cannot delete the primary collection '{name}' through this endpoint. "
            "Use DELETE /documents/{id} to remove individual documents instead."
        )

    # Guard: existence check
    existing = await client.get_collections()
    names = {c.name for c in existing.collections}
    if name not in names:
        raise KeyError(f"Collection '{name}' not found.")

    await client.delete_collection(collection_name=name)

    logger.info("Deleted Qdrant collection '%s'", name)
    return CollectionDeleteResponse(name=name)
