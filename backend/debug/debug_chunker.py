import fitz

def _extract_header(line: str):
    import re
    match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if match:
        return len(match.group(1)), match.group(2).strip()
    return None

doc = fitz.open("/tmp/test_resume.pdf")
page = doc[0]
md = page.get_text("markdown")
print("MARKDOWN:")
print(repr(md))

lines = md.split('\n')
for line in lines:
    res = _extract_header(line)
    if res:
        print(f"Header: {res}")

doc.close()
