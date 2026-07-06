"""
Semantic retrieval service (Phase 4).

Embeds a query using Gemini (RETRIEVAL_QUERY task type) and performs
an ANN search against the Qdrant collection.

Reuses the existing embed_texts() from Phase 2 — task_type is the only
difference between document ingestion and query embedding.
"""

from dataclasses import dataclass

from app.config import get_settings
from app.db.qdrant import get_qdrant_client
from app.services.embedding_service import embed_batch_with_retry
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A single chunk returned by the vector search."""

    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float   # cosine similarity (0 – 1)


async def retrieve_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
    collection_name: str | None = None,
) -> list[RetrievedChunk]:
    """
    Embed *query* and return the top-k most semantically similar chunks.

    Args:
        query:            Natural-language question from the user.
        top_k:            Maximum number of chunks to return.
        score_threshold:  Minimum cosine similarity to include a result.
                          Set to 0.0 to accept all results.
        collection_name:  Override the default collection from settings.

    Returns:
        List of RetrievedChunk, sorted by score descending.
    """
    settings = get_settings()
    client = get_qdrant_client()
    coll = collection_name or settings.QDRANT_COLLECTION

    # Embed the query with RETRIEVAL_QUERY task type (different from RETRIEVAL_DOCUMENT)
    vectors = await embed_batch_with_retry([query], task_type="RETRIEVAL_QUERY")
    query_vector = vectors[0]

    search_results = await client.search(
        collection_name=coll,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )

    # Log all raw candidate scores before filtering
    if search_results:
        logger.info("Raw candidate scores before filtering for query '%s':", query)
        for i, hit in enumerate(search_results):
            payload = hit.payload or {}
            filename = payload.get("filename", "unknown")
            logger.info("  Candidate #%d: filename='%s' score=%.4f", i+1, filename, hit.score)
    else:
        logger.info("No raw candidates returned from Qdrant search.")

    chunks: list[RetrievedChunk] = []
    
    if search_results:
        import uuid
        from sqlalchemy import select
        from app.db.postgres import get_db_session
        from app.db.models import Document
        
        doc_ids = set()
        for hit in search_results:
            payload = hit.payload or {}
            doc_id_str = payload.get("document_id")
            if doc_id_str:
                try:
                    doc_ids.add(uuid.UUID(doc_id_str))
                except ValueError:
                    pass
        
        valid_docs = set()
        if doc_ids:
            async with get_db_session() as session:
                from app.db.models import DocumentStatus
                res = await session.execute(
                    select(Document.id).where(
                        Document.id.in_(doc_ids),
                        Document.status == DocumentStatus.COMPLETED
                    )
                )
                valid_docs = {str(r[0]) for r in res}
                
        # First gather all valid chunks (excluding orphans)
        valid_candidates: list[RetrievedChunk] = []
        for hit in search_results:
            payload = hit.payload or {}
            doc_id_str = payload.get("document_id", "")
            if doc_id_str not in valid_docs:
                logger.warning("Found orphan vector referencing non-existent document_id=%s. Ignoring.", doc_id_str)
                continue
            valid_candidates.append(RetrievedChunk(
                document_id=doc_id_str,
                filename=payload.get("filename", "unknown"),
                page_number=int(payload.get("page_number", 1)),
                chunk_index=int(payload.get("chunk_index", 0)),
                text=payload.get("text", ""),
                score=float(hit.score),
            ))
            
        if valid_candidates:
            # Ensure descending order
            valid_candidates.sort(key=lambda c: c.score, reverse=True)
            top_score = valid_candidates[0].score
            gap_cutoff = top_score - settings.RETRIEVAL_MAX_GAP
            logger.info("Top score for query is %.4f. Gap threshold (max_gap=%.4f) cutoff is %.4f", top_score, settings.RETRIEVAL_MAX_GAP, gap_cutoff)
            
            for c in valid_candidates:
                # Apply absolute score floor
                if c.score < settings.RETRIEVAL_MIN_SCORE:
                    logger.info(
                        "Filtering out chunk filename='%s' index=%d (score=%.4f < floor=%.2f)",
                        c.filename, c.chunk_index, c.score, settings.RETRIEVAL_MIN_SCORE
                    )
                    continue
                # Apply relative score gap limit
                if c.score < gap_cutoff:
                    logger.info(
                        "Filtering out chunk filename='%s' index=%d (score=%.4f < gap_cutoff=%.4f)",
                        c.filename, c.chunk_index, c.score, gap_cutoff
                    )
                    continue
                chunks.append(c)

    logger.info(
        "Retrieved %d chunks above threshold=%.3f (gap=%.3f) for query (top_k=%d)",
        len(chunks),
        settings.RETRIEVAL_MIN_SCORE,
        settings.RETRIEVAL_MAX_GAP,
        top_k,
    )
    return chunks
