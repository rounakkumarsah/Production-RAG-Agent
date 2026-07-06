"""
Test script — runs inside the Docker container.
Uploads the test PDF to POST /upload and verifies the full pipeline.
"""
import json
import urllib.request

PDF_PATH = "test.pdf"
URL = "http://localhost:8000/upload"
BOUNDARY = "----FormBoundary7MA4YWxkTrZu0gW"

with open(PDF_PATH, "rb") as f:
    pdf_bytes = f.read()

# Build multipart body manually (no external deps)
boundary_bytes = BOUNDARY.encode()
body = (
    b"--" + boundary_bytes + b"\r\n"
    b'Content-Disposition: form-data; name="files"; filename="test_upload.pdf"\r\n'
    b"Content-Type: application/pdf\r\n"
    b"\r\n"
    + pdf_bytes
    + b"\r\n"
    b"--" + boundary_bytes + b"--\r\n"
)

req = urllib.request.Request(
    URL,
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
    method="POST",
)

print(f"Uploading {len(pdf_bytes):,} byte PDF to {URL} ...")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        print("\n=== Upload Response ===")
        print(json.dumps(result, indent=2, default=str))

        # Verify pipeline
        doc = result["documents"][0]
        status = doc["status"]
        chunk_count = doc.get("chunk_count", 0)
        page_count = doc.get("page_count", 0)

        print("\n=== Pipeline Verification ===")
        print(f"  status      : {status}")
        print(f"  page_count  : {page_count}")
        print(f"  chunk_count : {chunk_count}")

        assert status == "completed", f"FAIL — status is {status!r}, error: {doc.get('error')}"
        assert chunk_count > 0, f"FAIL — chunk_count is {chunk_count}"
        assert page_count > 0, f"FAIL — page_count is {page_count}"

        print("\nALL CHECKS PASSED - upload pipeline is working correctly")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")
except Exception as exc:
    print(f"ERROR: {exc}")
    raise
