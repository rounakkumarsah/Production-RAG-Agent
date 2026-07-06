import asyncio
import os
import io
import time
import json
import httpx

API_BASE = "http://localhost:8000"

async def test_upload_pipeline(client):
    print("Running Upload Pipeline Tests...")
    
    # Create mock files
    files = []
    
    # 1. Valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    files.append(("files", ("valid.pdf", pdf_content, "application/pdf")))
    
    # 2. Valid TXT
    files.append(("files", ("valid.txt", b"Hello world, this is a test.", "text/plain")))
    
    # 3. Invalid extension
    files.append(("files", ("invalid.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")))
    
    # 4. MIME spoofing (PDF extension, but not PDF content)
    files.append(("files", ("spoof.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")))
    
    # 5. Empty file
    files.append(("files", ("empty.txt", b"", "text/plain")))
    
    resp = await client.post(f"{API_BASE}/upload", files=files)
    
    # We expect 400 or 415 because the entire batch is rejected if ANY file fails validation early
    # Wait, the current implementation in `api/documents.py` validates all files before processing
    # and raises HTTPException immediately. Let's see what it returns.
    print(f"Upload batch response: {resp.status_code}")
    if resp.status_code != 415 and resp.status_code != 400:
        print(f"FAILED: Expected 415 or 400, got {resp.status_code}")
    else:
        print("PASS: Invalid batch rejected correctly.")
        
    # Now test valid upload
    files_valid = [
        ("files", ("valid.txt", b"Hello world, this is a test.", "text/plain")),
        ("files", ("valid2.md", b"# Markdown\n\nThis is a test.", "text/markdown"))
    ]
    resp = await client.post(f"{API_BASE}/upload", files=files_valid)
    print(f"Valid upload response: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"PASS: Uploaded {data['total']} files, Succeeded: {data['succeeded']}")
    else:
        print(f"FAIL: {resp.text}")

async def test_api_endpoints(client):
    print("Running API Endpoint Tests...")
    # Health
    resp = await client.get(f"{API_BASE}/health")
    print(f"/health: {resp.status_code}")
    
    # Documents
    resp = await client.get(f"{API_BASE}/documents")
    print(f"/documents: {resp.status_code}")
    
    # Swagger
    resp = await client.get(f"{API_BASE}/openapi.json")
    print(f"/openapi.json: {resp.status_code}")

async def main():
    async with httpx.AsyncClient() as client:
        await test_api_endpoints(client)
        await test_upload_pipeline(client)

if __name__ == "__main__":
    asyncio.run(main())
