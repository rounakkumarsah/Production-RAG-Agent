import asyncio
from sqlalchemy import select
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
from app.db.postgres import get_db_session
from app.db.models import Document, DocumentStatus
from app.config import get_settings

async def clean_orphan_vectors():
    settings = get_settings()
    client = QdrantClient(url=settings.QDRANT_URL)
    
    # Get all document IDs in Postgres that are valid
    async with get_db_session() as session:
        result = await session.execute(
            select(Document.id).where(Document.status == DocumentStatus.COMPLETED)
        )
        valid_doc_ids = {str(row[0]) for row in result.all()}
    
    print(f"Found {len(valid_doc_ids)} COMPLETED documents in Postgres.")
    
    # We must iterate Qdrant points. Since there are only 26 points, we can just scroll.
    records, next_page = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )
    
    orphan_ids = []
    for r in records:
        doc_id = r.payload.get("document_id")
        if doc_id not in valid_doc_ids:
            orphan_ids.append(r.id)
            
    print(f"Found {len(orphan_ids)} orphan vectors in Qdrant.")
    
    if orphan_ids:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=orphan_ids
        )
        print("Deleted orphan vectors.")
    else:
        print("No orphan vectors found.")

if __name__ == "__main__":
    asyncio.run(clean_orphan_vectors())
