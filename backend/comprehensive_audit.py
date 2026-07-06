import asyncio
import io
import time
import zipfile
import json
import httpx
import xml.etree.ElementTree as ET

API_BASE = "http://localhost:8000"

def create_xml_bomb():
    # Billion laughs attack
    xml_bomb = b'''<?xml version="1.0"?>
    <!DOCTYPE lolz [
     <!ENTITY lol "lol">
     <!ELEMENT lolz (#PCDATA)>
     <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
     <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
     <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
     <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
     <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
     <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
     <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
     <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
     <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
    ]>
    <lolz>&lol9;</lolz>'''
    
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        zf.writestr('_rels/.rels', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        zf.writestr('word/document.xml', xml_bomb)
    return out.getvalue()

async def check_xml_bomb(client):
    print("Testing XML Bomb (Billion Laughs)...")
    bomb_bytes = create_xml_bomb()
    files = [("files", ("bomb.docx", bomb_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    resp = await client.post(f"{API_BASE}/upload", files=files)
    # The zip itself is small, it passes validate_document_upload.
    # The vulnerability occurs during parsing.
    # The API should catch the exception and return 200 with failed status for that file,
    # OR if it crashes the container, we have a huge problem.
    print(f"XML Bomb Upload Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"XML Bomb parsing result: {data}")

async def check_alembic():
    import subprocess
    print("Checking Alembic Migrations...")
    try:
        result = subprocess.run(["alembic", "history"], capture_output=True, text=True)
        print("Alembic History:\n", result.stdout)
    except Exception as e:
        print("Failed to run alembic:", e)

async def check_csv_injection(client):
    print("Testing CSV Injection...")
    csv_content = b'Name,Role\n=cmd|\' /C calc\'!A0,Admin\n@SUM(1+1)*cmd|\' /C notepad\'!A0,User'
    files = [("files", ("injection.csv", csv_content, "text/csv"))]
    resp = await client.post(f"{API_BASE}/upload", files=files)
    print(f"CSV Injection Response: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"CSV Injection processing: {data}")

async def check_performance(client):
    print("Testing Concurrent Queries P50/P95/P99...")
    import numpy as np
    
    times = []
    # Test 10 concurrent requests
    async def make_req():
        start = time.time()
        resp = await client.post(f"{API_BASE}/query", json={"query": "test query", "top_k": 3})
        # read the stream
        async for line in resp.aiter_lines():
            pass
        return time.time() - start

    tasks = [make_req() for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, float):
            times.append(r)
    
    if times:
        p50 = np.percentile(times, 50)
        p95 = np.percentile(times, 95)
        p99 = np.percentile(times, 99)
        print(f"Concurrent queries (N=10) - P50: {p50:.3f}s, P95: {p95:.3f}s, P99: {p99:.3f}s")
    else:
        print("Concurrent queries failed.")

async def main():
    async with httpx.AsyncClient() as client:
        await check_alembic()
        await check_xml_bomb(client)
        await check_csv_injection(client)
        # Check performance requires numpy, we might need to skip numpy and calculate manually
        
        # Calculate manually
        print("Testing Concurrent Queries P50/P95/P99...")
        times = []
        async def make_req():
            start = time.time()
            resp = await client.post(f"{API_BASE}/query", json={"query": "test query", "top_k": 3})
            async for line in resp.aiter_lines(): pass
            return time.time() - start

        tasks = [make_req() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, float): times.append(r)
        
        if times:
            times.sort()
            n = len(times)
            p50 = times[int(n*0.5)]
            p95 = times[int(n*0.95)]
            p99 = times[int(n*0.99)]
            print(f"Concurrent queries (N={n}) - P50: {p50:.3f}s, P95: {p95:.3f}s, P99: {p99:.3f}s")

if __name__ == "__main__":
    asyncio.run(main())
