import asyncio
import httpx
import time

API_BASE = "http://localhost:8000"

async def upload_file(client, run_id):
    content = f"Duplicate check content {run_id}".encode('utf-8')
    files = [("files", ("dup.txt", content, "text/plain"))]
    resp = await client.post(f"{API_BASE}/upload", files=files)
    return resp.json()

async def main():
    print("Testing Concurrent Uploads of the exact same file...")
    async with httpx.AsyncClient() as client:
        # Same file content
        content = b"Exact same file content across 5 concurrent uploads."
        files_payload = [("files", ("dup.txt", content, "text/plain"))]
        
        async def make_req():
            return await client.post(f"{API_BASE}/upload", files=[("files", ("dup.txt", content, "text/plain"))])
            
        tasks = [make_req() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, httpx.Response):
                data = r.json()
                print("Status:", r.status_code)
                for d in data.get('documents', []):
                    print(" -", d['status'], d.get('error'))
            else:
                print("Exception:", r)

if __name__ == "__main__":
    asyncio.run(main())
