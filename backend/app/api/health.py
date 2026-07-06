"""
Health API router.
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_health

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    description=(
        "Returns the connectivity status for Gemini, PostgreSQL, and Qdrant. "
        "Overall `status` is `ok` only when all services are reachable."
    ),
)
async def health_check() -> HealthResponse:
    return await get_health()
