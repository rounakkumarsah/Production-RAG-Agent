"""
FastAPI application entry point.

Responsibilities:
  - Bootstrap logging
  - Register lifespan (startup / shutdown hooks)
  - Add middleware (CORS, request-ID)
  - Mount all API routers
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.collections import router as collections_router
from app.api.document_management import router as document_management_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.config import get_settings
from app.db import models  # noqa: F401 — registers Phase 2 tables with Base.metadata
from app.db import conversation_models  # noqa: F401 — registers Phase 4 tables
from app.db.postgres import dispose_engine, get_engine
from app.db.postgres import Base
from app.db.qdrant import close_qdrant_client
from app.services.vector_service import ensure_collection
from app.utils.logging import get_logger, setup_logging

# ── Bootstrap logging immediately (before any other import that logs) ─────────
_settings = get_settings()
setup_logging(level=_settings.LOG_LEVEL, environment=_settings.ENVIRONMENT)  # type: ignore[arg-type]
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "Starting %s v%s [%s]",
        _settings.APP_NAME,
        _settings.APP_VERSION,
        _settings.ENVIRONMENT,
    )

    # ── Startup: create PostgreSQL tables ────────────────────────────────────
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("PostgreSQL tables verified / created")

    # ── Startup: ensure Qdrant collection exists ──────────────────────────────
    await ensure_collection()

    # ── Startup: recover stuck documents ──────────────────────────────────────
    from app.services.document_service import recover_stuck_documents
    await recover_stuck_documents()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down — releasing resources …")
    await dispose_engine()
    await close_qdrant_client()
    logger.info("Shutdown complete")


# ── Application factory ───────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-ready RAG Agent API",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request-ID & latency middleware ───────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(
        request: Request, call_next
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "%s %s → %d  (%.2f ms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)            # Phase 1
    app.include_router(documents_router)         # Phase 2 — POST /upload
    app.include_router(document_management_router)  # Phase 3 — GET/DELETE /documents
    app.include_router(collections_router)       # Phase 3 — /collections CRUD
    app.include_router(query_router)             # Phase 4 — POST /query SSE

    return app


app = create_app()
