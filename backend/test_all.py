import requests
import json

formats = ["pdf", "docx", "pptx", "xlsx", "csv", "txt", "md"]

for ext in formats:
    print(f"Testing {ext}")
    filename = f"/tmp/test.{ext}"
    with open(filename, "rb") as f:
        files = {"files": (f"test.{ext}", f, "application/octet-stream")}
        try:
            response = requests.post("http://localhost:8000/upload", files=files)
            print(f"Status Code: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")
    print("-" * 40)
