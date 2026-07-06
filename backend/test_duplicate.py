import httpx
import time

API_URL = "http://localhost:8000"

def test_duplicate_safety():
    # Create a dummy test file
    test_content = b"This is a dummy test file for duplicate testing. " * 100
    files = {"files": ("test_duplicate.txt", test_content, "text/plain")}

    print("--- Uploading file for the first time ---")
    resp1 = httpx.post(f"{API_URL}/upload", files=files)
    print(resp1.status_code, resp1.json())
    doc1 = resp1.json()["documents"][0]
    
    print("\n--- Uploading identical file again (should be already_exists) ---")
    files2 = {"files": ("test_duplicate.txt", test_content, "text/plain")}
    resp2 = httpx.post(f"{API_URL}/upload", files=files2)
    print(resp2.status_code, resp2.json())
    doc2 = resp2.json()["documents"][0]
    assert doc2["status"] == "already_exists", "Expected already_exists"

if __name__ == "__main__":
    test_duplicate_safety()
