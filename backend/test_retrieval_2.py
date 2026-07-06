import asyncio
import json
import httpx
import time

API_BASE = "http://localhost:8000"

async def test_retrieval():
    print("Testing Retrieval...")
    async with httpx.AsyncClient() as client:
        # Check that we can stream the response
        resp = await client.post(
            f"{API_BASE}/query",
            json={
                "query": "What are the main risk factors discussed in the report?",
                "top_k": 5
            }
        )
        print(f"Query response status: {resp.status_code}")
        
        async for line in resp.aiter_lines():
            if line:
                print(f"Stream output: {line}")
                if "data: " in line:
                    try:
                        data = json.loads(line.replace("data: ", ""))
                        if data.get("type") == "sources":
                            print(f"Found citations: {len(data['sources'])}")
                    except Exception as e:
                        pass
        
if __name__ == "__main__":
    asyncio.run(test_retrieval())
