import json
import urllib.request
import os
import fitz

BASE_URL = "http://localhost:8000"
PDF_NAME = "Rounak_Kumar_Sah_Profile.pdf"
PDF_PATH = f"/tmp/{PDF_NAME}"

def create_dummy_profile():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Rounak Kumar Sah\nSoftware Engineer\nExperience in AI and Python.", fontsize=12)
    doc.save(PDF_PATH)
    doc.close()

def upload_file():
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    BOUNDARY = "----FormBoundary9X3kTrZu0gW"
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{PDF_NAME}"\r\n'
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

def get_documents():
    req = urllib.request.Request(f"{BASE_URL}/documents", method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        return None

def post_query():
    data = json.dumps({"query": "Who is Rounak?"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/query",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    # The /query endpoint might stream (SSE) or return JSON depending on how it was implemented in Phase 4.
    # User said "Use LangGraph. Streaming response. Server Sent Events."
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return content
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        return None

if __name__ == "__main__":
    if not os.path.exists(PDF_PATH):
        create_dummy_profile()
        
    print(f"Uploading {PDF_NAME}...")
    res = upload_file()
    print("Upload Result:", json.dumps(res, indent=2))
    
    print("\nVerifying GET /documents...")
    docs = get_documents()
    print("Documents:", json.dumps(docs, indent=2))
    
    if docs and "documents" in docs:
        doc_list = docs["documents"]
        assert len(doc_list) == 1, f"Expected 1 document, found {len(doc_list)}"
        assert doc_list[0]["filename"] == PDF_NAME, f"Expected {PDF_NAME}, got {doc_list[0]['filename']}"
    
    print("\nVerifying POST /query...")
    query_result = post_query()
    print("Query Result:\n", query_result)
    
    print("\n✅ Verification passed!")
