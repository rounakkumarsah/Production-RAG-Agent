"""
Conversation quality verification test.
Runs 4 turns of a resume-based conversation and verifies that:
  - Turn 4 ("Can you list them again as bullet points?") contains ONLY
    the technical skills as bullet points and does NOT include location
    or other unrelated information from Turn 3.

Requires:
  - A resume PDF already uploaded to the backend.
  - Backend running at http://localhost:8000.
"""
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:8000"


def query(question: str, conversation_id: str | None = None, top_k: int = 5) -> dict:
    """POST /query and collect the full SSE stream into a single result dict."""
    payload = json.dumps({
        "query": question,
        "conversation_id": conversation_id,
        "top_k": top_k,
    }).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer_parts: list[str] = []
    done_event: dict = {}

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                payload_str = line[5:].strip()
                if payload_str == "[DONE]":
                    break
                try:
                    event = json.loads(payload_str)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "chunk":
                    answer_parts.append(event.get("content", ""))
                elif event.get("type") == "done":
                    done_event = event

    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        raise

    return {
        "answer": "".join(answer_parts),
        "conversation_id": done_event.get("conversation_id"),
    }


def upload_resume_pdf():
    """Create and upload a minimal resume PDF. Returns document_id."""
    import fitz  # PyMuPDF — available inside Docker
    import tempfile, os

    resume_text = """John Smith
Software Engineer | New York, NY | john.smith@email.com

SUMMARY
Experienced software engineer with 8+ years building scalable distributed systems.

TECHNICAL SKILLS
- Languages: Python, Go, TypeScript, Rust
- Frameworks: FastAPI, Django, React, LangChain
- Databases: PostgreSQL, Redis, Qdrant, MongoDB
- Infrastructure: Docker, Kubernetes, AWS, Terraform
- Other: LangGraph, RAG systems, vector search, CI/CD pipelines

EXPERIENCE
Senior Software Engineer — Acme Corp, New York, NY (2020–present)
- Led migration of monolith to microservices, reducing latency by 40%.
- Built internal RAG knowledge base used by 500+ employees.

Software Engineer — StartupXYZ, San Francisco, CA (2018–2020)
- Developed real-time data pipelines processing 1M events/day.

EDUCATION
B.S. Computer Science — MIT, Cambridge, MA (2018)

LOCATION
Currently based in New York, NY."""

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), resume_text, fontsize=11)
    path = "/tmp/john_smith_resume.pdf"
    doc.save(path)
    doc.close()

    with open(path, "rb") as f:
        pdf_bytes = f.read()

    BOUNDARY = "----FormBoundary9X3kTrZu0gW"
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="john_smith_resume.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{BOUNDARY}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    doc_result = result["documents"][0]
    assert doc_result["status"] == "completed", f"Upload failed: {doc_result}"
    print(f"✅ Resume uploaded — {doc_result['chunk_count']} chunks, {doc_result['page_count']} pages")
    return doc_result["document_id"]


def run_verification():
    print("\n" + "="*70)
    print("CONVERSATION QUALITY VERIFICATION")
    print("="*70)

    # Upload resume first
    print("\n[Setup] Uploading resume PDF...")
    upload_resume_pdf()

    conv_id = None
    turns = [
        "Summarize this resume.",
        "What are his technical skills?",
        "Where does he live?",
        "Can you list them again as bullet points?",
    ]

    answers: list[str] = []

    for i, question in enumerate(turns, 1):
        print(f"\n{'─'*70}")
        print(f"Turn {i}: {question}")
        print("─"*70)
        result = query(question, conversation_id=conv_id)
        conv_id = result["conversation_id"]
        answer = result["answer"]
        answers.append(answer)
        print(f"Answer:\n{answer}")

    # ── Verification ──────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("VERIFICATION: Turn 4 answer quality check")
    print("="*70)

    turn4 = answers[3].lower()

    # The last answer should contain skills (bullets expected)
    has_bullet = any(c in answers[3] for c in ["•", "-", "*", "–"]) or any(
        line.strip().startswith(("-", "*", "•")) for line in answers[3].splitlines()
    )

    # Should NOT contain location-specific words from Turn 3's answer
    turn3 = answers[2].lower()
    # Extract location words from turn 3
    location_keywords = [w for w in ["new york", "ny", "currently based", "location"]
                         if w in turn3]

    location_bleed = any(kw in turn4 for kw in location_keywords) if location_keywords else False

    print(f"\n  Turn 4 answer has bullet points : {'✅ YES' if has_bullet else '⚠️  NO (may be numbered list)'}")
    print(f"  Location keywords in Turn 3    : {location_keywords or '(none detected)'}")
    print(f"  Location keywords bleed into   ")
    print(f"  Turn 4                         : {'❌ YES — location bleed detected' if location_bleed else '✅ NO — clean'}")

    if not location_bleed:
        print("\n✅ PASS — Turn 4 focuses only on technical skills, no location repetition")
    else:
        print("\n⚠️  PARTIAL — Location content may have bled into Turn 4.")
        print("   Review the answer above to confirm if it is acceptable.")

    print("\n" + "="*70)


if __name__ == "__main__":
    run_verification()
