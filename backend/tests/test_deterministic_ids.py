import fitz
import json
import urllib.request
import time
from qdrant_client import QdrantClient

BASE_URL = "http://localhost:8000"

def create_pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    text = "# Deterministic Test\n\nThis is a test to see if chunk IDs are deterministic."
    page.insert_text((50, 50), text, fontsize=12)
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
    client = QdrantClient("http://qdrant:6333")
    return client.count(collection_name="documents").count

if __name__ == "__main__":
    pdf_path = "/tmp/deterministic_test.pdf"
    create_pdf(pdf_path)
    
    print("Initial Vector Count:", get_vector_count())
    
    print("\nUploading first time...")
    res1 = upload_file(pdf_path, "deterministic_test.pdf")
    doc_id1 = res1["documents"][0]["document_id"]
    print("Upload 1 Complete. Postgres Document ID:", doc_id1)
    
    count1 = get_vector_count()
    print("Vector Count after Upload 1:", count1)
    
    print("\nUploading SECOND time (exact same file)...")
    time.sleep(2)  # brief pause
    res2 = upload_file(pdf_path, "deterministic_test.pdf")
    doc_id2 = res2["documents"][0]["document_id"]
    print("Upload 2 Complete. Postgres Document ID:", doc_id2)
    
    count2 = get_vector_count()
    print("Vector Count after Upload 2:", count2)
    
    if count1 == count2 and doc_id1 != doc_id2:
        print("\n✅ SUCCESS: Vector count remained the same! Existing vectors were updated with the new document_id instead of duplicating.")
    else:
        print("\n❌ FAILURE: Vector count increased or document IDs matched.")
