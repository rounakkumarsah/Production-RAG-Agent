"""
Qdrant client singleton.

Exposes a single QdrantClient instance shared across the application.
"""

from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Return the application-level Qdrant async client (lazy init)."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.QDRANT_API_KEY,
            timeout=10,
        )
        logger.info("Qdrant client created — url=%s", settings.qdrant_url)
    return _qdrant_client


async def close_qdrant_client() -> None:
    """Gracefully close the Qdrant client on shutdown."""
    global _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        logger.info("Qdrant client closed")
        _qdrant_client = None
