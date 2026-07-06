import fitz
import json
import urllib.request
import time
from urllib.error import HTTPError

BASE_URL = "http://localhost:8000"

def create_resume_pdf():
    doc = fitz.open()
    page = doc.new_page()
    text = """# John Smith Resume

## Contact Information
Email: john@example.com
Phone: 555-0100

## Experience
**Software Engineer** at TechCorp.
- Did some engineering.
- Wrote code.

## Education
B.S. Computer Science.
"""
    page.insert_text((50, 50), text, fontsize=12)
    path = "/tmp/test_resume.pdf"
    doc.save(path)
    doc.close()
    return path

def create_research_paper_pdf():
    doc = fitz.open()
    for i in range(30):
        page = doc.new_page()
        if i == 0:
            text = "# A Study on AI\n\n## Abstract\n\nThis is the abstract."
        elif i == 1:
            text = "## Introduction\n\nAI is cool. " * 50
        elif i == 15:
            text = "## Methodology\n\nWe did things. " * 50
        else:
            text = f"Page {i+1} content. " * 100
        page.insert_text((50, 50), text, fontsize=11)
    path = "/tmp/test_research_paper.pdf"
    doc.save(path)
    doc.close()
    return path

def create_tech_book_pdf():
    doc = fitz.open()
    for i in range(300):
        page = doc.new_page()
        if i % 30 == 0:
            text = f"# Chapter {i//30 + 1}\n\n## Section 1\n\nIntroduction to chapter."
        else:
            text = f"This is detailed content for page {i+1}. " * 150
        page.insert_text((50, 50), text, fontsize=11)
    path = "/tmp/test_tech_book.pdf"
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
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            doc_result = result["documents"][0]
            print(f"✅ {filename} uploaded in {time.time()-t0:.1f}s — {doc_result['chunk_count']} chunks, {doc_result['page_count']} pages")
            return doc_result["document_id"]
    except HTTPError as e:
        print(f"❌ Failed {filename}: {e.read().decode()}")
        return None

def check_qdrant(doc_id, filename):
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    client = QdrantClient("http://qdrant:6333")
    
    res = client.scroll(
        collection_name="documents",
        scroll_filter=qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchValue(value=doc_id),
                )
            ]
        ),
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    
    print(f"\n--- Metadata samples for {filename} ---")
    points, _ = res
    if not points:
        print("No vectors found!")
    for i, p in enumerate(points):
        print(f"Chunk {p.payload.get('chunk_index')}:")
        print(f"  Heading: {p.payload.get('heading')}")
        print(f"  Section: {p.payload.get('section')}")
        print(f"  Page: {p.payload.get('page_number')}")
        print(f"  Size: {p.payload.get('char_count')} chars")

if __name__ == "__main__":
    print("Generating PDFs...")
    resume = create_resume_pdf()
    paper = create_research_paper_pdf()
    book = create_tech_book_pdf()
    
    print("Uploading PDFs (this will trigger adaptive chunking and Gemini embeddings)...")
    id1 = upload_file(resume, "resume.pdf")
    
    print("Sleeping 30s to avoid Gemini rate limits...")
    time.sleep(30)
    id2 = upload_file(paper, "research_paper.pdf")
    
    print("Sleeping 30s to avoid Gemini rate limits...")
    time.sleep(30)
    id3 = upload_file(book, "tech_book.pdf")
    
    if id1: check_qdrant(id1, "resume.pdf")
    if id2: check_qdrant(id2, "research_paper.pdf")
    if id3: check_qdrant(id3, "tech_book.pdf")
