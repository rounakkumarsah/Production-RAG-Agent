import requests

API_URL = "http://localhost:8000"

queries = [
    "What is the cost of Apple?",
    "How old is Alice?",
    "What kind of file is this markdown file?",
    "What is the presentation about?"
]

for q in queries:
    resp = requests.post(f"{API_URL}/query", json={"query": q, "top_k": 3}, stream=True)
    if resp.status_code == 200:
        print(f"Q: {q}")
        full_answer = ""
        sources = []
        for line in resp.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    payload = decoded_line[6:]
                    if payload == "[DONE]":
                        break
                    import json
                    try:
                        data = json.loads(payload)
                        if data.get("type") == "chunk":
                            full_answer += data.get("content", "")
                        elif data.get("type") == "sources":
                            sources = data.get("sources", [])
                    except:
                        pass
        print(f"A: {full_answer}")
        print(f"Context docs: {len(sources)}")
        print("-" * 40)
    else:
        print(f"Query failed: {resp.status_code} {resp.text}")
