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
        
        conv_id = None
        async for line in resp1.aiter_lines():
            if line and "data: " in line:
                try:
                    data = json.loads(line.replace("data: ", ""))
                    if data.get("type") == "done":
                        conv_id = data.get("conversation_id")
                        print(f"Got conversation ID: {conv_id}")
                except Exception:
                    pass

        if not conv_id:
            print("Failed to get conversation_id")
            return
            
        # Second request
        print("\nSending follow-up...")
        resp2 = await client.post(
            f"{API_BASE}/query",
            json={
                "query": "What is my name?",
                "conversation_id": conv_id,
                "top_k": 2
            }
        )
        
        answer = ""
        async for line in resp2.aiter_lines():
            if line and "data: " in line:
                try:
                    data = json.loads(line.replace("data: ", ""))
                    if data.get("type") == "chunk":
                        answer += data.get("content", "")
                except Exception:
                    pass
        print(f"AI replied: {answer}")
        
if __name__ == "__main__":
    asyncio.run(test_memory())
