import asyncio
import json
import httpx

API_BASE = "http://localhost:8000"

async def test_memory():
    print("Testing Conversation Memory...")
    async with httpx.AsyncClient() as client:
        # First request
        resp1 = await client.post(
            f"{API_BASE}/query",
            json={
                "query": "My name is Sachin. I'm testing memory.",
                "top_k": 2
            }
        )
        
        async for line in resp1.aiter_lines():
            if line and "data: " in line:
                print(line)
        
if __name__ == "__main__":
    asyncio.run(test_memory())
