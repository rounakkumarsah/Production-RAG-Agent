"""
Re-index utility: Wipes the Qdrant vectors and PostgreSQL metadata.
Used to start fresh before re-uploading documents into the adaptive chunking system.
"""

import asyncio
import sys

# Ensure backend root is in PYTHONPATH
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.postgres import get_db_session
from app.db.qdrant import get_qdrant_client
from app.config import get_settings
from app.services.vector_service import ensure_collection

async def wipe_database(force=False):
    print("⚠️  WARNING: This will permanently delete all vector and document metadata.")
    if not force:
        confirm = input("Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Aborted.")
            return

    settings = get_settings()
    q_client = get_qdrant_client()
    
    print("🔄 Starting atomic reset...")
    try:
        async with get_db_session() as session:
            async with session.begin():
                # 1. Truncate PostgreSQL table (transactional)
                await session.execute(text("TRUNCATE TABLE documents CASCADE;"))
                
                # 2. Wipe Qdrant Collection
                # If this fails, the postgres truncation will rollback!
                try:
                    await q_client.delete_collection(settings.QDRANT_COLLECTION)
                except Exception as e:
                    # Ignore if it doesn't exist
                    pass
                
                await ensure_collection()
                # Commit happens automatically upon exiting session.begin() if no exception
                
        print("✅ Atomic wipe successful.")
    except Exception as e:
        print(f"❌ Reset failed. Rolled back Postgres. Error: {e}")
        sys.exit(1)

    # 3. Verification
    print("🔍 Verifying consistency...")
    try:
        async with get_db_session() as session:
            pg_count = await session.scalar(text("SELECT count(*) FROM documents;"))
        
        q_count = (await q_client.count(settings.QDRANT_COLLECTION)).count
        
        if pg_count != 0 or q_count != 0:
            print(f"❌ Inconsistency detected! PG docs: {pg_count}, Qdrant vectors: {q_count}")
            sys.exit(1)
            
        print("✅ Verification passed: 0 documents, 0 vectors.")
    except Exception as e:
        print(f"❌ Verification failed due to error: {e}")
        sys.exit(1)

    print("\n🎉 Reset complete! You can now upload your PDFs again to re-index them.")

if __name__ == "__main__":
    force_mode = "--force" in sys.argv
    asyncio.run(wipe_database(force_mode))
