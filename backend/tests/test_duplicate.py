import fitz
import json
import urllib.request
import time
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://raguser:ragpass@localhost:5432/ragdb" # Assuming defaults in .env or exposed via localhost

def create_pdf(path):
    import time
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"Duplicate Detection Test {time.time()}", fontsize=12)
    doc.save(path)
    doc.close()
    return path

def upload_file(path, filename):
    with open(path, "rb") as f:
        pdf_bytes = f.read()

    BOUNDARY = "----FormBoundary9X3kTrZu0gW"
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{BOUNDARY}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_vector_count():
    # When running inside the container or outside? 
    # The script will be run INSIDE the container to easily access Qdrant and Postgres via Docker DNS
    client = QdrantClient("http://qdrant:6333")
    return client.count(collection_name="documents").count

import subprocess

import asyncio

async def get_pg_doc_count():
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from sqlalchemy import text
    from app.db.postgres import get_db_session
    async with get_db_session() as session:
        result = await session.execute(text("SELECT count(*) FROM documents;"))
        return result.scalar()

async def main():
    pdf_path = "/tmp/duplicate_test.pdf"
    create_pdf(pdf_path)
    
    initial_pg = await get_pg_doc_count()
    initial_qdrant = get_vector_count()
    print(f"Initial PG docs: {initial_pg}, Vectors: {initial_qdrant}")
    
    print("\n--- FIRST UPLOAD ---")
    res1 = upload_file(pdf_path, "dup_test.pdf")
    doc1 = res1["documents"][0]
    print(f"Status: {doc1['status']}")
    
    pg_after_1 = await get_pg_doc_count()
    q_after_1 = get_vector_count()
    print(f"PG docs: {pg_after_1}, Vectors: {q_after_1}")
    
    assert doc1['status'] == 'completed', f"Expected completed, got {doc1['status']}"
    assert pg_after_1 == initial_pg + 1, "PG count should increase by 1"
    assert q_after_1 > initial_qdrant, "Vector count should increase"
    
    print("\n--- SECOND UPLOAD (Duplicate) ---")
    res2 = upload_file(pdf_path, "dup_test.pdf")
    doc2 = res2["documents"][0]
    print(f"Status: {doc2['status']}")
    print(json.dumps(doc2, indent=2))
    
    pg_after_2 = await get_pg_doc_count()
    q_after_2 = get_vector_count()
    print(f"PG docs: {pg_after_2}, Vectors: {q_after_2}")
    
    assert doc2['status'] == 'already_exists', f"Expected already_exists, got {doc2['status']}"
    assert 'message' in doc2, "Should return a message"
    assert doc2['existing_document_id'] == doc1['document_id'], "Should return original document ID"
    assert pg_after_2 == pg_after_1, "PG count should NOT increase"
    assert q_after_2 == q_after_1, "Vector count should NOT increase"
    
    print("\n✅ SUCCESS: Duplicate detection worked flawlessly.")

if __name__ == "__main__":
    asyncio.run(main())
